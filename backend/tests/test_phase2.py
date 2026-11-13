"""
Comprehensive verification test suite for Phase 2: FastAPI Backend and RAG Q&A.
Tests:
1. Java PDF generation and upload via POST /documents/upload.
2. Question asking about inheritance via POST /chat.
3. Relevant content retrieval verification.
4. Llama 3.2:3b generated answer verification.
5. Exact source filename and page number citation verification.
6. Unrelated question asking.
7. Verification that assistant does not invent document facts or fake citations.
8. API error handling (invalid extensions, empty files, non-existent documents, empty questions).
9. Document listing and conversation history tracking.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymupdf
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.db.mongo import MongoDBManager
from backend.app.main import app
from backend.app.services.vector_store import VectorStoreService


class TestPhase2FastAPIRAG(unittest.TestCase):
    """Test suite covering all FastAPI endpoints and RAG question answering."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="phase2_test_"))
        cls.java_pdf_path = cls.test_dir / "java_oop_guide.pdf"

        # Generate a high-quality 2-page Java OOP PDF fixture
        doc = pymupdf.open()

        # Page 1: Core Inheritance & Extends keyword
        p1 = doc.new_page()
        p1_text = (
            "JAVA OBJECT-ORIENTED PROGRAMMING: INHERITANCE GUIDE\n\n"
            "Inheritance in Java is a core object-oriented mechanism where a subclass derives attributes "
            "and methods from an existing superclass. In Java, inheritance is explicitly declared using the "
            "'extends' keyword.\n\n"
            "Key Characteristics of Java Inheritance:\n"
            "1. Single Inheritance: Java allows a class to extend only one direct superclass, preventing the diamond problem.\n"
            "2. Superclass vs Subclass: The parent class is called the superclass; the inheriting child is the subclass.\n"
            "3. Super Keyword: Subclasses use 'super' to invoke superclass constructors and overridden methods.\n"
            "4. Method Overriding: A subclass can redefine a parent method using the @Override annotation."
        )
        p1.insert_text((50, 72), p1_text)

        # Page 2: Interfaces and Polymorphism
        p2 = doc.new_page()
        p2_text = (
            "JAVA POLYMORPHISM AND INTERFACES\n\n"
            "Polymorphism allows objects of different classes to respond to the same method call in distinct ways.\n"
            "In Java, multiple inheritance of type is achieved through Interfaces using the 'implements' keyword.\n"
            "An interface is a contract containing abstract method signatures that concrete classes must implement.\n"
            "Dynamic method dispatch resolves method calls at runtime based on the actual object instance."
        )
        p2.insert_text((50, 72), p2_text)

        doc.save(str(cls.java_pdf_path))
        doc.close()

        cls.java_doc_id = None

    @classmethod
    def tearDownClass(cls):
        # Cleanup test document if still exists
        if cls.java_doc_id:
            try:
                vs = VectorStoreService()
                vs.delete_document(cls.java_doc_id)
                mongo = MongoDBManager.get_instance()
                if mongo.is_connected:
                    mongo.delete_document(cls.java_doc_id)
            except Exception:
                pass

    # -------------------------------------------------------------
    # 1. Test Root and Health Probes
    # -------------------------------------------------------------
    def test_01_root_and_health(self):
        """Verify API root and subsystem health endpoints."""
        root_resp = self.client.get("/")
        self.assertEqual(root_resp.status_code, 200)
        data = root_resp.json()
        self.assertEqual(data["status"], "Running")
        self.assertIn("documentation", data)

        health_resp = self.client.get("/health")
        self.assertIn(health_resp.status_code, [200, 207])
        health_data = health_resp.json()
        self.assertIn("components", health_data)
        self.assertIn("chromadb", health_data["components"])
        self.assertIn("ollama", health_data["components"])
        print("\n[PASS] test_01_root_and_health: Verified GET / and GET /health")

    # -------------------------------------------------------------
    # 2. Test Java PDF Upload (POST /documents/upload)
    # -------------------------------------------------------------
    def test_02_upload_java_pdf(self):
        """Test uploading Java OOP PDF and indexing in ChromaDB and MongoDB."""
        with open(self.java_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        response = self.client.post(
            "/documents/upload",
            files={"file": ("java_oop_guide.pdf", pdf_bytes, "application/pdf")},
            data={"category": "java"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("document_id", data)
        self.assertEqual(data["filename"], "java_oop_guide.pdf")
        self.assertEqual(data["file_type"], "pdf")
        self.assertEqual(data["total_pages"], 2)
        self.assertGreaterEqual(data["total_chunks"], 2)
        self.assertEqual(data["status"], "ready")

        TestPhase2FastAPIRAG.java_doc_id = data["document_id"]
        print(f"\n[PASS] test_02_upload_java_pdf: Ingested {data['filename']} (ID: {data['document_id']}) with {data['total_chunks']} chunks.")

    # -------------------------------------------------------------
    # 3. Test Question about Inheritance (POST /chat)
    # -------------------------------------------------------------
    def test_03_ask_inheritance_question_and_verify_rag(self):
        """Ask question about inheritance, verify context retrieval, answer, source, and page number."""
        self.assertIsNotNone(self.java_doc_id, "Java document must be uploaded first.")

        chat_payload = {
            "question": "How does inheritance work in Java and what keyword is used to declare it?",
            "top_k": 3,
            "category": "java",
        }

        response = self.client.post("/chat", json=chat_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Assertions on RAG response structure
        self.assertIn("session_id", data)
        self.assertIn("answer", data)
        self.assertIn("citations", data)
        self.assertGreater(data["retrieved_chunks_count"], 0)
        self.assertTrue(data["has_document_context"])

        answer_text = data["answer"]
        print(f"\n[PASS] Generated Answer:\n{answer_text}\n")

        # Verify inheritance keywords in generated answer
        answer_lower = answer_text.lower()
        self.assertTrue(
            "extends" in answer_lower or "subclass" in answer_lower or "inheritance" in answer_lower,
            "Answer must reference inheritance concepts",
        )

        # Verify source filename and exact page number
        citations = data["citations"]
        self.assertGreater(len(citations), 0, "Must return at least one verified citation.")

        citation = citations[0]
        self.assertEqual(citation["filename"], "java_oop_guide.pdf")
        self.assertEqual(citation["page_number"], 1, "Inheritance details reside on Page 1 of the guide.")
        self.assertGreater(citation["similarity"], 0.0)

        print(
            f"[PASS] Citation Verified: File={citation['filename']}, "
            f"Page={citation['page_number']}, Similarity={citation['similarity']}"
        )

    # -------------------------------------------------------------
    # 4. Test Unrelated Question (Verify No Hallucination)
    # -------------------------------------------------------------
    def test_04_unrelated_question_grounding(self):
        """Ask an unrelated question and verify assistant does not invent facts or fake citations."""
        chat_payload = {
            "question": "What is the capital city of Australia and what is its average climate in July?",
            "top_k": 3,
            "category": "java",
        }

        response = self.client.post("/chat", json=chat_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        answer_lower = data["answer"].lower()
        negative_markers = [
            "not contain sufficient information",
            "not mentioned",
            "does not contain",
            "no information",
            "not available in the provided document",
        ]

        grounded_rejection = any(marker in answer_lower for marker in negative_markers)
        self.assertTrue(
            grounded_rejection or len(data["citations"]) == 0,
            f"Assistant must decline or avoid fake citations for unrelated query. Answer: {data['answer']}",
        )
        print(f"\n[PASS] test_04_unrelated_question_grounding: Properly declined or ungrounded unrelated question.")

    # -------------------------------------------------------------
    # 5. Test API Error Handling and Validations
    # -------------------------------------------------------------
    def test_05_api_error_handling(self):
        """Verify 415, 400, 404, and 422 HTTP status codes for invalid requests."""
        # A. Unsupported file extension (.exe)
        bad_ext_resp = self.client.post(
            "/documents/upload",
            files={"file": ("malicious.exe", b"binary_data", "application/octet-stream")},
        )
        self.assertEqual(bad_ext_resp.status_code, 415)

        # B. Empty file (0 bytes)
        empty_resp = self.client.post(
            "/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        self.assertEqual(empty_resp.status_code, 400)

        # C. Query non-existent document
        not_found_resp = self.client.get("/documents/doc_does_not_exist_9999")
        self.assertEqual(not_found_resp.status_code, 404)

        # D. Delete non-existent document
        delete_not_found = self.client.delete("/documents/doc_does_not_exist_9999")
        self.assertEqual(delete_not_found.status_code, 404)

        # E. Empty question in chat
        empty_chat_resp = self.client.post("/chat", json={"question": "   "})
        self.assertIn(empty_chat_resp.status_code, [400, 422])

        print("\n[PASS] test_05_api_error_handling: Verified 415, 400, 404, and 422 validation behaviors.")

    # -------------------------------------------------------------
    # 6. Test Document Listing and Session History
    # -------------------------------------------------------------
    def test_06_document_listing_and_sessions(self):
        """Verify GET /documents, GET /chats, and document status inspection."""
        # Check document list
        list_resp = self.client.get("/documents")
        self.assertEqual(list_resp.status_code, 200)
        docs_data = list_resp.json()
        self.assertIn("documents", docs_data)

        # Check document status
        status_resp = self.client.get(f"/documents/{self.java_doc_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertEqual(status_data["document"]["document_id"], self.java_doc_id)
        self.assertGreater(status_data["chunks_count"], 0)

        # Check chat sessions
        chats_resp = self.client.get("/chats")
        self.assertEqual(chats_resp.status_code, 200)

        print("\n[PASS] test_06_document_listing_and_sessions: Verified listing and status inspection.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
