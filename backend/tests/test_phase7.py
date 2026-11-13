"""
Comprehensive Test Suite for Phase 7: User Management, Persistence, Ownership, and Analytics.
Validates:
1. Student registration with bcrypt password hashing and token generation.
2. Duplicate email registration rejection.
3. Login authentication (valid credentials vs invalid password vs non-existent user).
4. Protected endpoint token validation (GET /auth/me).
5. User-specific document ownership and cross-user data isolation.
6. Document ownership permission checks (User B cannot delete User A's document -> 403 Forbidden).
7. User-specific chat history isolation and access denial for other users.
8. Student preparation analytics calculations and topic recommendations.
"""

import os
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
import pymupdf
import bcrypt
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.mongo import MongoDBManager


class TestPhase7UserManagementAndAnalytics(unittest.TestCase):
    """Rigorous tests for Phase 7 security, ownership, and student analytics."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="phase7_tests_"))

        cls.run_id = uuid4().hex[:6]
        cls.email_a = f"alex_{cls.run_id}@placement.edu"
        cls.email_b = f"beth_{cls.run_id}@placement.edu"

        # Create two separate test PDF fixtures
        cls.doc_a_pdf = cls.test_dir / "alex_specialized_resume.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Alex Rivers - Senior Python and Backend Engineer Resume.")
        doc.save(str(cls.doc_a_pdf))
        doc.close()

        cls.doc_b_pdf = cls.test_dir / "beth_distributed_systems.pdf"
        bdoc = pymupdf.open()
        bpage = bdoc.new_page()
        bpage.insert_text((50, 72), "Beth Chen - Distributed Systems and Java Microservices Guide.")
        bdoc.save(str(cls.doc_b_pdf))
        bdoc.close()

    # -------------------------------------------------------------------------
    # Test 1: User Registration & Secure Password Hashing
    # -------------------------------------------------------------------------
    def test_01_user_registration(self):
        # 1. Register User A
        payload = {
            "email": self.email_a,
            "password": "SecurePassword123!",
            "full_name": "Alex Rivers",
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], self.email_a)
        self.assertEqual(data["user"]["full_name"], "Alex Rivers")
        self.assertTrue(data["user"]["user_id"].startswith("user_"))

        # Save credentials for later tests
        self.__class__.user_a_token = data["access_token"]
        self.__class__.user_a_id = data["user"]["user_id"]
        self.__class__.user_a_headers = {"Authorization": f"Bearer {data['access_token']}"}

        # Verify password is NOT stored in plain text in MongoDB
        mongo = MongoDBManager.get_instance()
        user_record = mongo.get_user_by_email(self.email_a)
        self.assertIsNotNone(user_record)
        self.assertNotIn("SecurePassword123!", str(user_record))
        self.assertTrue(user_record["hashed_password"].startswith("$2b$"))
        self.assertTrue(bcrypt.checkpw(b"SecurePassword123!", user_record["hashed_password"].encode("utf-8")))

        # 2. Verify duplicate registration fails with 400 Bad Request
        dup_resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(dup_resp.status_code, 400)
        self.assertIn("already exists", dup_resp.json()["detail"].lower())

        # 3. Register User B
        payload_b = {
            "email": self.email_b,
            "password": "StrongSecret456!",
            "full_name": "Beth Chen",
        }
        resp_b = self.client.post("/auth/register", json=payload_b)
        self.assertEqual(resp_b.status_code, 201)
        data_b = resp_b.json()
        self.__class__.user_b_token = data_b["access_token"]
        self.__class__.user_b_id = data_b["user"]["user_id"]
        self.__class__.user_b_headers = {"Authorization": f"Bearer {data_b['access_token']}"}

        print("\n[OK] Test 1: User registration and bcrypt password hashing verified.")

    # -------------------------------------------------------------------------
    # Test 2: User Login
    # -------------------------------------------------------------------------
    def test_02_user_login(self):
        login_payload = {
            "email": self.email_a,
            "password": "SecurePassword123!",
        }
        resp = self.client.post("/auth/login", json=login_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["user_id"], self.user_a_id)
        print("\n[OK] Test 2: User login with valid credentials verified.")

    # -------------------------------------------------------------------------
    # Test 3: Invalid Login Attempts
    # -------------------------------------------------------------------------
    def test_03_invalid_login(self):
        # Incorrect password
        bad_pw_resp = self.client.post(
            "/auth/login",
            json={"email": self.email_a, "password": "WrongPassword999!"},
        )
        self.assertEqual(bad_pw_resp.status_code, 401)
        self.assertIn("Invalid email or password", bad_pw_resp.json()["detail"])

        # Non-existent user
        non_user_resp = self.client.post(
            "/auth/login",
            json={"email": f"nonexistent_{self.run_id}@placement.edu", "password": "AnyPassword123!"},
        )
        self.assertEqual(non_user_resp.status_code, 401)
        print("\n[OK] Test 3: Invalid login rejected with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # Test 4: Protected Endpoints & Token Validation
    # -------------------------------------------------------------------------
    def test_04_protected_endpoints(self):
        # 1. No token -> 401
        no_auth = self.client.get("/auth/me")
        self.assertEqual(no_auth.status_code, 401)

        # 2. Tampered token -> 401
        bad_auth = self.client.get("/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
        self.assertEqual(bad_auth.status_code, 401)

        # 3. Valid User A token -> 200 with Alex's profile
        resp_a = self.client.get("/auth/me", headers=self.user_a_headers)
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(resp_a.json()["user_id"], self.user_a_id)
        self.assertEqual(resp_a.json()["email"], self.email_a)

        # 4. Valid User B token -> 200 with Beth's profile
        resp_b = self.client.get("/auth/me", headers=self.user_b_headers)
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(resp_b.json()["user_id"], self.user_b_id)
        self.assertEqual(resp_b.json()["email"], self.email_b)

        print("\n[OK] Test 4: Protected endpoint token validation verified.")

    # -------------------------------------------------------------------------
    # Test 5: Document Ownership & Cross-User Data Separation
    # -------------------------------------------------------------------------
    def test_05_document_ownership_and_separation(self):
        # 1. User A uploads Document A
        with open(self.doc_a_pdf, "rb") as fa:
            resp_a = self.client.post(
                "/documents/upload",
                files={"file": ("alex_specialized_resume.pdf", fa, "application/pdf")},
                data={"category": "resume"},
                headers=self.user_a_headers,
            )
        self.assertEqual(resp_a.status_code, 201)
        doc_a_id = resp_a.json()["document_id"]

        # 2. User B uploads Document B
        with open(self.doc_b_pdf, "rb") as fb:
            resp_b = self.client.post(
                "/documents/upload",
                files={"file": ("beth_distributed_systems.pdf", fb, "application/pdf")},
                data={"category": "placement"},
                headers=self.user_b_headers,
            )
        self.assertEqual(resp_b.status_code, 201)
        doc_b_id = resp_b.json()["document_id"]

        # 3. User A lists documents: must only see Document A
        list_a = self.client.get("/documents", headers=self.user_a_headers)
        self.assertEqual(list_a.status_code, 200)
        a_doc_ids = [d["document_id"] for d in list_a.json()["documents"]]
        self.assertIn(doc_a_id, a_doc_ids)
        self.assertNotIn(doc_b_id, a_doc_ids, "User A must NOT see User B's documents.")

        # 4. User B lists documents: must only see Document B
        list_b = self.client.get("/documents", headers=self.user_b_headers)
        self.assertEqual(list_b.status_code, 200)
        b_doc_ids = [d["document_id"] for d in list_b.json()["documents"]]
        self.assertIn(doc_b_id, b_doc_ids)
        self.assertNotIn(doc_a_id, b_doc_ids, "User B must NOT see User A's documents.")

        # 5. User B attempts to access User A's document status -> 403 Forbidden
        status_b_try_a = self.client.get(f"/documents/{doc_a_id}", headers=self.user_b_headers)
        self.assertEqual(status_b_try_a.status_code, 403)

        # 6. User B attempts to delete User A's document -> 403 Forbidden
        del_b_try_a = self.client.delete(f"/documents/{doc_a_id}", headers=self.user_b_headers)
        self.assertEqual(del_b_try_a.status_code, 403)
        self.assertIn("permission", del_b_try_a.json()["detail"].lower())

        # 7. User A deletes their own document -> 200 OK
        del_a = self.client.delete(f"/documents/{doc_a_id}", headers=self.user_a_headers)
        self.assertEqual(del_a.status_code, 200)

        print("\n[OK] Test 5: Document ownership, isolation, and 403 deletion guards verified.")

    # -------------------------------------------------------------------------
    # Test 6: Chat Persistence and User Separation
    # -------------------------------------------------------------------------
    def test_06_chat_persistence_and_separation(self):
        session_a = f"alex_chat_{self.run_id}"

        # 1. User A asks a question
        chat_resp = self.client.post(
            "/chat",
            json={
                "question": "What are core Java inheritance concepts?",
                "session_id": session_a,
            },
            headers=self.user_a_headers,
        )
        self.assertEqual(chat_resp.status_code, 200)

        # 2. User A lists chats -> sees session_a
        chats_a = self.client.get("/chats", headers=self.user_a_headers)
        self.assertEqual(chats_a.status_code, 200)
        a_session_ids = [s["session_id"] for s in chats_a.json()["sessions"]]
        self.assertIn(session_a, a_session_ids)

        # 3. User B lists chats -> does NOT see User A's session
        chats_b = self.client.get("/chats", headers=self.user_b_headers)
        self.assertEqual(chats_b.status_code, 200)
        b_session_ids = [s["session_id"] for s in chats_b.json()["sessions"]]
        self.assertNotIn(session_a, b_session_ids, "User B must not see User A's chats.")

        # 4. User B attempts to view User A's chat session -> 403 Forbidden
        view_b_try_a = self.client.get(f"/chats/{session_a}", headers=self.user_b_headers)
        self.assertEqual(view_b_try_a.status_code, 403)

        # 5. User B attempts to delete User A's chat session -> 403 Forbidden
        del_b_try_a = self.client.delete(f"/chats/{session_a}", headers=self.user_b_headers)
        self.assertEqual(del_b_try_a.status_code, 403)

        print("\n[OK] Test 6: Chat persistence and cross-user isolation verified.")

    # -------------------------------------------------------------------------
    # Test 7: Student Preparation Analytics Engine
    # -------------------------------------------------------------------------
    def test_07_analytics_calculations(self):
        # 1. Insert known records for User B directly to verify analytics computation
        mongo = MongoDBManager.get_instance()
        mongo.save_aptitude_result({
            "attempt_id": f"apt_{self.run_id}",
            "user_id": self.user_b_id,
            "category": "quantitative",
            "total_questions": 5,
            "correct_count": 4,
            "score_percentage": 80.0,
        })
        mongo.save_mock_interview({
            "session_id": f"mock_{self.run_id}",
            "user_id": self.user_b_id,
            "topic": "Java",
            "scores": {
                "correctness": 8,
                "relevance": 9,
                "completeness": 8,
                "clarity": 8,
                "communication": 9,
                "overall_score": 8.4,
            },
            "overall_score": 8.4,
        })

        # 2. Query analytics for User B
        resp = self.client.get("/analytics/dashboard", headers=self.user_b_headers)
        self.assertEqual(resp.status_code, 200)
        analytics = resp.json()

        self.assertEqual(analytics["user_id"], self.user_b_id)
        self.assertGreaterEqual(analytics["total_uploaded_documents"], 1)
        self.assertEqual(analytics["aptitude_stats"]["total_tests"], 1)
        self.assertEqual(analytics["aptitude_stats"]["average_score"], 80.0)
        self.assertEqual(analytics["mock_interview_stats"]["total_interviews"], 1)
        self.assertEqual(analytics["mock_interview_stats"]["average_overall"], 8.4)

        # 3. Verify topic-wise progress and recommendations exist
        self.assertTrue(len(analytics["topic_wise_progress"]) >= 5)
        self.assertTrue(len(analytics["recommended_next_topics"]) >= 1)

        print("\n[OK] Test 7: Dashboard analytics calculations and smart recommendations verified.")


if __name__ == "__main__":
    unittest.main()
