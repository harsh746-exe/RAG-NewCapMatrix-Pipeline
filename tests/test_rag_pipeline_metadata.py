import sys
import tempfile
import unittest
from pathlib import Path


# Ensure `src/` is importable when running `python -m unittest`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from core.rag_pipeline import RAGCapabilityAnalyzerTXT  # noqa: E402
from langchain.schema import Document  # noqa: E402


class TestRAGPipelineMetadata(unittest.TestCase):
    def test_extracts_contract_name_from_txt_header_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "example.txt"
            original = Path(tmpdir) / "02_Detailed Project Descriptions" / "SSOE" / "folder" / "file.pdf"
            txt_path.write_text(
                "\n".join(
                    [
                        "# Converted from: file.pdf",
                        f"# Original PDF: {original}",
                        "# Text Length: 10 characters",
                        "",
                        "Some content here.",
                    ]
                ),
                encoding="utf-8",
            )

            analyzer = RAGCapabilityAnalyzerTXT(provider="ollama", model_name="llama3")
            original_source, contract_name = analyzer._extract_source_metadata_from_txt_header(txt_path)

            self.assertEqual(contract_name, "SSOE")
            self.assertEqual(original_source, str(original))

    def test_prepare_context_includes_contract_and_file(self):
        analyzer = RAGCapabilityAnalyzerTXT(provider="ollama", model_name="llama3")
        docs = [
            Document(
                page_content="Evidence chunk",
                metadata={"contract_name": "CDAC", "filename": "pp_doc_1"},
            )
        ]
        ctx = analyzer._prepare_context(docs)
        self.assertIn("Contract: CDAC", ctx)
        self.assertIn("File: pp_doc_1", ctx)


if __name__ == "__main__":
    unittest.main()

