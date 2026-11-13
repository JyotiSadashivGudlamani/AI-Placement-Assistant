"""
MongoDB persistence layer for document registry and conversation histories.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from backend.app.core.config import settings


class MongoDBManager:
    """Manages MongoDB connections, document registry, and conversation history."""

    _instance: Optional["MongoDBManager"] = None

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.MONGO_URI
        self.db_name = db_name or settings.MONGO_DB_NAME
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connected = False
        self.connect()

    def connect(self) -> bool:
        """Establishes connection to MongoDB with timeout."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2500)
            # Verify connectivity with ping
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]

            # Setup indexes
            self.db.documents.create_index("document_id", unique=True)
            self.db.documents.create_index("filename")
            self.db.conversations.create_index("session_id", unique=True)
            self.db.conversations.create_index("updated_at")

            # Phase 5 Indexes
            self.db.technical_questions.create_index("question_id", unique=True)
            self.db.technical_questions.create_index("topic")
            self.db.hr_drafts.create_index("draft_id", unique=True)
            self.db.aptitude_results.create_index("attempt_id", unique=True)
            self.db.aptitude_results.create_index("timestamp")
            self.db.resumes.create_index("resume_id", unique=True)
            self.db.jd_matches.create_index("match_id", unique=True)
            self.db.mock_interviews.create_index("session_id", unique=True)

            # Phase 7 User & Ownership Indexes
            self.db.users.create_index("user_id", unique=True)
            self.db.users.create_index("email", unique=True)
            self.db.documents.create_index("user_id")
            self.db.conversations.create_index("user_id")
            self.db.technical_questions.create_index("user_id")
            self.db.hr_drafts.create_index("user_id")
            self.db.aptitude_results.create_index("user_id")
            self.db.resumes.create_index("user_id")
            self.db.jd_matches.create_index("user_id")
            self.db.mock_interviews.create_index("user_id")

            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            self.client = None
            self.db = None
            return False

    @property
    def is_connected(self) -> bool:
        """Checks if MongoDB is currently available."""
        if not self._connected or self.client is None:
            return self.connect()
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            self._connected = False
            return False

    @classmethod
    def get_instance(cls) -> "MongoDBManager":
        """Singleton accessor for MongoDB manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------
    # User Management Methods (Phase 7)
    # -------------------------------------------------------------
    def create_user(
        self,
        user_id: str,
        email: str,
        full_name: str,
        hashed_password: str,
    ) -> Dict[str, Any]:
        """Creates a new student user record with securely hashed password."""
        if not self.is_connected:
            raise RuntimeError("MongoDB connection is not available.")
        user_doc = {
            "user_id": user_id,
            "email": email.strip().lower(),
            "full_name": full_name.strip(),
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
        }
        self.db.users.insert_one(user_doc)
        return {
            "user_id": user_id,
            "email": user_doc["email"],
            "full_name": user_doc["full_name"],
            "created_at": user_doc["created_at"],
            "is_active": True,
        }

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by lowercase email."""
        if not self.is_connected:
            return None
        return self.db.users.find_one({"email": email.strip().lower()}, {"_id": 0})

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by user_id."""
        if not self.is_connected:
            return None
        return self.db.users.find_one({"user_id": user_id}, {"_id": 0})

    # -------------------------------------------------------------
    # Document Registry Methods
    # -------------------------------------------------------------
    def register_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        total_pages: int,
        total_chunks: int,
        category: str = "placement",
        status: str = "ready",
        content_hash: str = "",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upserts a document record in the documents collection with user ownership."""
        if not self.is_connected:
            raise RuntimeError("MongoDB connection is not available.")

        doc_record = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "category": category,
            "status": status,
            "content_hash": content_hash,
            "user_id": user_id,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        self.db.documents.update_one(
            {"document_id": document_id},
            {"$set": doc_record},
            upsert=True,
        )
        return doc_record

    def list_documents(
        self,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists all registered documents, optionally filtered by category and user ownership."""
        if not self.is_connected:
            return []

        filter_query: Dict[str, Any] = {}
        if category:
            filter_query["category"] = category
        if user_id:
            filter_query["user_id"] = user_id

        cursor = self.db.documents.find(filter_query, {"_id": 0}).sort("uploaded_at", pymongo.DESCENDING)
        return list(cursor)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves document record by document_id."""
        if not self.is_connected:
            return None
        return self.db.documents.find_one({"document_id": document_id}, {"_id": 0})

    def get_document_owner(self, document_id: str) -> Optional[str]:
        """Retrieves the user_id that owns the document."""
        doc = self.get_document(document_id)
        return doc.get("user_id") if doc else None

    def delete_document(self, document_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes document record from registry with optional ownership check."""
        if not self.is_connected:
            return False
        query: Dict[str, Any] = {"document_id": document_id}
        if user_id:
            query["user_id"] = user_id
        result = self.db.documents.delete_one(query)
        return result.deleted_count > 0

    # -------------------------------------------------------------
    # Conversation History Methods
    # -------------------------------------------------------------
    def save_chat_turn(
        self,
        session_id: str,
        question: str,
        answer: str,
        citations: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> None:
        """Appends a user question and assistant answer turn to the conversation with user scoping."""
        if not self.is_connected:
            return

        now_str = datetime.now(timezone.utc).isoformat()
        user_msg = {
            "role": "user",
            "content": question,
            "timestamp": now_str,
        }
        assistant_msg = {
            "role": "assistant",
            "content": answer,
            "citations": citations,
            "timestamp": now_str,
        }

        set_fields: Dict[str, Any] = {
            "updated_at": now_str,
            "last_question": question,
        }
        if user_id:
            set_fields["user_id"] = user_id

        self.db.conversations.update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "session_id": session_id,
                    "created_at": now_str,
                },
                "$set": set_fields,
                "$push": {
                    "messages": {"$each": [user_msg, assistant_msg]}
                },
            },
            upsert=True,
        )

    def get_conversation(
        self,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieves full conversation session messages with optional user scoping."""
        if not self.is_connected:
            return None
        query: Dict[str, Any] = {"session_id": session_id}
        if user_id:
            query["user_id"] = user_id
        return self.db.conversations.find_one(query, {"_id": 0})

    def list_sessions(
        self,
        limit: int = 20,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists recent conversation sessions with summary metadata and optional user scoping."""
        if not self.is_connected:
            return []

        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id

        cursor = (
            self.db.conversations.find(
                query,
                {
                    "_id": 0,
                    "session_id": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "last_question": 1,
                    "user_id": 1,
                    "message_count": {"$size": "$messages"},
                },
            )
            .sort("updated_at", pymongo.DESCENDING)
            .limit(limit)
        )
        return list(cursor)

    def delete_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """Deletes a conversation session with optional user ownership check."""
        if not self.is_connected:
            return False
        query: Dict[str, Any] = {"session_id": session_id}
        if user_id:
            query["user_id"] = user_id
        res = self.db.conversations.delete_one(query)
        return res.deleted_count > 0

    # -------------------------------------------------------------
    # Module 1: Technical Questions Persistence
    # -------------------------------------------------------------
    def save_technical_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a generated or bookmarked technical question."""
        if not self.is_connected:
            return question_data
        question_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.db.technical_questions.update_one(
            {"question_id": question_data["question_id"]},
            {"$set": question_data},
            upsert=True,
        )
        return question_data

    def list_saved_technical_questions(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists saved technical interview questions."""
        if not self.is_connected:
            return []
        query = {"topic": topic} if topic else {}
        cursor = self.db.technical_questions.find(query, {"_id": 0}).sort("created_at", pymongo.DESCENDING)
        return list(cursor)

    def delete_technical_question(self, question_id: str) -> bool:
        """Removes a saved technical question."""
        if not self.is_connected:
            return False
        res = self.db.technical_questions.delete_one({"question_id": question_id})
        return res.deleted_count > 0

    # -------------------------------------------------------------
    # Module 2: HR Drafts Persistence
    # -------------------------------------------------------------
    def save_hr_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves an HR question and draft answer."""
        if not self.is_connected:
            return draft_data
        draft_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.db.hr_drafts.update_one(
            {"draft_id": draft_data["draft_id"]},
            {"$set": draft_data},
            upsert=True,
        )
        return draft_data

    def list_hr_drafts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists saved HR question drafts."""
        if not self.is_connected:
            return []
        query = {"category": category} if category else {}
        cursor = self.db.hr_drafts.find(query, {"_id": 0}).sort("created_at", pymongo.DESCENDING)
        return list(cursor)

    def delete_hr_draft(self, draft_id: str) -> bool:
        """Deletes a saved HR draft."""
        if not self.is_connected:
            return False
        res = self.db.hr_drafts.delete_one({"draft_id": draft_id})
        return res.deleted_count > 0

    # -------------------------------------------------------------
    # Module 3: Aptitude Practice Persistence
    # -------------------------------------------------------------
    def save_aptitude_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves an aptitude test attempt result."""
        if not self.is_connected:
            return result_data
        result_data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.db.aptitude_results.update_one(
            {"attempt_id": result_data["attempt_id"]},
            {"$set": result_data},
            upsert=True,
        )
        return result_data

    def list_aptitude_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists recent aptitude test results."""
        if not self.is_connected:
            return []
        cursor = self.db.aptitude_results.find({}, {"_id": 0}).sort("timestamp", pymongo.DESCENDING).limit(limit)
        return list(cursor)

    # -------------------------------------------------------------
    # Module 4: Resume Profiles Persistence
    # -------------------------------------------------------------
    def save_resume_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Saves analyzed resume profile and extracted details."""
        if not self.is_connected:
            return profile
        profile.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())
        self.db.resumes.update_one(
            {"resume_id": profile["resume_id"]},
            {"$set": profile},
            upsert=True,
        )
        return profile

    def get_resume_profile(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves resume profile by ID."""
        if not self.is_connected:
            return None
        return self.db.resumes.find_one({"resume_id": resume_id}, {"_id": 0})

    def list_resumes(self) -> List[Dict[str, Any]]:
        """Lists all analyzed resumes."""
        if not self.is_connected:
            return []
        cursor = self.db.resumes.find({}, {"_id": 0}).sort("uploaded_at", pymongo.DESCENDING)
        return list(cursor)

    # -------------------------------------------------------------
    # Module 5: Job Description & Matches Persistence
    # -------------------------------------------------------------
    def save_jd_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves JD analysis and resume skill matching result."""
        if not self.is_connected:
            return match_data
        match_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.db.jd_matches.update_one(
            {"match_id": match_data["match_id"]},
            {"$set": match_data},
            upsert=True,
        )
        return match_data

    def list_jd_matches(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists recent JD matches."""
        if not self.is_connected:
            return []
        cursor = self.db.jd_matches.find({}, {"_id": 0}).sort("created_at", pymongo.DESCENDING).limit(limit)
        return list(cursor)

    # -------------------------------------------------------------
    # Module 6: Mock Interview Persistence
    # -------------------------------------------------------------
    def save_mock_interview(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a mock interview session."""
        if not self.is_connected:
            return session_data
        session_data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        self.db.mock_interviews.update_one(
            {"session_id": session_data["session_id"]},
            {"$set": session_data},
            upsert=True,
        )
        return session_data

    def get_mock_interview(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a mock interview session by ID."""
        if not self.is_connected:
            return None
        return self.db.mock_interviews.find_one({"session_id": session_id}, {"_id": 0})

    def list_mock_interviews(self, limit: int = 20, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists recent mock interview sessions with optional user scoping."""
        if not self.is_connected:
            return []
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        cursor = self.db.mock_interviews.find(query, {"_id": 0}).sort("updated_at", pymongo.DESCENDING).limit(limit)
        return list(cursor)

    # -------------------------------------------------------------
    # Phase 7: Student Preparation Analytics Engine
    # -------------------------------------------------------------
    def get_user_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregates personalized preparation metrics, scores, recent activities,
        topic-wise progress, and next learning recommendations for the student.
        """
        if not self.is_connected:
            return {
                "user_id": user_id,
                "total_uploaded_documents": 0,
                "total_questions_asked": 0,
                "technical_prep_count": 0,
                "aptitude_stats": {
                    "total_tests": 0,
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "categories": {"quantitative": 0, "logical": 0, "verbal": 0},
                },
                "mock_interview_stats": {
                    "total_interviews": 0,
                    "average_overall": 0.0,
                    "criteria_averages": {
                        "correctness": 0.0,
                        "relevance": 0.0,
                        "completeness": 0.0,
                        "clarity": 0.0,
                        "communication": 0.0,
                    },
                },
                "recent_activity": [],
                "topic_wise_progress": [],
                "recommended_next_topics": [],
            }

        user_filter: Dict[str, Any] = {"user_id": user_id} if user_id else {}

        # 1. Total uploaded documents
        total_docs = self.db.documents.count_documents(user_filter)

        # 2. Total questions asked across chat & agent sessions
        chat_sessions = list(self.db.conversations.find(user_filter, {"messages": 1, "last_question": 1, "updated_at": 1}))
        chat_q_count = sum(
            len([m for m in s.get("messages", []) if m.get("role") == "user"])
            for s in chat_sessions
        )
        agent_turns = list(self.db.agent_conversations.find(user_filter, {"turns": 1, "last_request": 1, "updated_at": 1}))
        agent_q_count = sum(len(a.get("turns", [])) for a in agent_turns)
        total_questions = chat_q_count + agent_q_count

        # 3. Technical preparation activity
        tech_qs = list(self.db.technical_questions.find(user_filter, {"topic": 1, "created_at": 1, "title": 1}))
        tech_count = len(tech_qs)

        # 4. Aptitude stats
        apt_results = list(self.db.aptitude_results.find(user_filter, {"_id": 0}))
        apt_total = len(apt_results)
        apt_avg = round(sum(r.get("score_percentage", 0) for r in apt_results) / apt_total, 1) if apt_total > 0 else 0.0
        apt_best = max([r.get("score_percentage", 0) for r in apt_results], default=0.0)

        apt_cats: Dict[str, Dict[str, Any]] = {"quantitative": {"scores": []}, "logical": {"scores": []}, "verbal": {"scores": []}}
        for r in apt_results:
            cat = r.get("category", "").lower()
            if cat in apt_cats:
                apt_cats[cat]["scores"].append(r.get("score_percentage", 0))

        apt_category_breakdown = {
            k: (round(sum(v["scores"]) / len(v["scores"]), 1) if v["scores"] else 0.0)
            for k, v in apt_cats.items()
        }

        # 5. Mock Interview stats
        mock_sessions = list(self.db.mock_interviews.find(user_filter, {"_id": 0}))
        mock_total = len(mock_sessions)
        
        mock_criteria = {"correctness": [], "relevance": [], "completeness": [], "clarity": [], "communication": [], "overall": []}
        for ms in mock_sessions:
            scores = ms.get("evaluation", {}).get("scores") or ms.get("scores") or {}
            for crit in ["correctness", "relevance", "completeness", "clarity", "communication"]:
                val = scores.get(crit)
                if isinstance(val, (int, float)):
                    mock_criteria[crit].append(val)
            ov = scores.get("overall_score") or ms.get("overall_score")
            if isinstance(ov, (int, float)):
                mock_criteria["overall"].append(ov)

        mock_avg_overall = round(sum(mock_criteria["overall"]) / len(mock_criteria["overall"]), 1) if mock_criteria["overall"] else 0.0
        criteria_averages = {
            crit: (round(sum(mock_criteria[crit]) / len(mock_criteria[crit]), 1) if mock_criteria[crit] else 0.0)
            for crit in ["correctness", "relevance", "completeness", "clarity", "communication"]
        }

        # 6. Recent activity timeline
        activity_items: List[Dict[str, Any]] = []

        # Documents
        recent_docs = self.db.documents.find(user_filter, {"_id": 0}).sort("uploaded_at", pymongo.DESCENDING).limit(5)
        for d in recent_docs:
            activity_items.append({
                "type": "document",
                "title": f"Uploaded {d.get('filename')}",
                "detail": f"{d.get('total_chunks', 0)} chunks indexed",
                "timestamp": d.get("uploaded_at", ""),
            })

        # Chats
        for cs in chat_sessions[:5]:
            if cs.get("last_question"):
                activity_items.append({
                    "type": "chat",
                    "title": f"Q&A: {cs.get('last_question')[:50]}...",
                    "detail": "RAG Document Retrieval",
                    "timestamp": cs.get("updated_at", ""),
                })

        # Aptitude
        for ar in apt_results[:5]:
            activity_items.append({
                "type": "aptitude",
                "title": f"Aptitude Test ({ar.get('category', 'all').capitalize()})",
                "detail": f"Score: {ar.get('score_percentage', 0)}% ({ar.get('correct_count', 0)}/{ar.get('total_questions', 0)} correct)",
                "timestamp": ar.get("timestamp", ""),
            })

        # Mock interviews
        for mi in mock_sessions[:5]:
            activity_items.append({
                "type": "mock_interview",
                "title": f"Mock Interview ({mi.get('topic', 'General')})",
                "detail": f"Rated {mi.get('overall_score', 0)}/10 across 5 criteria",
                "timestamp": mi.get("updated_at", ""),
            })

        # Sort activities chronologically descending
        activity_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        recent_activity = activity_items[:8]

        # 7. Topic-wise progress calculation
        topic_counts: Dict[str, int] = {}
        for t in tech_qs:
            tp = t.get("topic", "General")
            topic_counts[tp] = topic_counts.get(tp, 0) + 1

        core_topics = [
            ("Java", "Java & OOP Principles", topic_counts.get("Java", 0)),
            ("Python", "Python & Backend Systems", topic_counts.get("Python", 0)),
            ("DSA", "Data Structures & Algorithms", topic_counts.get("DSA", 0)),
            ("DBMS", "Database Management & SQL", topic_counts.get("DBMS", 0)),
            ("Operating Systems", "OS & Multithreading", topic_counts.get("Operating Systems", 0)),
            ("Computer Networks", "Networking & Protocols", topic_counts.get("Computer Networks", 0)),
        ]

        topic_wise_progress = [
            {
                "topic": t[0],
                "description": t[1],
                "practiced_count": t[2],
                "mastery_percentage": min(100, int((t[2] / 5.0) * 100)),  # 5 questions = 100% milestone
            }
            for t in core_topics
        ]

        # 8. Intelligent next topic recommendations
        recommendations: List[Dict[str, Any]] = []

        # Check resume
        resume_count = self.db.resumes.count_documents(user_filter)
        if resume_count == 0:
            recommendations.append({
                "title": "Upload and Audit Your Resume",
                "reason": "You haven't scanned your resume yet. Get ATS score and gap suggestions.",
                "action_url": "/resume",
                "badge": "Priority",
            })

        # Check least practiced technical topics
        unpracticed = [t for t in topic_wise_progress if t["practiced_count"] == 0]
        if unpracticed:
            first_un = unpracticed[0]
            recommendations.append({
                "title": f"Practice Technical {first_un['topic']}",
                "reason": f"No questions attempted yet for {first_un['description']}.",
                "action_url": "/technical",
                "badge": "Core CS",
            })

        # Check aptitude performance
        if apt_total == 0:
            recommendations.append({
                "title": "Take a Diagnostic Aptitude Quiz",
                "reason": "Test your quantitative & logical reasoning speed under time limits.",
                "action_url": "/aptitude",
                "badge": "Assessment",
            })
        elif apt_avg < 70.0:
            weakest_cat = min(apt_category_breakdown, key=apt_category_breakdown.get)
            recommendations.append({
                "title": f"Strengthen {weakest_cat.capitalize()} Aptitude",
                "reason": f"Current average is {apt_category_breakdown.get(weakest_cat, 0)}%. Target 80%+ for placement rounds.",
                "action_url": "/aptitude",
                "badge": "Improvement",
            })

        # Check mock interview
        if mock_total == 0:
            recommendations.append({
                "title": "Complete Your First Mock Interview",
                "reason": "Simulate technical answering and receive rubric feedback on 5 criteria.",
                "action_url": "/mock-interview",
                "badge": "Interview",
            })

        # Fallback recommendation if active in all areas
        if len(recommendations) < 3:
            recommendations.append({
                "title": "Job Description Skill Matching",
                "reason": "Paste a target job posting to find missing technical keywords.",
                "action_url": "/jd",
                "badge": "Placement",
            })

        return {
            "user_id": user_id,
            "total_uploaded_documents": total_docs,
            "total_questions_asked": total_questions,
            "technical_prep_count": tech_count,
            "aptitude_stats": {
                "total_tests": apt_total,
                "average_score": apt_avg,
                "best_score": apt_best,
                "categories": apt_category_breakdown,
            },
            "mock_interview_stats": {
                "total_interviews": mock_total,
                "average_overall": mock_avg_overall,
                "criteria_averages": criteria_averages,
            },
            "recent_activity": recent_activity,
            "topic_wise_progress": topic_wise_progress,
            "recommended_next_topics": recommendations[:4],
        }

