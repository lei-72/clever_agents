"""RAG Tool：入库、混合检索与重排。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.llm import LLMFactory
from app.schemas.qa import KnowledgeChunkIn, QASource


@dataclass(slots=True)
class RAGTool:
    """封装 PostgreSQL + Milvus 的混合检索。"""

    llm_factory: LLMFactory
    pg_pool: Any
    collection: Any

    @classmethod
    async def from_settings(cls) -> "RAGTool":
        import asyncpg
        from pymilvus import connections

        settings = get_settings()
        pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=1, max_size=5)
        connections.connect(alias="default", uri=settings.milvus_uri)
        collection = await cls._ensure_collection(settings.milvus_collection)
        instance = cls(llm_factory=LLMFactory.from_settings(), pg_pool=pool, collection=collection)
        await instance._ensure_tables()
        return instance

    async def ingest(self, chunks: list[KnowledgeChunkIn]) -> int:
        if not chunks:
            return 0

        rows: list[tuple[str, str, str, str, str | None]] = []
        vector_ids: list[str] = []
        vectors: list[list[float]] = []

        for chunk in chunks:
            embedding = await self.llm_factory.embed_text(chunk.content)
            vector_id = f"{chunk.document_id}:{chunk.chunk_id}"
            vector_ids.append(vector_id)
            vectors.append(embedding)
            rows.append(
                (
                    chunk.document_id,
                    chunk.chunk_id,
                    chunk.title,
                    chunk.content,
                    chunk.source_uri,
                )
            )

        async with self.pg_pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO qa_knowledge_chunk(document_id, chunk_id, title, content, source_uri)
                VALUES($1, $2, $3, $4, $5)
                ON CONFLICT (document_id, chunk_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    source_uri = EXCLUDED.source_uri
                """,
                rows,
            )

        self.collection.upsert([vector_ids, vectors])
        self.collection.flush()
        return len(chunks)

    async def retrieve_hybrid(self, query: str, top_k: int, rerank_k: int) -> list[QASource]:
        query_vector = await self.llm_factory.embed_text(query)
        dense_hits = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            limit=top_k,
            output_fields=["pk"],
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        )
        dense_scores: dict[str, float] = {}
        for hit in dense_hits[0]:
            dense_scores[str(hit.entity.get("pk"))] = 1.0 - float(hit.distance)

        async with self.pg_pool.acquire() as conn:
            lexical_rows = await conn.fetch(
                """
                SELECT
                    document_id,
                    chunk_id,
                    title,
                    content,
                    source_uri,
                    ts_rank_cd(
                        to_tsvector('simple', content),
                        plainto_tsquery('simple', $1)
                    ) AS lexical_score
                FROM qa_knowledge_chunk
                WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', $1)
                ORDER BY lexical_score DESC
                LIMIT $2
                """,
                query,
                top_k,
            )

            source_map: dict[str, QASource] = {}
            for row in lexical_rows:
                pk = f"{row['document_id']}:{row['chunk_id']}"
                source_map[pk] = QASource(
                    document_id=row["document_id"],
                    chunk_id=row["chunk_id"],
                    title=row["title"],
                    content=row["content"],
                    source_uri=row["source_uri"],
                    score=float(row["lexical_score"]),
                )

            if dense_scores:
                missing_ids = [pk.split(":", 1) for pk in dense_scores if pk not in source_map]
                if missing_ids:
                    dense_rows = await conn.fetch(
                        """
                        SELECT document_id, chunk_id, title, content, source_uri
                        FROM qa_knowledge_chunk
                        WHERE (document_id, chunk_id) IN (
                            SELECT * FROM UNNEST($1::text[], $2::text[])
                        )
                        """,
                        [doc for doc, _ in missing_ids],
                        [chunk for _, chunk in missing_ids],
                    )
                    for row in dense_rows:
                        pk = f"{row['document_id']}:{row['chunk_id']}"
                        source_map[pk] = QASource(
                            document_id=row["document_id"],
                            chunk_id=row["chunk_id"],
                            title=row["title"],
                            content=row["content"],
                            source_uri=row["source_uri"],
                            score=0.0,
                        )

        for pk, source in source_map.items():
            lexical_component = min(source.score, 1.0)
            dense_component = dense_scores.get(pk, 0.0)
            source.score = max(min(lexical_component * 0.45 + dense_component * 0.55, 1.0), 0.0)

        reranked = sorted(source_map.values(), key=lambda item: item.score, reverse=True)
        return reranked[:rerank_k]

    async def _ensure_tables(self) -> None:
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_knowledge_chunk (
                    document_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_uri TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY(document_id, chunk_id)
                );
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_qa_knowledge_chunk_tsv
                ON qa_knowledge_chunk
                USING GIN (to_tsvector('simple', content));
                """
            )

    @staticmethod
    async def _ensure_collection(name: str) -> Collection:
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, utility

        if utility.has_collection(name):
            collection = Collection(name)
            collection.load()
            return collection

        schema = CollectionSchema(
            fields=[
                FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            ],
            description="QA knowledge vector collection",
        )
        collection = Collection(name=name, schema=schema)
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 200},
            },
        )
        collection.load()
        return collection
