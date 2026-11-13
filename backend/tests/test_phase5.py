"""
Comprehensive Phase 5 Test Suite.
Tests all 6 Placement Preparation Modules independently:
1. Module 1: Technical Interview Preparation
2. Module 2: HR Preparation
3. Module 3: Aptitude Practice
4. Module 4: Resume Analyser
5. Module 5: Job Description Analyser
6. Module 6: Mock Interview
"""

import os
from pathlib import Path
import tempfile
import unittest
import pymupdf
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.mongo import MongoDBManager


class TestPhase5PlacementModules(unittest.TestCase):
    """Rigorous end-to-end tests for all 6 Placement Preparation modules."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="phase5_tests_"))

        # Create a sample student resume PDF fixture
        cls.resume_pdf = cls.test_dir / "student_sample_resume.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        resume_text = (
            "ARJUN SHARMA\n"
            "Email: arjun.sharma.dev@gmail.com | Phone: 9876543210\n"
            "GitHub: github.com/arjun-dev | LinkedIn: linkedin.com/in/arjun-sharma\n\n"
            "EDUCATION:\n"
            "Bachelor of Technology in Computer Science (B.Tech)\n"
            "Graduation Year: 2024 | CGPA: 8.8\n\n"
            "TECHNICAL SKILLS:\n"
            "Languages: Python, Java, SQL, C++\n"
            "Frameworks: FastAPI, React, Node.js\n"
            "Databases: MongoDB, PostgreSQL\n"
            "Developer Tools: Git, Docker, Linux\n\n"
            "PROJECTS:\n"
            "1. E-Commerce Microservices Platform\n"
            "Engineered distributed backend using FastAPI and PostgreSQL handling 500+ requests/sec.\n"
            "Containerized services with Docker and achieved 99.8% uptime.\n\n"
            "2. AI Document Assistant System\n"
            "Built semantic search engine using Python, MongoDB, and vector embeddings.\n"
            "Optimized query response latency by 45%.\n"
        )
        page.insert_text((50, 72), resume_text)
        doc.save(str(cls.resume_pdf))
        doc.close()

    # -------------------------------------------------------------
    # Module 1 Tests: Technical Interview Preparation
    # -------------------------------------------------------------
    def test_module1_topics_and_generation(self):
        # 1. Test topic listing
        resp = self.client.get("/technical/topics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("topics", data)
        self.assertIn("Java", data["topics"])
        self.assertIn("DSA", data["topics"])
        self.assertIn("AI and ML", data["topics"])

        # 2. Test technical question generation
        payload = {
            "topic": "Java",
            "difficulty": "medium",
            "include_code": True,
        }
        gen_resp = self.client.post("/technical/generate", json=payload)
        self.assertEqual(gen_resp.status_code, 200)
        q_data = gen_resp.json()
        self.assertEqual(q_data["topic"], "Java")
        self.assertTrue(len(q_data["question"]) > 10)
        self.assertTrue(len(q_data["answer"]) > 10)
        self.assertTrue(len(q_data["explanation"]) > 10)
        self.assertIsNotNone(q_data.get("code_example"))
        self.assertTrue(len(q_data.get("follow_up_questions", [])) >= 1)

        # 3. Test saving technical question
        save_payload = {
            "question_id": q_data["question_id"],
            "topic": q_data["topic"],
            "difficulty": q_data["difficulty"],
            "question": q_data["question"],
            "answer": q_data["answer"],
            "explanation": q_data["explanation"],
            "code_example": q_data.get("code_example"),
            "follow_up_questions": q_data.get("follow_up_questions", []),
            "notes": "Important Java GC review question",
        }
        save_resp = self.client.post("/technical/save", json=save_payload)
        self.assertEqual(save_resp.status_code, 200)

        # 4. Test listing saved questions
        list_resp = self.client.get("/technical/saved?topic=Java")
        self.assertEqual(list_resp.status_code, 200)
        saved_list = list_resp.json()
        self.assertTrue(any(q["question_id"] == q_data["question_id"] for q in saved_list["questions"]))

        # 5. Test deleting saved question
        del_resp = self.client.delete(f"/technical/saved/{q_data['question_id']}")
        self.assertEqual(del_resp.status_code, 200)

    # -------------------------------------------------------------
    # Module 2 Tests: HR Preparation
    # -------------------------------------------------------------
    def test_module2_hr_guidance_no_hallucination(self):
        # 1. Test category listing
        resp = self.client.get("/hr/categories")
        self.assertEqual(resp.status_code, 200)
        cats = resp.json()["categories"]
        cat_ids = [c["id"] for c in cats]
        self.assertIn("self_introduction", cat_ids)
        self.assertIn("why_hire_you", cat_ids)

        # 2. Test generating guidance with explicit background
        real_bg = "Final year CS student with projects in FastAPI and MongoDB, 8.8 CGPA"
        payload = {
            "category": "why_hire_you",
            "target_company": "Acme Tech",
            "target_role": "Backend Engineer",
            "student_background": real_bg,
        }
        res = self.client.post("/hr/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["category"], "why_hire_you")
        self.assertTrue(len(data["draft_answer"]) > 20)
        self.assertTrue(len(data["dos_and_donts"]) >= 2)
        self.assertTrue(len(data["sample_structure"]) >= 2)

        # 3. Test saving HR draft
        draft_payload = {
            "draft_id": data["draft_id"],
            "category": data["category"],
            "question": data["question"],
            "draft_answer": data["draft_answer"],
            "target_company": "Acme Tech",
            "user_notes": "Emphasize FastAPI scalability",
        }
        save_resp = self.client.post("/hr/save", json=draft_payload)
        self.assertEqual(save_resp.status_code, 200)

        # 4. Test listing drafts
        list_resp = self.client.get("/hr/saved")
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(any(d["draft_id"] == data["draft_id"] for d in list_resp.json()["drafts"]))

        # 5. Delete draft
        del_resp = self.client.delete(f"/hr/saved/{data['draft_id']}")
        self.assertEqual(del_resp.status_code, 200)

    # -------------------------------------------------------------
    # Module 3 Tests: Aptitude Practice
    # -------------------------------------------------------------
    def test_module3_aptitude_quiz_evaluation(self):
        # 1. Generate quiz with 3 questions
        gen_resp = self.client.post(
            "/aptitude/quiz/generate",
            json={"category": "all", "count": 3, "difficulty": "medium"},
        )
        self.assertEqual(gen_resp.status_code, 200)
        quiz = gen_resp.json()
        self.assertEqual(len(quiz["questions"]), 3)
        for q in quiz["questions"]:
            self.assertEqual(len(q["options"]), 4)
            # Ensure correct option is NOT leaked in client quiz response
            self.assertNotIn("correct_option", q)

        # 2. Submit quiz answers
        answers_payload = [
            {"question_id": "quant_01", "selected_option": "A"},  # Correct (5%)
            {"question_id": "logic_01", "selected_option": "B"},  # Correct (224)
            {"question_id": "verb_01", "selected_option": "D"},   # Incorrect
        ]
        sub_resp = self.client.post(
            "/aptitude/quiz/submit",
            json={
                "category": "all",
                "answers": answers_payload,
                "time_taken_seconds": 145,
            },
        )
        self.assertEqual(sub_resp.status_code, 200)
        result = sub_resp.json()
        self.assertEqual(result["total_questions"], 3)
        self.assertEqual(result["correct_count"], 2)
        self.assertEqual(result["wrong_count"], 1)
        self.assertEqual(result["time_taken_seconds"], 145)
        self.assertAlmostEqual(result["score_percentage"], 66.67, delta=0.5)

        # Verify step-by-step explanations are present
        for res_item in result["results"]:
            self.assertTrue(len(res_item["explanation"]) > 10)

        # 3. Check history endpoint
        hist_resp = self.client.get("/aptitude/history")
        self.assertEqual(hist_resp.status_code, 200)
        self.assertTrue(hist_resp.json()["total_attempts"] >= 1)

    # -------------------------------------------------------------
    # Module 4 Tests: Resume Analyser
    # -------------------------------------------------------------
    def test_module4_resume_analysis(self):
        with open(self.resume_pdf, "rb") as f:
            resp = self.client.post(
                "/resume/analyze",
                files={"file": ("student_sample_resume.pdf", f, "application/pdf")},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Contact Info extraction
        contact = data["contact_info"]
        self.assertEqual(contact["email"], "arjun.sharma.dev@gmail.com")
        self.assertIn("9876543210", contact["phone"])
        self.assertIn("github.com/arjun-dev", contact["github"])
        self.assertIn("linkedin.com/in/arjun-sharma", contact["linkedin"])

        # Skill extraction
        skills = data["skills"]["all_skills"]
        self.assertIn("Python", skills)
        self.assertIn("Java", skills)
        self.assertIn("FastAPI", skills)
        self.assertIn("Docker", skills)
        self.assertIn("MongoDB", skills)

        # Health audit
        self.assertTrue(len(data["strengths"]) >= 2)
        self.assertTrue(len(data["improvement_suggestions"]) >= 1)

        # Retrieve resume by ID
        resume_id = data["resume_id"]
        get_resp = self.client.get(f"/resume/{resume_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["resume_id"], resume_id)

    # -------------------------------------------------------------
    # Module 5 Tests: Job Description Analyser
    # -------------------------------------------------------------
    def test_module5_jd_analysis_and_matching(self):
        sample_jd = (
            "We are hiring a Backend Engineer at Global Cloud Tech!\n\n"
            "Responsibilities:\n"
            "• Design and develop scalable REST APIs and microservices.\n"
            "• Optimize database query performance and manage schemas.\n"
            "• Collaborate with frontend developers on API contracts.\n\n"
            "Requirements:\n"
            "• Solid proficiency in Python and FastAPI.\n"
            "• Experience with SQL and relational databases like PostgreSQL.\n"
            "• Familiarity with Docker containerization.\n\n"
            "Preferred Qualifications:\n"
            "• Experience with Redis caching and Apache Kafka.\n"
            "• Knowledge of AWS and Kubernetes.\n"
        )

        candidate_skills = ["Python", "FastAPI", "SQL", "Docker", "Git"]

        resp = self.client.post(
            "/jd/analyze",
            json={
                "jd_text": sample_jd,
                "role_title": "Backend Engineer",
                "company_name": "Global Cloud Tech",
                "candidate_skills": candidate_skills,
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["role_title"], "Backend Engineer")
        self.assertEqual(data["company_name"], "Global Cloud Tech")
        self.assertIn("Python", data["required_skills"])
        self.assertIn("FastAPI", data["required_skills"])

        # Skill match verification
        match = data["skill_match"]
        self.assertIsNotNone(match)
        self.assertIn("Python", match["matched_required_skills"])
        self.assertIn("FastAPI", match["matched_required_skills"])
        self.assertTrue(match["overall_match_score"] > 0)
        self.assertTrue("Score =" in match["score_formula"])

        # Missing skills & recommendations
        self.assertTrue(len(data["recommended_learning_topics"]) >= 1)
        self.assertTrue(len(data["preparation_action_plan"]) >= 2)

        # Match history check
        hist_resp = self.client.get("/jd/history")
        self.assertEqual(hist_resp.status_code, 200)
        self.assertTrue(hist_resp.json()["total"] >= 1)

    # -------------------------------------------------------------
    # Module 6 Tests: Mock Interview
    # -------------------------------------------------------------
    def test_module6_mock_interview_flow(self):
        # 1. Start session
        start_payload = {
            "interview_type": "technical",
            "topic": "Java",
            "difficulty": "medium",
            "total_questions": 2,
        }
        start_resp = self.client.post("/mock-interview/start", json=start_payload)
        self.assertEqual(start_resp.status_code, 200)
        session = start_resp.json()
        session_id = session["session_id"]
        self.assertEqual(session["status"], "in_progress")
        self.assertEqual(session["current_question_number"], 1)
        self.assertTrue(len(session["question"]) > 10)

        # 2. Answer Question 1
        ans1_resp = self.client.post(
            f"/mock-interview/{session_id}/answer",
            json={
                "student_answer": (
                    "In Java, inheritance allows a subclass to inherit fields and methods from a superclass using extends. "
                    "It promotes code reusability and polymorphism. Method overriding occurs with @Override."
                )
            },
        )
        self.assertEqual(ans1_resp.status_code, 200)
        ans1_data = ans1_resp.json()
        self.assertEqual(ans1_data["turn_number"], 1)
        self.assertFalse(ans1_data["is_completed"])
        self.assertIsNotNone(ans1_data["next_question"])

        # Verify 5 evaluation criteria
        scores = ans1_data["scores"]
        self.assertTrue(1 <= scores["correctness"] <= 10)
        self.assertTrue(1 <= scores["relevance"] <= 10)
        self.assertTrue(1 <= scores["completeness"] <= 10)
        self.assertTrue(1 <= scores["clarity"] <= 10)
        self.assertTrue(1 <= scores["communication"] <= 10)
        self.assertTrue(1.0 <= scores["overall_score"] <= 10.0)

        self.assertTrue(len(ans1_data["feedback"]) > 10)
        self.assertTrue(len(ans1_data["improved_answer"]) > 10)

        # 3. Answer Question 2 (completes session)
        ans2_resp = self.client.post(
            f"/mock-interview/{session_id}/answer",
            json={
                "student_answer": (
                    "Interfaces provide pure abstraction and allow multiple inheritance of type using implements. "
                    "Abstract classes can have state and implemented methods."
                )
            },
        )
        self.assertEqual(ans2_resp.status_code, 200)
        ans2_data = ans2_resp.json()
        self.assertTrue(ans2_data["is_completed"])
        self.assertIsNotNone(ans2_data["final_summary"])
        self.assertTrue(ans2_data["final_summary"]["average_score"] > 0)

        # 4. Get full interview transcript
        detail_resp = self.client.get(f"/mock-interview/{session_id}")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()
        self.assertEqual(detail["status"], "completed")
        self.assertEqual(len(detail["turns"]), 2)

        # 5. Check interview history
        hist_resp = self.client.get("/mock-interviews/history")
        self.assertEqual(hist_resp.status_code, 200)
        self.assertTrue(any(s["session_id"] == session_id for s in hist_resp.json()["sessions"]))


if __name__ == "__main__":
    unittest.main()
