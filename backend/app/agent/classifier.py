"""
Intent Classification and Parameter Extraction Engine for Phase 6 LangGraph Agent.
Combines deterministic pattern recognition with LLM fallback for ambiguous queries.
"""

import json
import re
from typing import Any, Dict, Optional, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.schemas.technical import TECHNICAL_TOPICS
from backend.app.schemas.hr import HR_CATEGORIES


TECHNICAL_KEYWORDS = [
    "java", "python", "c++", "c and c++", "oop", "object oriented", "dsa", "data structures",
    "algorithms", "dbms", "database", "sql", "operating systems", "os", "computer networks",
    "networking", "ai and ml", "machine learning", "deep learning", "llm and rag", "llm", "rag",
    "concurrency", "multithreading", "garbage collection", "polymorphism", "deadlock", "acid"
]

HR_KEYWORDS = [
    "self introduction", "tell me about yourself", "introduce yourself", "strengths and weaknesses",
    "career goals", "teamwork", "conflict resolution", "problem solving", "why should we hire you",
    "why hire you", "company motivation", "hr interview", "behavioral question", "star method"
]

APTITUDE_KEYWORDS = [
    "aptitude", "quantitative", "quant", "logical reasoning", "verbal ability", "math puzzle",
    "percentage", "profit and loss", "time and work", "speed and distance", "blood relations",
    "syllogism", "number series", "math problem", "aptitude quiz", "test my aptitude"
]


class IntentClassifier:
    """Classifies user intent and extracts parameters for agent tool invocation."""

    @classmethod
    async def classify(cls, user_request: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Returns:
            intent: str
            confidence: float (0.0 to 1.0)
            parameters: Dict[str, Any]
        """
        clean_text = user_request.strip()
        lower_text = clean_text.lower()

        if not clean_text or len(clean_text) < 2:
            return "invalid", 1.0, {"reason": "Request is empty."}

        # ---------------------------------------------------------
        # 1. Answer Evaluation Intent
        # ---------------------------------------------------------
        eval_patterns = [
            r"\bevaluate my answer\b",
            r"\bscore my response\b",
            r"\bgrade this answer\b",
            r"\bhow is my answer\b",
            r"\bfeedback on my answer\b",
            r"\bevaluate this response\b",
            r"\bmy answer is:\b",
        ]
        if any(re.search(pat, lower_text) for pat in eval_patterns):
            # Extract question and answer if separated by Question:/Answer:
            q_part = "Interview Question"
            a_part = clean_text

            if "question:" in lower_text and "answer:" in lower_text:
                parts = re.split(r"answer:", clean_text, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    q_part = re.sub(r"^.*?question:\s*", "", parts[0], flags=re.IGNORECASE).strip()
                    a_part = parts[1].strip()

            return "mock_interview_evaluation", 0.95, {
                "question": q_part,
                "student_answer": a_part,
                "topic": cls._extract_technical_topic(lower_text) or "General",
            }

        # ---------------------------------------------------------
        # 2. Job Description Analysis Intent
        # ---------------------------------------------------------
        jd_patterns = [
            r"\bjob description\b",
            r"\bmatch my resume\b",
            r"\banalyze this jd\b",
            r"\brequirements for this role\b",
            r"\bskill match\b",
            r"\bresponsibilities and skills\b",
            r"\bwe are hiring\b",
            r"\bqualifications:\b",
        ]
        if any(re.search(pat, lower_text) for pat in jd_patterns) or ("responsibilities" in lower_text and "requirements" in lower_text):
            return "jd_analysis", 0.92, {
                "jd_text": clean_text,
                "role_title": "Software Engineer",
            }

        # ---------------------------------------------------------
        # 3. Resume Analysis Intent
        # ---------------------------------------------------------
        resume_patterns = [
            r"\bmy resume\b",
            r"\banalyze my resume\b",
            r"\bcheck my resume\b",
            r"\bwhat skills are on my resume\b",
            r"\bmy ats score\b",
            r"\bresume strengths\b",
            r"\bmissing from my resume\b",
            r"\bextracted skills\b",
            r"\breview my resume\b",
        ]
        if any(re.search(pat, lower_text) for pat in resume_patterns):
            return "resume_analysis", 0.93, {}

        # ---------------------------------------------------------
        # 4. Aptitude Practice Intent
        # ---------------------------------------------------------
        if any(kw in lower_text for kw in APTITUDE_KEYWORDS):
            apt_cat = "all"
            if any(k in lower_text for k in ["quant", "math", "percentage", "profit", "work", "distance"]):
                apt_cat = "quantitative"
            elif any(k in lower_text for k in ["logical", "reasoning", "syllogism", "blood relation", "series"]):
                apt_cat = "logical"
            elif any(k in lower_text for k in ["verbal", "english", "grammar", "synonym"]):
                apt_cat = "verbal"

            return "aptitude", 0.90, {
                "category": apt_cat,
                "count": 2,
                "difficulty": cls._extract_difficulty(lower_text),
            }

        # ---------------------------------------------------------
        # 5. HR & Behavioral Interview Intent
        # ---------------------------------------------------------
        if any(kw in lower_text for kw in HR_KEYWORDS):
            cat = "self_introduction"
            if "strength" in lower_text or "weakness" in lower_text:
                cat = "strengths_weaknesses"
            elif "goal" in lower_text:
                cat = "career_goals"
            elif "team" in lower_text or "conflict" in lower_text:
                cat = "teamwork"
            elif "problem" in lower_text:
                cat = "problem_solving"
            elif "why should we hire you" in lower_text or "why hire you" in lower_text:
                cat = "why_hire_you"
            elif "company" in lower_text or "motivation" in lower_text:
                cat = "company_motivation"

            return "hr_prep", 0.90, {
                "category": cat,
                "target_company": None,
                "target_role": "Software Engineer",
            }

        # ---------------------------------------------------------
        # 6. Technical Interview Prep Intent
        # ---------------------------------------------------------
        detected_topic = cls._extract_technical_topic(lower_text)
        is_interview_prep_prompt = any(kw in lower_text for kw in [
            "interview question", "ask me a question", "give me a question", "technical question",
            "coding question", "practice question", "test my knowledge", "quiz me on"
        ])

        if detected_topic and (is_interview_prep_prompt or "code" in lower_text or "explain" in lower_text):
            return "technical_prep", 0.88, {
                "topic": detected_topic,
                "difficulty": cls._extract_difficulty(lower_text),
                "include_code": True,
            }

        # ---------------------------------------------------------
        # 7. Document-Based RAG Search Intent
        # ---------------------------------------------------------
        rag_patterns = [
            r"\baccording to (?:the )?(?:document|guide|notes|pdf)\b",
            r"\bin (?:the )?(?:uploaded|provided) (?:document|file|notes)\b",
            r"\bwhat does (?:the )?(?:document|pdf|guide) say\b",
            r"\bfrom (?:the )?(?:document|pdf|notes)\b",
            r"\bsearch (?:the )?(?:documents|corpus|notes)\b",
            r"\bcitation\b",
        ]
        if any(re.search(pat, lower_text) for pat in rag_patterns) or ("java" in lower_text and "inheritance" in lower_text and not is_interview_prep_prompt):
            return "rag_qa", 0.85, {
                "question": clean_text,
                "retrieval_mode": "hybrid_rerank",
                "top_k": 3,
            }

        # ---------------------------------------------------------
        # 8. Greetings & General Placement Inquiries
        # ---------------------------------------------------------
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "who are you", "what can you do", "help"]
        stripped_lower = re.sub(r"[!?,.]+$", "", lower_text).strip()
        if (
            stripped_lower in greetings
            or re.match(r"^(hi|hello|hey)\b", lower_text)
            or "what can you do" in lower_text
            or "how can you help" in lower_text
        ):
            return "general_chat", 0.95, {"message": clean_text}

        # ---------------------------------------------------------
        # 9. Check for completely Out-Of-Scope / Non-Placement queries
        # ---------------------------------------------------------
        out_of_scope_terms = [
            "recipe", "bake", "cookie", "cake", "weather", "horoscope", "astrology",
            "movie review", "cricket score", "football score", "fashion advice", "bitcoin price"
        ]
        if any(term in lower_text for term in out_of_scope_terms):
            return "invalid", 0.98, {
                "reason": "Request is outside the scope of campus placement preparation.",
            }

        # ---------------------------------------------------------
        # 10. LLM-Assisted Fallback Classification for Ambiguous Queries
        # ---------------------------------------------------------
        try:
            llm_intent, conf, params = await cls._classify_with_llm(clean_text)
            if llm_intent:
                return llm_intent, conf, params
        except Exception:
            pass

        # Default fallback to RAG / Technical QA
        if len(clean_text) > 15:
            return "rag_qa", 0.65, {"question": clean_text, "retrieval_mode": "hybrid_rerank", "top_k": 3}

        return "invalid", 0.50, {"reason": "Could not determine intent."}

    @staticmethod
    def _extract_technical_topic(text: str) -> Optional[str]:
        for t in TECHNICAL_TOPICS:
            if t.lower() in text:
                return t
        if "c++" in text or "cpp" in text:
            return "C and C++"
        if "data structure" in text or "algorithm" in text:
            return "DSA"
        if "database" in text:
            return "DBMS"
        if "network" in text:
            return "Computer Networks"
        return None

    @staticmethod
    def _extract_difficulty(text: str) -> str:
        if "hard" in text or "advanced" in text or "senior" in text:
            return "hard"
        if "easy" in text or "beginner" in text or "basic" in text:
            return "easy"
        return "medium"

    @classmethod
    async def _classify_with_llm(cls, text: str) -> Tuple[str, float, Dict[str, Any]]:
        """Invokes Ollama to classify ambiguous inputs into a valid placement tool."""
        prompt = (
            f"Classify this student request into EXACTLY ONE intent:\n"
            f"- rag_qa (querying uploaded document content or notes)\n"
            f"- resume_analysis (analyzing or reviewing student resume)\n"
            f"- jd_analysis (analyzing job descriptions and matching skills)\n"
            f"- technical_prep (technical interview question or coding problem)\n"
            f"- hr_prep (HR or behavioral question like self-introduction, STAR)\n"
            f"- aptitude (math, quant, logical reasoning, or verbal test)\n"
            f"- mock_interview_evaluation (evaluating or grading an interview answer)\n"
            f"- invalid (non-placement or nonsense request)\n\n"
            f"Student Request: \"{text}\"\n\n"
            f"Output strictly valid JSON with no markdown:\n"
            f"{{\"intent\": \"one_of_the_above\", \"confidence\": 0.85}}"
        )

        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You output only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )
            if res.status_code == 200:
                raw = res.json().get("message", {}).get("content", "").strip()
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
                data = json.loads(cleaned)
                intent = data.get("intent", "invalid")
                conf = float(data.get("confidence", 0.7))
                return intent, conf, {}

        return "invalid", 0.0, {}
