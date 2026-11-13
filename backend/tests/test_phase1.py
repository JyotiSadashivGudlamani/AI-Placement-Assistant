"""
Comprehensive test suite for Phase 1: Document Ingestion and Vector Storage.
Tests PDF extraction (PyMuPDF), DOCX extraction (python-docx), TXT extraction,
multi-page page number preservation, chunk overlap, embedding dimensions (384),
ChromaDB storage, duplicate prevention, and document deletion.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in Python path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import docx
import pymupdf

from backend.app.services.document_loader import (
    DocumentLoader,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from backend.app.services.chunking import TextChunker
from backend.app.services.embeddings import EmbeddingService
from backend.app.services.vector_store import VectorStoreService


class TestPhase1DocumentIngestion(unittest.TestCase):
    """Test suite covering all requirements of Phase 1."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp(prefix="phase1_test_"))
        cls.loader = DocumentLoader(max_file_size_bytes=1024 * 1024)  # 1MB for test
        cls.embedding_service = EmbeddingService.get_instance()

        # Isolated ChromaDB directory for tests
        cls.chroma_dir = cls.test_dir / "test_chroma_db"
        cls.vector_store = VectorStoreService(
            chroma_db_dir=cls.chroma_dir,
            collection_name="test_phase1_collection",
            embedding_service=cls.embedding_service,
        )

        # Existing sample PDF path
        cls.sample_pdf_path = (
            Path(__file__).resolve().parent.parent
            / "experiments"
            / "sample_resume.pdf"
        )

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary test directory
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        # Reset test collection before each test that uses the vector store
        self.vector_store.reset_collection()

    # -------------------------------------------------------------
    # 1. Test PDF Extraction using PyMuPDF
    # -------------------------------------------------------------
    def test_pdf_extraction(self):
        """Verify extraction from real resume PDF using PyMuPDF."""
        self.assertTrue(
            self.sample_pdf_path.exists(),
            f"Sample resume not found at {self.sample_pdf_path}",
        )

        doc = self.loader.load_from_path(self.sample_pdf_path, category="resume")

        self.assertEqual(doc.file_type, "pdf")
        self.assertGreater(doc.total_pages, 0)
        self.assertGreater(doc.total_characters, 100)
        self.assertEqual(len(doc.pages), doc.total_pages)
        self.assertEqual(doc.pages[0].page_number, 1)

        # Content assertions
        full_text = doc.full_text
        self.assertIn("Jyoti", full_text)
        self.assertTrue("Computer Science" in full_text or "Engineering" in full_text)
        print("\n[PASS] test_pdf_extraction: Successfully extracted sample_resume.pdf via PyMuPDF.")

    # -------------------------------------------------------------
    # 2. Test Multi-Page PDF Page Numbers Preservation
    # -------------------------------------------------------------
    def test_multipage_pdf_page_numbers(self):
        """Create a 3-page PDF and verify that page numbers are preserved across chunks."""
        multi_pdf_path = self.test_dir / "multipage_sample.pdf"

        # Generate a 3-page synthetic PDF with PyMuPDF
        pdf_doc = pymupdf.open()
        p1 = pdf_doc.new_page()
        p1.insert_text(
            (50, 72),
            "PAGE ONE CONTENT: Candidate Profile. Core Skills: Python, FastAPI, React.",
        )
        p2 = pdf_doc.new_page()
        p2.insert_text(
            (50, 72),
            "PAGE TWO CONTENT: Professional Experience. Developed AI RAG microservices.",
        )
        p3 = pdf_doc.new_page()
        p3.insert_text(
            (50, 72),
            "PAGE THREE CONTENT: Education and Certifications. Bachelor of Engineering.",
        )
        pdf_doc.save(str(multi_pdf_path))
        pdf_doc.close()

        # Ingest document
        loaded_doc = self.loader.load_from_path(multi_pdf_path)
        self.assertEqual(loaded_doc.total_pages, 3)
        self.assertEqual(loaded_doc.pages[0].page_number, 1)
        self.assertEqual(loaded_doc.pages[1].page_number, 2)
        self.assertEqual(loaded_doc.pages[2].page_number, 3)

        self.assertIn("PAGE ONE CONTENT", loaded_doc.pages[0].text)
        self.assertIn("PAGE TWO CONTENT", loaded_doc.pages[1].text)
        self.assertIn("PAGE THREE CONTENT", loaded_doc.pages[2].text)

        # Chunk the document and verify each chunk maintains the accurate page number
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_document(loaded_doc)

        page_numbers_in_chunks = {c.page_number for c in chunks}
        self.assertEqual(page_numbers_in_chunks, {1, 2, 3})

        for chunk in chunks:
            self.assertIn(f"p{chunk.page_number}", chunk.chunk_id)
            self.assertEqual(chunk.metadata["page_number"], chunk.page_number)

        print("\n[PASS] test_multipage_pdf_page_numbers: Correctly preserved pages 1, 2, 3 across chunks.")

    # -------------------------------------------------------------
    # 3. Test DOCX Extraction (Paragraphs + Tables)
    # -------------------------------------------------------------
    def test_docx_extraction(self):
        """Create a DOCX file with paragraphs and tables and verify extraction."""
        docx_path = self.test_dir / "sample_resume.docx"

        doc = docx.Document()
        doc.add_heading("Jyoti - AI Engineer Candidate", level=1)
        doc.add_paragraph("Summary: Experienced in FastAPI, ChromaDB, and LLM integrations.")
        doc.add_paragraph("Projects: Built AI Placement Assistant with RAG pipeline.")

        # Add table for Education
        table = doc.add_table(rows=3, cols=3)
        headers = ["Degree", "Institution", "Year"]
        for col_idx, header in enumerate(headers):
            table.cell(0, col_idx).text = header

        row1 = ["B.E. Computer Science", "Engineering College", "2026"]
        for col_idx, val in enumerate(row1):
            table.cell(1, col_idx).text = val

        row2 = ["Higher Secondary", "Science Academy", "2022"]
        for col_idx, val in enumerate(row2):
            table.cell(2, col_idx).text = val

        doc.save(str(docx_path))

        loaded_docx = self.loader.load_from_path(docx_path)
        self.assertEqual(loaded_docx.file_type, "docx")
        self.assertGreater(loaded_docx.total_characters, 50)

        full_text = loaded_docx.full_text
        # Assert paragraph content
        self.assertIn("Experienced in FastAPI", full_text)
        # Assert table content
        self.assertIn("B.E. Computer Science", full_text)
        self.assertIn("Engineering College", full_text)
        self.assertIn("Higher Secondary", full_text)
        print("\n[PASS] test_docx_extraction: Extracted paragraphs and tables from DOCX.")

    # -------------------------------------------------------------
    # 4. Test TXT Extraction
    # -------------------------------------------------------------
    def test_txt_extraction(self):
        """Verify reading plain text documents."""
        txt_path = self.test_dir / "skills.txt"
        txt_content = (
            "Technical Skills:\n"
            "- Languages: Python, JavaScript, Java, C++\n"
            "- Frameworks: FastAPI, React, Node.js\n"
            "- Databases: ChromaDB, MongoDB, MySQL"
        )
        txt_path.write_text(txt_content, encoding="utf-8")

        loaded_txt = self.loader.load_from_path(txt_path)
        self.assertEqual(loaded_txt.file_type, "txt")
        self.assertEqual(loaded_txt.total_pages, 1)
        self.assertIn("Languages: Python", loaded_txt.full_text)
        self.assertIn("ChromaDB, MongoDB", loaded_txt.full_text)
        print("\n[PASS] test_txt_extraction: Successfully extracted UTF-8 TXT content.")

    # -------------------------------------------------------------
    # 5. Test Invalid and Empty Files
    # -------------------------------------------------------------
    def test_invalid_and_empty_files(self):
        """Verify rejection of empty files, unsupported extensions, and oversized files."""
        # A. Unsupported extension
        invalid_ext_path = self.test_dir / "program.exe"
        invalid_ext_path.write_bytes(b"MZ binary executable code")
        with self.assertRaises(UnsupportedFileTypeError):
            self.loader.load_from_path(invalid_ext_path)

        # B. Empty file (0 bytes)
        empty_path = self.test_dir / "empty.pdf"
        empty_path.write_bytes(b"")
        with self.assertRaises(EmptyDocumentError):
            self.loader.load_from_path(empty_path)

        # C. Whitespace-only text file
        blank_txt_path = self.test_dir / "blank.txt"
        blank_txt_path.write_text("   \n\n\t  ", encoding="utf-8")
        with self.assertRaises(EmptyDocumentError):
            self.loader.load_from_path(blank_txt_path)

        # D. Oversized file
        oversized_path = self.test_dir / "huge.txt"
        oversized_path.write_bytes(b"A" * (1024 * 1024 + 100))  # Exceeds 1MB loader limit
        with self.assertRaises(FileTooLargeError):
            self.loader.load_from_path(oversized_path)

        print("\n[PASS] test_invalid_and_empty_files: Handled extension, 0-byte, whitespace, and size limits.")

    # -------------------------------------------------------------
    # 6. Test Chunk Overlap & Splitter
    # -------------------------------------------------------------
    def test_chunk_overlap(self):
        """Verify recursive chunking overlap behavior."""
        text = (
            "Sentence one describes Python programming. "
            "Sentence two explains FastAPI web APIs. "
            "Sentence three discusses sentence transformers and vector retrieval. "
            "Sentence four focuses on ChromaDB vector storage and indexing. "
            "Sentence five covers LLM generation with Ollama."
        )

        chunker = TextChunker(chunk_size=120, chunk_overlap=40)
        chunks = chunker.chunk_text(text, document_id="doc_overlap_test")

        self.assertGreater(len(chunks), 1)

        # Verify consecutive chunks share overlap
        for i in range(len(chunks) - 1):
            tail = chunks[i].text[-20:]
            # The tail or part of it should be near the start of the next chunk
            overlap_found = any(
                word in chunks[i + 1].text for word in tail.split() if len(word) > 4
            )
            self.assertTrue(
                overlap_found,
                f"Expected overlap between chunk {i} and {i+1}",
            )

        # Test invalid overlap configuration
        with self.assertRaises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=100)

        with self.assertRaises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=150)

        print("\n[PASS] test_chunk_overlap: Overlap verified across consecutive chunks.")

    # -------------------------------------------------------------
    # 7. Test Embedding Dimensions
    # -------------------------------------------------------------
    def test_embedding_dimensions(self):
        """Verify embeddings generated with all-MiniLM-L6-v2 have dimension 384."""
        query = "What is the candidate's experience with machine learning?"
        single_vec = self.embedding_service.embed_query(query)

        self.assertEqual(len(single_vec), 384)
        self.assertIsInstance(single_vec[0], float)

        # Test batch embedding
        batch = [
            "Python developer with backend skills",
            "Frontend React and Vite application",
            "ChromaDB vector database indexing",
        ]
        vectors = self.embedding_service.embed_texts(batch)

        self.assertEqual(len(vectors), 3)
        for vec in vectors:
            self.assertEqual(len(vec), 384)

        print("\n[PASS] test_embedding_dimensions: Confirmed all-MiniLM-L6-v2 produces exact 384-dim vectors.")

    # -------------------------------------------------------------
    # 8. Test ChromaDB Storage and Semantic Search
    # -------------------------------------------------------------
    def test_chromadb_storage(self):
        """Verify document ingestion, metadata indexing, and semantic search in ChromaDB."""
        loaded_doc = self.loader.load_from_path(self.sample_pdf_path)
        stored_count = self.vector_store.store_document(loaded_doc)

        self.assertGreater(stored_count, 0)
        self.assertEqual(self.vector_store.count(), stored_count)

        # Verify metadata fields are stored
        chunks = self.vector_store.get_document_chunks(loaded_doc.document_id)
        self.assertEqual(len(chunks), stored_count)

        for chunk_item in chunks:
            meta = chunk_item["metadata"]
            self.assertEqual(meta["filename"], loaded_doc.filename)
            self.assertEqual(meta["file_type"], "pdf")
            self.assertEqual(meta["category"], "resume")
            self.assertIn("chunk_id", meta)
            self.assertIn("page_number", meta)

        # Test semantic search
        search_results = self.vector_store.search(
            query="What programming skills does Jyoti have?",
            n_results=3,
        )

        self.assertGreater(len(search_results), 0)
        top_result = search_results[0]
        self.assertIn("similarity", top_result)
        self.assertIn("text", top_result)
        self.assertGreater(top_result["similarity"], 0.0)

        print(
            f"\n[PASS] test_chromadb_storage: Stored {stored_count} chunks. "
            f"Top search similarity: {top_result['similarity']}"
        )

    # -------------------------------------------------------------
    # 9. Test Document Deletion and Deduplication
    # -------------------------------------------------------------
    def test_document_deletion_and_deduplication(self):
        """Verify duplicate prevention during re-ingestion and complete deletion."""
        loaded_doc = self.loader.load_from_path(self.sample_pdf_path)

        # First ingestion
        count_first = self.vector_store.store_document(loaded_doc)
        total_after_first = self.vector_store.count()
        self.assertEqual(total_after_first, count_first)

        # Re-ingestion of the exact same document ID must NOT duplicate records
        count_second = self.vector_store.store_document(loaded_doc)
        total_after_second = self.vector_store.count()
        self.assertEqual(
            total_after_second,
            total_after_first,
            "Re-ingestion must not create duplicate records in ChromaDB",
        )

        # Test document deletion
        deleted_count = self.vector_store.delete_document(loaded_doc.document_id)
        self.assertEqual(deleted_count, total_after_first)
        self.assertEqual(self.vector_store.count(), 0)

        # Verify search returns empty now
        post_delete_search = self.vector_store.search("Jyoti")
        self.assertEqual(len(post_delete_search), 0)

        print("\n[PASS] test_document_deletion_and_deduplication: Re-ingestion prevented duplicates and deletion cleared vectors.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
