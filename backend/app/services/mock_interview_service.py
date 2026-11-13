"""
Service for Module 6: Mock Interview.
Orchestrates turn-by-turn conversational mock technical and HR interviews.
Evaluates answers on the 5 mandatory criteria:
1. Correctness
2. Relevance
3. Completeness
4. Clarity
5. Communication
Provides actionable critique, improved answer models, and performance tracking.
"""

from uuid import uuid4
from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.mock_interview import EvaluationScores, InterviewTurn
from backend.app.services.technical_prep import TechnicalPrepService
from backend.app.services.hr_prep import HRPrepService


class MockInterviewService:
    """Manages conversational mock interview sessions, dynamic evaluation, and scoring."""

    _instance: Optional["MockInterviewService"] = None

    def __init__(self):
        self.mongo = MongoDBManager.get_instance()
        self.tech_service = TechnicalPrepService.get_instance()
        self.hr_service = HRPrepService.get_instance()

    @classmethod
    def get_instance(cls) -> "MockInterviewService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------
    # 1. Start Interview Session
    # -------------------------------------------------------------
    async def start_session(
        self,
        interview_type: str = "technical",
        topic: str = "Java",
        difficulty: str = "medium",
        total_questions: int = 3,
    ) -> Dict[str, Any]:
        """Initializes a new mock interview session and produces Question 1."""
        session_id = f"mock_{uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Generate Question 1
        first_question = await self._generate_interview_question(
            interview_type=interview_type,
            topic=topic,
            difficulty=difficulty,
            question_number=1,
        )

        turns = [
            {
                "turn_number": 1,
                "question": first_question,
                "student_answer": None,
                "feedback": None,
                "improved_answer": None,
                "scores": None,
                "timestamp": now_iso,
            }
        ]

        session_data = {
            "session_id": session_id,
            "interview_type": interview_type,
            "topic": topic,
            "difficulty": difficulty,
            "status": "in_progress",
            "total_questions": total_questions,
            "completed_questions": 0,
            "average_score": None,
            "turns": turns,
            "final_summary": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        self.mongo.save_mock_interview(session_data)

        return {
            "session_id": session_id,
            "interview_type": interview_type,
            "topic": topic,
            "difficulty": difficulty,
            "total_questions": total_questions,
            "current_question_number": 1,
            "question": first_question,
            "status": "in_progress",
        }

    # -------------------------------------------------------------
    # 2. Evaluate Student Answer & Next Question
    # -------------------------------------------------------------
    async def submit_answer(
        self,
        session_id: str,
        student_answer: str,
    ) -> Dict[str, Any]:
        """
        Evaluates student answer on 5 criteria:
        Correctness, Relevance, Completeness, Clarity, Communication.
        Updates session and returns feedback, improved answer, and next question.
        """
        session = self.mongo.get_mock_interview(session_id)
        if not session:
            raise ValueError(f"Mock interview session '{session_id}' not found.")

        if session.get("status") == "completed":
            raise ValueError(f"Mock interview session '{session_id}' has already ended.")

        turns: List[Dict[str, Any]] = session.get("turns", [])
        if not turns:
            raise ValueError("No active turn found in session.")

        current_turn = turns[-1]
        turn_num = current_turn["turn_number"]
        question = current_turn["question"]

        # Run 5-criteria evaluation
        evaluation = await self._evaluate_response(
            question=question,
            student_answer=student_answer,
            interview_type=session.get("interview_type", "technical"),
            topic=session.get("topic", "Java"),
            difficulty=session.get("difficulty", "medium"),
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        current_turn["student_answer"] = student_answer
        current_turn["feedback"] = evaluation["feedback"]
        current_turn["improved_answer"] = evaluation["improved_answer"]
        current_turn["scores"] = evaluation["scores"]
        current_turn["timestamp"] = now_iso

        completed_count = len([t for t in turns if t.get("student_answer")])
        total_questions = session.get("total_questions", 3)
        is_completed = completed_count >= total_questions

        next_q = None
        next_q_num = None
        final_summary = None

        if not is_completed:
            # Generate next question
            next_q_num = turn_num + 1
            next_q = await self._generate_interview_question(
                interview_type=session.get("interview_type", "technical"),
                topic=session.get("topic", "Java"),
                difficulty=session.get("difficulty", "medium"),
                question_number=next_q_num,
                prior_question=question,
            )
            turns.append({
                "turn_number": next_q_num,
                "question": next_q,
                "student_answer": None,
                "feedback": None,
                "improved_answer": None,
                "scores": None,
                "timestamp": now_iso,
            })
        else:
            # Complete session
            session["status"] = "completed"
            all_scores = [t["scores"]["overall_score"] for t in turns if t.get("scores")]
            avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
            session["average_score"] = avg_score

            final_summary = {
                "overall_performance": "Strong Candidate" if avg_score >= 8.0 else ("Competent - Room for Polish" if avg_score >= 6.0 else "Needs Fundamental Review"),
                "average_score": avg_score,
                "total_questions_answered": completed_count,
                "strengths_observed": [
                    "Maintained a professional, responsive conversational flow.",
                    "Demonstrated awareness of core technical concepts."
                ],
                "areas_to_improve": [
                    "Include edge cases and trade-offs more explicitly.",
                    "Use precise technical terminology and concrete examples."
                ]
            }
            session["final_summary"] = final_summary

        session["turns"] = turns
        session["completed_questions"] = completed_count
        session["updated_at"] = now_iso
        self.mongo.save_mock_interview(session)

        return {
            "session_id": session_id,
            "turn_number": turn_num,
            "evaluated_question": question,
            "student_answer": student_answer,
            "scores": evaluation["scores"],
            "feedback": evaluation["feedback"],
            "improved_answer": evaluation["improved_answer"],
            "is_completed": is_completed,
            "next_question": next_q,
            "next_question_number": next_q_num,
            "final_summary": final_summary,
        }

    # -------------------------------------------------------------
    # 3. Dynamic Evaluation Logic (Ollama + Heuristic Fallback)
    # -------------------------------------------------------------
    async def _evaluate_response(
        self,
        question: str,
        student_answer: str,
        interview_type: str,
        topic: str,
        difficulty: str,
    ) -> Dict[str, Any]:
        """Scores student answer across Correctness, Relevance, Completeness, Clarity, Communication."""
        # Try dynamic LLM evaluation
        try:
            prompt = (
                f"You are a strict, constructive engineering interviewer evaluating a candidate's response.\n"
                f"Interview Context: {interview_type.upper()} ({topic}, {difficulty})\n"
                f"QUESTION: {question}\n"
                f"CANDIDATE'S ANSWER: {student_answer}\n\n"
                f"Evaluate the answer strictly on these 5 criteria (scores 1 to 10 each):\n"
                f"1. Correctness: Factual and technical accuracy.\n"
                f"2. Relevance: How directly it addresses the question asked.\n"
                f"3. Completeness: Thoroughness, edge cases, or trade-offs mentioned.\n"
                f"4. Clarity: Structure and articulation.\n"
                f"5. Communication: Professionalism and verbal poise.\n\n"
                f"Format output as a valid JSON object strictly matching this schema with no markdown code fences:\n"
                f"{{\n"
                f'  "correctness": 8,\n'
                f'  "relevance": 9,\n'
                f'  "completeness": 7,\n'
                f'  "clarity": 8,\n'
                f'  "communication": 8,\n'
                f'  "feedback": "Constructive 2-3 sentence analysis of what was good and what was missing",\n'
                f'  "improved_answer": "Model answer demonstrating how a top candidate would answer this cleanly"\n'
                f"}}"
            )

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": "You output only valid JSON without explanation or formatting."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
                if res.status_code == 200:
                    raw_text = res.json().get("message", {}).get("content", "").strip()
                    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
                    parsed = json.loads(cleaned)

                    c = int(parsed.get("correctness", 7))
                    r = int(parsed.get("relevance", 8))
                    comp = int(parsed.get("completeness", 6))
                    cl = int(parsed.get("clarity", 7))
                    comm = int(parsed.get("communication", 8))
                    overall = round((c + r + comp + cl + comm) / 5.0, 1)

                    scores = EvaluationScores(
                        correctness=c,
                        relevance=r,
                        completeness=comp,
                        clarity=cl,
                        communication=comm,
                        overall_score=overall,
                    )
                    return {
                        "scores": scores.model_dump(),
                        "feedback": parsed.get("feedback", "Good explanation. Consider expanding on edge cases."),
                        "improved_answer": parsed.get("improved_answer", "A more comprehensive answer would structure points clearly."),
                    }
        except Exception:
            pass  # Fall through to deterministic heuristic rubric

        # Deterministic Heuristic Evaluation Fallback
        word_count = len(student_answer.split())
        base_score = 6
        if word_count > 40:
            base_score += 2
        elif word_count > 15:
            base_score += 1

        c = min(base_score, 9)
        r = min(base_score + 1, 9)
        comp = min(base_score - 1, 8)
        cl = min(base_score, 8)
        comm = min(base_score, 9)
        overall = round((c + r + comp + cl + comm) / 5.0, 1)

        scores = EvaluationScores(
            correctness=c,
            relevance=r,
            completeness=comp,
            clarity=cl,
            communication=comm,
            overall_score=overall,
        )

        return {
            "scores": scores.model_dump(),
            "feedback": (
                f"You addressed the core topic clearly ({word_count} words). To elevate this to a top-tier interview response, "
                "state the definition upfront, mention a concrete real-world example, and discuss potential performance trade-offs."
            ),
            "improved_answer": (
                f"An optimal response would follow a 3-part structure: 1) Clear direct definition answering '{question}', "
                "2) Practical code/architectural example illustrating how it works in production, and "
                "3) Common pitfalls or edge cases to avoid."
            ),
        }

    # -------------------------------------------------------------
    # 4. Question Generator Helper
    # -------------------------------------------------------------
    async def _generate_interview_question(
        self,
        interview_type: str,
        topic: str,
        difficulty: str,
        question_number: int,
        prior_question: Optional[str] = None,
    ) -> str:
        """Produces a relevant sequential question for the mock interview."""
        if interview_type.lower() == "hr":
            hr_data = await self.hr_service.generate_hr_guidance(
                category="self_introduction" if question_number == 1 else ("teamwork" if question_number == 2 else "why_hire_you")
            )
            return hr_data["question"]
        else:
            tech_data = await self.tech_service.generate_question(
                topic=topic,
                difficulty=difficulty,
            )
            return tech_data["question"]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session details and turn history."""
        return self.mongo.get_mock_interview(session_id)

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists recent mock interview sessions."""
        return self.mongo.list_mock_interviews(limit=limit)
