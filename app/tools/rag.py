"""RAG Tool：入库、混合检索与重排。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.llm import LLMFactory
from app.schemas.qa import KnowledgeChunkIn, QASource


@dataclass(slots=True)
class RAGTool:
    """封装 PostgreSQL + Milvus 的混合检索。

    设计说明：
    - PostgreSQL 保存可读文本与元数据，并提供词法检索（FTS）。
    - Milvus 保存向量，用于语义检索（Dense Search）。
    - 查询时做 Hybrid Fusion：词法分 + 向量分加权融合后返回。
    """ 

    llm_factory: LLMFactory
    pg_pool: Any
    collection: Any

    @classmethod
    async def from_settings(cls) -> "RAGTool":
        """基于全局配置初始化 RAGTool。

        初始化步骤：
        1) 连接 PostgreSQL 并创建连接池
        2) 连接 Milvus 并确保目标 collection 可用
        3) 初始化 LLMFactory（embedding/chat 统一入口）
        4) 确保 PostgreSQL 表结构与索引存在
        """
        import asyncpg
        from pymilvus import connections

        settings = get_settings()
        pool = await asyncpg.create_pool(settings.postgres_dsn, min_size=1, max_size=5)
        connections.connect(alias="default", uri=settings.milvus_uri)
        collection = await cls._ensure_collection(
            settings.milvus_collection,
            settings.qa_embedding_dim,
        )
        instance = cls(llm_factory=LLMFactory.from_settings(), pg_pool=pool, collection=collection)
        await instance._ensure_tables()
        return instance

    async def ingest(self, chunks: list[KnowledgeChunkIn]) -> int:
        """批量入库知识分块（文本 + 向量）。

        参数:
        - chunks: 待入库的分块列表。每个分块都需要 document_id/chunk_id/content 等字段。

        返回:
        - 实际处理的分块数量（len(chunks)）。

        关键实现:
        - 先逐条生成 embedding，再批量写 PostgreSQL（UPSERT）；
        - 最后把向量批量 upsert 到 Milvus，保证主键一致（document_id:chunk_id）。
        """
        if not chunks:
            return 0

        rows: list[tuple[str, str, str, str, str | None]] = []
        vector_ids: list[str] = []
        vectors: list[list[float]] = []

        for chunk in chunks:
            # 向量主键与结构化存储主键保持同构，便于跨存储关联。
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

        # Milvus upsert 与 PostgreSQL UPSERT 语义保持一致，可重复写入更新。
        self.collection.upsert([vector_ids, vectors])
        # flush 确保向量尽快可检索（测试与联调阶段更直观）。
        self.collection.flush()
        return len(chunks)

    async def retrieve_hybrid(self, query: str, top_k: int, rerank_k: int) -> list[QASource]:
        """执行混合检索并返回重排后的来源列表。

        参数:
        - query: 用户问题
        - top_k: 召回候选数量（词法和向量各自的上限）
        - rerank_k: 最终返回数量

        返回:
        - QASource 列表，已完成融合打分并按分数降序截断。

        打分策略:
        - 最终分 = lexical_score * 0.45 + dense_score * 0.55
        - 该策略是轻量启发式，可替换为专门 reranker 模型。
        """
        # 1) 向量检索：用 query embedding 在 Milvus 中召回语义相近候选。
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
            # COSINE 距离越小越相似，这里转换为“越大越好”的相似分。
            dense_scores[str(hit.entity.get("pk"))] = 1.0 - float(hit.distance)

        async with self.pg_pool.acquire() as conn:
            # 2) 词法检索：PostgreSQL FTS 召回关键词匹配文本并给出 lexical_score。
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
                # 3) 补齐仅命中向量、未命中词法的候选，避免遗漏语义相关文档。
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
            # 4) 融合打分并收敛到 [0, 1]，方便后续 confidence 逻辑复用。
            lexical_component = min(source.score, 1.0)
            dense_component = dense_scores.get(pk, 0.0)
            source.score = max(min(lexical_component * 0.45 + dense_component * 0.55, 1.0), 0.0)

        # 5) 最终重排并截断输出。
        reranked = sorted(source_map.values(), key=lambda item: item.score, reverse=True)
        return reranked[:rerank_k]

    async def _ensure_tables(self) -> None:
        """确保 PostgreSQL 结构化存储表和检索索引存在。

        - qa_knowledge_chunk: 保存 chunk 文本及来源元数据
        - idx_qa_knowledge_chunk_tsv: FTS GIN 索引，支撑词法召回
        """
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
    async def _ensure_collection(name: str, embedding_dim: int) -> Any:
        """确保 Milvus collection 可用且维度匹配当前 embedding 模型。

        规则:
        - 若 collection 已存在：校验 schema dim 必须与 embedding_dim 一致；
        - 若不存在：按当前 dim 创建 collection 并建立 HNSW 索引。

        注意:
        - embedding 模型切换导致维度变化时，需先 drop 旧 collection 再重建。
        """
        from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, utility

        if utility.has_collection(name):
            collection = Collection(name)
            # 运行期主动校验维度，避免“入库成功率随机失败”的隐性问题。
            dim = collection.schema.fields[1].params.get("dim")
            if dim != embedding_dim:
                raise RuntimeError(
                    f"Milvus collection dim mismatch: current={dim}, expected={embedding_dim}. "
                    f"Please drop collection `{name}` and retry."
                )
            collection.load()
            return collection

        schema = CollectionSchema(
            fields=[
                FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
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
