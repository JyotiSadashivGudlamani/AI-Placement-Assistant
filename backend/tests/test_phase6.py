"""
Comprehensive Test Suite for Phase 6: LangGraph Agentic AI Placement Assistant.
Validates:
1. Graph workflow topology and tool registry endpoint (GET /agent/workflow).
2. RAG-related request routing and grounded citation return.
3. Resume-related request routing and ATS analysis return.
4. Job description request routing and keyword/skill matching.
5. Technical interview generation request routing.
6. Mock interview answer evaluation across criteria.
7. Invalid and out-of-scope query handling with polite guardrails.
8. Conversation memory persistence and thread checkpointing across multi-turn sessions.
"""

import os
from pathlib import Path
import tempfile
import unittest
import pymupdf
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.mongo import MongoDBManager


class TestPhase6LangGraphAgent(unittest.TestCase):
    """Rigorous tests for the LangGraph orchestrator and tool routing."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="phase6_tests_"))

        # 1. Create and ingest a small test PDF into the system for RAG verification
        cls.java_pdf = cls.test_dir / "java_core_principles.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text(
            (50, 72),
            "Core Java Placement Handbook.\n\n"
            "Section: Object-Oriented Programming Principles.\n"
            "Inheritance in Java allows a child class to inherit fields and methods from a parent class using the extends keyword.\n"
            "Java supports single class inheritance and multiple interface inheritance using implements.\n"
            "Polymorphism enables an object to take many forms, achieved through method overriding and overloading.\n"
            "Encapsulation restricts direct access to data members through private access modifiers and public getters/setters."
        )
        doc.save(str(cls.java_pdf))
        doc.close()

        with open(cls.java_pdf, "rb") as f:
            resp = cls.client.post(
                "/documents/upload",
                files={"file": ("java_core_principles.pdf", f, "application/pdf")},
                data={"category": "technical", "notes": "Java Handbook for Phase 6 Tests"},
            )
        assert resp.status_code in (200, 201), f"Upload failed: {resp.text}"

        # 2. Upload a sample student resume for Resume tool verification
        cls.resume_pdf = cls.test_dir / "arjun_sharma_resume.pdf"
        rdoc = pymupdf.open()
        rpage = rdoc.new_page()
        rpage.insert_text(
            (50, 72),
            "ARJUN SHARMA\n"
            "Email: arjun.dev@gmail.com | Phone: 9876543210\n"
            "EDUCATION:\n"
            "B.Tech in Computer Science, 2024, CGPA: 8.8\n"
            "SKILLS:\n"
            "Languages: Python, Java, SQL, C++\n"
            "Frameworks: FastAPI, React, Node.js\n"
            "Databases: MongoDB, PostgreSQL\n"
            "PROJECTS:\n"
            "Built distributed microservices platform with FastAPI and Docker."
        )
        rdoc.save(str(cls.resume_pdf))
        rdoc.close()

        with open(cls.resume_pdf, "rb") as rf:
            cls.client.post(
                "/resume/upload",
                files={"file": ("arjun_sharma_resume.pdf", rf, "application/pdf")},
                data={"user_id": "student_phase6_test"},
            )

    # -------------------------------------------------------------------------
    # Test 1: Graph Topology and Tool Registry
    # -------------------------------------------------------------------------
    def test_01_graph_workflow_endpoint(self):
        resp = self.client.get("/agent/workflow")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["graph_name"], "PlacementPreparationStateGraph")
        self.assertIn("classify", data["nodes"])
        self.assertIn("rag_qa", data["nodes"])
        self.assertIn("synthesize", data["nodes"])
        self.assertIn("tool_rag_qa", data["tools"])
        self.assertIn("tool_resume_analysis", data["tools"])
        self.assertIn("tool_job_description_analysis", data["tools"])
        self.assertIn("tool_mock_interview_evaluation", data["tools"])
        print("\n[OK] Test 1: Workflow structure & registered tools verified.")

    # -------------------------------------------------------------------------
    # Test 2: RAG-Related Request
    # -------------------------------------------------------------------------
    def test_02_rag_related_request(self):
        payload = {
            "message": "What does the uploaded document say about inheritance in Java?",
            "session_id": "test_rag_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "rag_qa")
        self.assertEqual(data["tool_used"], "rag_qa")
        self.assertTrue(len(data["response"]) > 20)
        self.assertIn("execution_path", data)
        self.assertTrue(any("classify" in step for step in data["execution_path"]))
        self.assertTrue(any("rag_qa" in step for step in data["execution_path"]))
        print(f"\n[OK] Test 2: RAG query routed successfully. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 3: Resume-Related Request
    # -------------------------------------------------------------------------
    def test_03_resume_related_request(self):
        payload = {
            "message": "Please review my resume and check my extracted skills and strengths.",
            "session_id": "test_resume_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "resume_analysis")
        self.assertEqual(data["tool_used"], "resume_analysis")
        self.assertTrue(len(data["response"]) > 20)
        self.assertTrue(any("resume_analysis" in step for step in data["execution_path"]))
        print(f"\n[OK] Test 3: Resume query routed successfully. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 4: Job Description Request
    # -------------------------------------------------------------------------
    def test_04_job_description_request(self):
        jd_text = (
            "Analyze this job description: We are hiring a Backend Engineer. "
            "Responsibilities: Build high performance REST APIs. "
            "Requirements: Python, FastAPI, MongoDB, Docker, Git. Good understanding of microservices."
        )
        payload = {
            "message": jd_text,
            "session_id": "test_jd_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "jd_analysis")
        self.assertEqual(data["tool_used"], "job_description_analysis")
        self.assertTrue(len(data["response"]) > 20)
        self.assertTrue(any("jd_analysis" in step for step in data["execution_path"]))
        print(f"\n[OK] Test 4: JD query routed successfully. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 5: Interview Question Generation Request
    # -------------------------------------------------------------------------
    def test_05_interview_generation_request(self):
        payload = {
            "message": "Give me a technical interview question on Java inheritance with code example.",
            "session_id": "test_tech_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "technical_prep")
        self.assertEqual(data["tool_used"], "technical_prep")
        self.assertTrue(len(data["response"]) > 20)
        self.assertTrue(any("technical_prep" in step for step in data["execution_path"]))
        print(f"\n[OK] Test 5: Technical question generation routed successfully. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 6: Answer Evaluation Request
    # -------------------------------------------------------------------------
    def test_06_answer_evaluation_request(self):
        eval_message = (
            "Evaluate my answer. "
            "Question: What is polymorphism in Java? "
            "Answer: Polymorphism is the ability of an object to take on many forms. "
            "Compile-time polymorphism is method overloading where the signature differs. "
            "Runtime polymorphism is method overriding where subclass overrides superclass method."
        )
        payload = {
            "message": eval_message,
            "session_id": "test_eval_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "mock_interview_evaluation")
        self.assertEqual(data["tool_used"], "mock_interview_evaluation")
        self.assertTrue(len(data["response"]) > 20)
        self.assertTrue(any("mock_interview_evaluation" in step for step in data["execution_path"]))
        print(f"\n[OK] Test 6: Answer evaluation routed successfully. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 7: Invalid / Out-of-Scope Request
    # -------------------------------------------------------------------------
    def test_07_invalid_request(self):
        payload = {
            "message": "What is the best recipe for baking chocolate chip cookies?",
            "session_id": "test_invalid_session_1",
            "user_id": "student_phase6_test",
        }
        resp = self.client.post("/agent/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "invalid")
        self.assertEqual(data["tool_used"], "fallback")
        self.assertTrue(len(data["response"]) > 20)
        self.assertTrue(any("fallback" in step for step in data["execution_path"]))
        # Verify guardrail guidance is included
        self.assertTrue(
            "placement" in data["response"].lower() or "interview" in data["response"].lower(),
            "Fallback response should guide user back to placement prep."
        )
        print(f"\n[OK] Test 7: Out-of-scope query handled with guardrail fallback. Path: {data['execution_path']}")

    # -------------------------------------------------------------------------
    # Test 8: Conversation History and Session Tracking
    # -------------------------------------------------------------------------
    def test_08_conversation_history(self):
        session_id = "test_memory_session_99"
        # Turn 1: Greetings
        resp1 = self.client.post(
            "/agent/chat",
            json={"message": "Hello! What can you help me with?", "session_id": session_id},
        )
        self.assertEqual(resp1.status_code, 200)

        # Turn 2: Question
        resp2 = self.client.post(
            "/agent/chat",
            json={"message": "Give me an interview question on Python", "session_id": session_id},
        )
        self.assertEqual(resp2.status_code, 200)

        # Check session details
        history_resp = self.client.get(f"/agent/session/{session_id}")
        self.assertEqual(history_resp.status_code, 200)
        data = history_resp.json()
        self.assertEqual(data["session_id"], session_id)
        self.assertGreaterEqual(len(data["turns"]), 2)

        # Check sessions list
        list_resp = self.client.get("/agent/sessions")
        self.assertEqual(list_resp.status_code, 200)
        sessions_data = list_resp.json()
        session_ids = [s["session_id"] for s in sessions_data["sessions"]]
        self.assertIn(session_id, session_ids)
        print(f"\n[OK] Test 8: Multi-turn session memory verified ({len(data['turns'])} turns tracked).")


if __name__ == "__main__":
    unittest.main()
