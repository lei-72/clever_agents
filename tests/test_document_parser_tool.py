"""DocumentParserTool 测试。"""

from __future__ import annotations

import unittest

from app.tools.document_parser import DocumentParserTool


class TestDocumentParserTool(unittest.TestCase):
    def test_parse_txt_and_build_chunks(self) -> None:
        tool = DocumentParserTool(chunk_size=10, overlap=2)
        parsed = tool.parse(
            filename="demo.txt",
            content="这是第一段。\n\n这是第二段，测试切块功能。".encode("utf-8"),
        )
        chunks = tool.build_chunks(
            document_id="doc-test-1",
            source_uri="file://demo.txt",
            parsed=parsed,
        )
        self.assertEqual(parsed.title, "demo")
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0].document_id, "doc-test-1")
        self.assertTrue(chunks[0].content)

    def test_split_text_prefers_line_boundaries(self) -> None:
        tool = DocumentParserTool(chunk_size=25, overlap=5)
        parts = tool._split_text(
            "第一行内容很长很长很长\n第二行内容也很长很长很长\n第三行内容同样很长很长很长",
        )
        self.assertGreaterEqual(len(parts), 2)
        self.assertIn("第一行内容", parts[0])

    def test_parse_unsupported_file(self) -> None:
        tool = DocumentParserTool()
        with self.assertRaises(ValueError):
            tool.parse(filename="demo.xlsx", content=b"123")

    def test_parse_empty_file_raises(self) -> None:
        tool = DocumentParserTool()
        with self.assertRaises(ValueError):
            tool.parse(filename="demo.txt", content=b"")

    def test_build_chunks_with_empty_text_raises(self) -> None:
        tool = DocumentParserTool()
        with self.assertRaises(ValueError):
            tool.build_chunks(
                document_id="doc-test-2",
                source_uri=None,
                parsed=tool.parse(filename="demo.txt", content="\n\n".encode("utf-8")),
            )

    def test_invalid_chunk_settings_raise(self) -> None:
        with self.assertRaises(ValueError):
            DocumentParserTool(chunk_size=0, overlap=0)
        with self.assertRaises(ValueError):
            DocumentParserTool(chunk_size=10, overlap=-1)
        with self.assertRaises(ValueError):
            DocumentParserTool(chunk_size=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
