"""
Service for Module 3: Aptitude Practice.
Provides multiple-choice questions (MCQs), instant answer validation,
step-by-step explanations, score calculation, time tracking, and attempt persistence.
"""

from uuid import uuid4
from datetime import datetime, timezone
import random
from typing import Any, Dict, List, Optional

from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.aptitude import (
    APTITUDE_CATEGORIES,
    APTITUDE_CATEGORY_LABELS,
    AptitudeClientQuestion,
    MCQOption,
    QuestionResultItem,
    QuizResultResponse,
)


APTITUDE_QUESTION_BANK: List[Dict[str, Any]] = [
    # ------------------ Quantitative Aptitude ------------------
    {
        "question_id": "quant_01",
        "category": "quantitative",
        "subtopic": "Percentages & Profit",
        "difficulty": "easy",
        "question_text": "A shopkeeper marks an article 40% above the cost price and allows a discount of 25% on the marked price. What is the net profit percentage?",
        "options": [
            {"key": "A", "text": "5%"},
            {"key": "B", "text": "10%"},
            {"key": "C", "text": "15%"},
            {"key": "D", "text": "20%"}
        ],
        "correct_option": "A",
        "explanation": "Let Cost Price (CP) = $100. Marked Price (MP) = 100 + 40 = $140. Discount = 25% of 140 = $35. Selling Price (SP) = 140 - 35 = $105. Net Profit = SP - CP = 105 - 100 = $5. Profit Percentage = (5 / 100) * 100% = 5%."
    },
    {
        "question_id": "quant_02",
        "category": "quantitative",
        "subtopic": "Time & Work",
        "difficulty": "medium",
        "question_text": "Worker A can complete a task in 12 days, and Worker B can complete the same task in 18 days. If they work together for 4 days, what fraction of the work remains unfinished?",
        "options": [
            {"key": "A", "text": "4/9"},
            {"key": "B", "text": "5/9"},
            {"key": "C", "text": "1/3"},
            {"key": "D", "text": "2/3"}
        ],
        "correct_option": "A",
        "explanation": "A's 1-day work = 1/12. B's 1-day work = 1/18. Combined 1-day work = (1/12 + 1/18) = (3 + 2)/36 = 5/36. Work completed in 4 days = 4 * (5/36) = 20/36 = 5/9. Remaining work = 1 - 5/9 = 4/9."
    },
    {
        "question_id": "quant_03",
        "category": "quantitative",
        "subtopic": "Speed, Time & Distance",
        "difficulty": "medium",
        "question_text": "A train 150 meters long passes an electric pole in 9 seconds. How long will it take to cross a platform 250 meters long at the same speed?",
        "options": [
            {"key": "A", "text": "18 seconds"},
            {"key": "B", "text": "24 seconds"},
            {"key": "C", "text": "20 seconds"},
            {"key": "D", "text": "15 seconds"}
        ],
        "correct_option": "B",
        "explanation": "Speed of train = Distance / Time = 150 m / 9 s = 50/3 m/s. To cross a platform, total distance = Train Length + Platform Length = 150 + 250 = 400 m. Time required = Total Distance / Speed = 400 / (50/3) = 400 * 3 / 50 = 24 seconds."
    },
    {
        "question_id": "quant_04",
        "category": "quantitative",
        "subtopic": "Probability",
        "difficulty": "hard",
        "question_text": "Two fair six-sided dice are rolled simultaneously. What is the probability that the sum of the numbers appearing on the dice is a prime number?",
        "options": [
            {"key": "A", "text": "5/12"},
            {"key": "B", "text": "7/18"},
            {"key": "C", "text": "1/2"},
            {"key": "D", "text": "13/36"}
        ],
        "correct_option": "A",
        "explanation": "Total possible outcomes = 6 * 6 = 36. Prime sums possible between 2 and 12 are {2, 3, 5, 7, 11}.\n- Sum = 2: (1,1) -> 1 pair\n- Sum = 3: (1,2), (2,1) -> 2 pairs\n- Sum = 5: (1,4), (2,3), (3,2), (4,1) -> 4 pairs\n- Sum = 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) -> 6 pairs\n- Sum = 11: (5,6), (6,5) -> 2 pairs\nTotal favorable outcomes = 1 + 2 + 4 + 6 + 2 = 15. Probability = 15 / 36 = 5 / 12."
    },

    # ------------------ Logical Reasoning ------------------
    {
        "question_id": "logic_01",
        "category": "logical",
        "subtopic": "Number & Letter Series",
        "difficulty": "easy",
        "question_text": "Find the next term in the sequence: 7, 14, 28, 56, 112, ?",
        "options": [
            {"key": "A", "text": "168"},
            {"key": "B", "text": "224"},
            {"key": "C", "text": "196"},
            {"key": "D", "text": "252"}
        ],
        "correct_option": "B",
        "explanation": "Each consecutive number is multiplied by 2 (geometric progression with common ratio r = 2): 7*2=14, 14*2=28, 28*2=56, 56*2=112, 112*2 = 224."
    },
    {
        "question_id": "logic_02",
        "category": "logical",
        "subtopic": "Blood Relations",
        "difficulty": "medium",
        "question_text": "Pointing to a photograph of a woman, Rahul said: 'She is the mother of the only daughter of my paternal grandfather's only son.' How is the woman related to Rahul?",
        "options": [
            {"key": "A", "text": "Sister"},
            {"key": "B", "text": "Aunt"},
            {"key": "C", "text": "Mother"},
            {"key": "D", "text": "Daughter"}
        ],
        "correct_option": "C",
        "explanation": "Step 1: 'My paternal grandfather's only son' refers to Rahul's father.\nStep 2: 'The only daughter of Rahul's father' refers to Rahul's sister.\nStep 3: 'The mother of Rahul's sister' is Rahul's mother.\nTherefore, the woman is Rahul's mother."
    },
    {
        "question_id": "logic_03",
        "category": "logical",
        "subtopic": "Syllogisms",
        "difficulty": "medium",
        "question_text": "Statements:\n1. All engineers are innovators.\n2. Some innovators are leaders.\nConclusions:\nI. Some engineers are leaders.\nII. All innovators are engineers.",
        "options": [
            {"key": "A", "text": "Only conclusion I follows"},
            {"key": "B", "text": "Only conclusion II follows"},
            {"key": "C", "text": "Neither I nor II follows"},
            {"key": "D", "text": "Both I and II follow"}
        ],
        "correct_option": "C",
        "explanation": "From 'All engineers are innovators' and 'Some innovators are leaders', the middle term 'innovators' is undistributed in both premises. Hence, no definite relation can be established between engineers and leaders. Neither Conclusion I nor Conclusion II follows."
    },
    {
        "question_id": "logic_04",
        "category": "logical",
        "subtopic": "Direction Sense",
        "difficulty": "easy",
        "question_text": "A person walks 10 km North, turns right and walks 6 km, then turns right again and walks 10 km. How far and in what direction is the person from the starting point?",
        "options": [
            {"key": "A", "text": "6 km East"},
            {"key": "B", "text": "6 km West"},
            {"key": "C", "text": "10 km North"},
            {"key": "D", "text": "16 km East"}
        ],
        "correct_option": "A",
        "explanation": "Walking 10 km North (+y direction) and later 10 km South (-y direction) cancels the vertical displacement (10 - 10 = 0). The horizontal movement was 6 km East (+x direction). Thus, the person is 6 km East of the starting point."
    },

    # ------------------ Verbal Ability ------------------
    {
        "question_id": "verb_01",
        "category": "verbal",
        "subtopic": "Sentence Correction",
        "difficulty": "easy",
        "question_text": "Select the grammatically correct sentence:",
        "options": [
            {"key": "A", "text": "Neither of the two candidates have submitted their assignment on time."},
            {"key": "B", "text": "Neither of the two candidates has submitted his or her assignment on time."},
            {"key": "C", "text": "Neither of the two candidates are submitted their assignment on time."},
            {"key": "D", "text": "Neither of the two candidates have been submitted his assignment on time."}
        ],
        "correct_option": "B",
        "explanation": "'Neither' is a singular indefinite pronoun when referring to two entities, so it requires a singular verb ('has submitted', not 'have submitted') and singular pronoun agreement ('his or her')."
    },
    {
        "question_id": "verb_02",
        "category": "verbal",
        "subtopic": "Vocabulary & Antonyms",
        "difficulty": "medium",
        "question_text": "Choose the word that is most nearly OPPOSITE in meaning to 'METICULOUS':",
        "options": [
            {"key": "A", "text": "Fastidious"},
            {"key": "B", "text": "Careless"},
            {"key": "C", "text": "Scrupulous"},
            {"key": "D", "text": "Diligent"}
        ],
        "correct_option": "B",
        "explanation": "'Meticulous' means showing great attention to detail; very careful and precise. Fastidious, scrupulous, and diligent are synonyms. 'Careless' is the direct antonym."
    },
    {
        "question_id": "verb_03",
        "category": "verbal",
        "subtopic": "Para Jumbles",
        "difficulty": "medium",
        "question_text": "Rearrange the sentences into a coherent paragraph:\nP: This transition requires significant investment in renewable infrastructure.\nQ: Global energy consumption is shifting rapidly away from fossil fuels.\nR: Governments worldwide are offering policy incentives to accelerate this change.\nS: However, the long-term environmental benefits far outweigh the upfront capital costs.",
        "options": [
            {"key": "A", "text": "Q -> P -> S -> R"},
            {"key": "B", "text": "P -> Q -> R -> S"},
            {"key": "C", "text": "Q -> P -> R -> S"},
            {"key": "D", "text": "R -> Q -> P -> S"}
        ],
        "correct_option": "C",
        "explanation": "Q introduces the main topic (global shift from fossil fuels). P connects logically to 'this transition' and mentions the need for investment. R adds how governments are incentivizing the change. S provides the concluding contrast ('However, the long-term benefits...'). The proper flow is Q -> P -> R -> S."
    }
]


class AptitudeService:
    """Manages question generation, quiz submission, scoring, and history."""

    _instance: Optional["AptitudeService"] = None

    def __init__(self):
        self.mongo = MongoDBManager.get_instance()
        self.question_map = {q["question_id"]: q for q in APTITUDE_QUESTION_BANK}

    @classmethod
    def get_instance(cls) -> "AptitudeService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_quiz(
        self,
        category: str = "all",
        difficulty: str = "medium",
        count: int = 5,
    ) -> Dict[str, Any]:
        """Generates a random practice quiz from the verified question bank."""
        norm_cat = category.lower()
        if norm_cat != "all" and norm_cat in APTITUDE_CATEGORIES:
            eligible = [q for q in APTITUDE_QUESTION_BANK if q["category"] == norm_cat]
        else:
            eligible = list(APTITUDE_QUESTION_BANK)

        # Shuffle and select requested count
        selected = random.sample(eligible, min(count, len(eligible)))

        client_questions = [
            AptitudeClientQuestion(
                question_id=q["question_id"],
                category=q["category"],
                subtopic=q["subtopic"],
                difficulty=q["difficulty"],
                question_text=q["question_text"],
                options=[MCQOption(**opt) for opt in q["options"]],
            )
            for q in selected
        ]

        quiz_id = f"quiz_{uuid4().hex[:12]}"
        return {
            "quiz_id": quiz_id,
            "category": norm_cat,
            "category_label": APTITUDE_CATEGORY_LABELS.get(norm_cat, norm_cat),
            "difficulty": difficulty,
            "total_questions": len(client_questions),
            "questions": client_questions,
        }

    def evaluate_quiz(
        self,
        category: str,
        answers: List[Dict[str, Any]],
        time_taken_seconds: int,
    ) -> QuizResultResponse:
        """
        Evaluates submitted student answers against ground truth.
        Computes score, percentage, elapsed time, and persists attempt.
        """
        results: List[QuestionResultItem] = []
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0

        for ans in answers:
            qid = ans.get("question_id")
            selected = ans.get("selected_option")
            q_truth = self.question_map.get(qid)

            if not q_truth:
                continue

            correct_opt = q_truth["correct_option"]
            if not selected:
                unanswered_count += 1
                is_correct = False
            elif selected.strip().upper() == correct_opt.upper():
                correct_count += 1
                is_correct = True
            else:
                wrong_count += 1
                is_correct = False

            results.append(
                QuestionResultItem(
                    question_id=qid,
                    question_text=q_truth["question_text"],
                    selected_option=selected,
                    correct_option=correct_opt,
                    is_correct=is_correct,
                    explanation=q_truth["explanation"],
                )
            )

        total_q = len(results)
        score_pct = round((correct_count / total_q) * 100, 2) if total_q > 0 else 0.0
        now_iso = datetime.now(timezone.utc).isoformat()
        attempt_id = f"apt_{uuid4().hex[:12]}"

        response = QuizResultResponse(
            attempt_id=attempt_id,
            category=category,
            category_label=APTITUDE_CATEGORY_LABELS.get(category, category),
            total_questions=total_q,
            correct_count=correct_count,
            wrong_count=wrong_count,
            unanswered_count=unanswered_count,
            score_percentage=score_pct,
            time_taken_seconds=time_taken_seconds,
            results=results,
            timestamp=now_iso,
        )

        # Persist to MongoDB
        self.mongo.save_aptitude_result(response.model_dump())
        return response

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent aptitude test history."""
        return self.mongo.list_aptitude_results(limit=limit)
