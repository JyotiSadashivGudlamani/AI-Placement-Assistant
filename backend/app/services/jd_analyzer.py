"""
Service for Module 5: Job Description Analyser.
Parses job postings, extracts required/preferred skills and key responsibilities,
computes a mathematically transparent skill-match score against a candidate's resume,
identifies missing skills, and formulates targeted learning paths.
"""

from uuid import uuid4
from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Set
import httpx

from backend.app.core.config import settings
from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.jd import JDAnalysisResponse, SkillMatchDetails
from backend.app.services.resume_analyzer import KNOWN_DATABASES, KNOWN_FRAMEWORKS, KNOWN_LANGUAGES, KNOWN_TOOLS


TECH_DICTIONARY: Dict[str, str] = {
    # Standardize casing
    "python": "Python", "java": "Java", "c": "C", "c++": "C++", "cpp": "C++", "c#": "C#",
    "javascript": "JavaScript", "typescript": "TypeScript", "sql": "SQL", "golang": "Go", "go": "Go",
    "react": "React", "react.js": "React", "reactjs": "React", "angular": "Angular",
    "vue": "Vue.js", "node.js": "Node.js", "nodejs": "Node.js", "express": "Express.js",
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask", "spring boot": "Spring Boot",
    "spring": "Spring Boot", "mongodb": "MongoDB", "mysql": "MySQL", "postgresql": "PostgreSQL",
    "redis": "Redis", "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS",
    "git": "Git", "linux": "Linux", "rest api": "REST APIs", "restful": "REST APIs",
    "microservices": "Microservices", "graphql": "GraphQL", "kafka": "Apache Kafka",
    "dsa": "Data Structures & Algorithms", "oop": "Object-Oriented Programming",
    "ci/cd": "CI/CD Pipelines", "system design": "System Design"
}


class JDAnalyzerService:
    """Analyzes Job Descriptions and computes deterministic ATS skill-match scores."""

    _instance: Optional["JDAnalyzerService"] = None

    def __init__(self):
        self.mongo = MongoDBManager.get_instance()

    @classmethod
    def get_instance(cls) -> "JDAnalyzerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------
    # Skill Extraction Helpers
    # -------------------------------------------------------------
    @staticmethod
    def extract_skills_from_text(text: str) -> List[str]:
        """Extracts technical skills found in text matching known engineering terms."""
        lower = text.lower()
        found = set()

        for term, standard_name in TECH_DICTIONARY.items():
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, lower):
                found.add(standard_name)

        return sorted(list(found))

    @staticmethod
    def split_jd_sections(text: str) -> tuple[str, str, str]:
        """Heuristically splits JD into (responsibilities, required_skills, preferred_skills)."""
        lines = text.split("\n")
        current_section = "general"
        resp_lines = []
        req_lines = []
        pref_lines = []

        for line in lines:
            l_lower = line.strip().lower()
            if any(kw in l_lower for kw in ["preferred", "nice to have", "good to have", "plus", "bonus"]):
                current_section = "preferred"
                continue
            elif any(kw in l_lower for kw in ["requirement", "qualification", "must have", "basic qualification", "skills required"]):
                current_section = "required"
                continue
            elif any(kw in l_lower for kw in ["responsibilit", "duties", "what you will do", "what you'll do", "the role"]):
                current_section = "responsibilities"
                continue

            if current_section == "preferred":
                pref_lines.append(line)
            elif current_section == "required":
                req_lines.append(line)
            elif current_section == "responsibilities":
                resp_lines.append(line)
            else:
                req_lines.append(line)

        return "\n".join(resp_lines), "\n".join(req_lines), "\n".join(pref_lines)

    # -------------------------------------------------------------
    # Transparent Match Calculation
    # -------------------------------------------------------------
    @staticmethod
    def calculate_transparent_match(
        required_skills: List[str],
        preferred_skills: List[str],
        candidate_skills: List[str],
    ) -> SkillMatchDetails:
        """
        Computes mathematically transparent match score:
        Formula:
          If Preferred Skills exist:
            Overall = 70% * (Matched Required / Total Required) + 30% * (Matched Preferred / Total Preferred)
          If No Preferred Skills:
            Overall = 100% * (Matched Required / Total Required)
        """
        cand_set = {s.lower() for s in candidate_skills}

        matched_req = [s for s in required_skills if s.lower() in cand_set]
        missing_req = [s for s in required_skills if s.lower() not in cand_set]

        matched_pref = [s for s in preferred_skills if s.lower() in cand_set]
        missing_pref = [s for s in preferred_skills if s.lower() not in cand_set]

        total_req = len(required_skills)
        total_pref = len(preferred_skills)

        req_pct = (len(matched_req) / total_req * 100) if total_req > 0 else 100.0
        pref_pct = (len(matched_pref) / total_pref * 100) if total_pref > 0 else 100.0

        if total_pref > 0:
            overall = round(0.70 * req_pct + 0.30 * pref_pct, 1)
            formula_str = (
                f"Score = 70% * (Required: {len(matched_req)}/{total_req}) + "
                f"30% * (Preferred: {len(matched_pref)}/{total_pref}) = {overall}%"
            )
        else:
            overall = round(req_pct, 1)
            formula_str = f"Score = 100% * (Required: {len(matched_req)}/{total_req}) = {overall}%"

        return SkillMatchDetails(
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            required_match_percentage=round(req_pct, 1),
            preferred_match_percentage=round(pref_pct, 1),
            overall_match_score=overall,
            score_formula=formula_str,
        )

    # -------------------------------------------------------------
    # Main Analysis Execution
    # -------------------------------------------------------------
    async def analyze_job_description(
        self,
        jd_text: str,
        role_title: Optional[str] = None,
        company_name: Optional[str] = None,
        resume_id: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyzes JD and optionally calculates skill-match against resume."""
        clean_text = jd_text.strip()
        resp_text, req_text, pref_text = self.split_jd_sections(clean_text)

        # 1. Skill Extraction
        required_skills = self.extract_skills_from_text(req_text or clean_text)
        preferred_skills = self.extract_skills_from_text(pref_text) if pref_text else []

        # Ensure no overlap
        preferred_skills = [s for s in preferred_skills if s not in required_skills]

        # Fallback if specific sections were ambiguous
        if not required_skills and not preferred_skills:
            all_skills = self.extract_skills_from_text(clean_text)
            required_skills = all_skills[:max(len(all_skills) - 2, 1)]
            preferred_skills = all_skills[max(len(all_skills) - 2, 1):]

        # 2. Extract Responsibilities
        responsibilities = []
        bullet_matches = re.findall(r"^[•\-*]\s*(.+)$", clean_text, re.MULTILINE)
        if bullet_matches:
            responsibilities = [b.strip() for b in bullet_matches[:6]]
        else:
            sentences = [s.strip() for s in clean_text.split(".") if len(s.strip()) > 30]
            responsibilities = sentences[:4]

        # 3. Retrieve Candidate Skills if Resume ID provided
        cand_skills: List[str] = list(candidate_skills) if candidate_skills else []
        if resume_id:
            resume_profile = self.mongo.get_resume_profile(resume_id)
            if resume_profile:
                profile_skills = resume_profile.get("skills", {}).get("all_skills", [])
                cand_skills = list(set(cand_skills + profile_skills))

        # 4. Compute Match Details if candidate skills available
        match_details: Optional[SkillMatchDetails] = None
        recommended_topics: List[str] = []
        action_plan: List[str] = []

        if cand_skills or resume_id:
            match_details = self.calculate_transparent_match(
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                candidate_skills=cand_skills,
            )

            # Generate Recommended Learning Topics for missing required skills
            for missing in match_details.missing_required_skills:
                recommended_topics.append(f"Master core concepts and practical projects in {missing}.")

            for missing in match_details.missing_preferred_skills[:3]:
                recommended_topics.append(f"Familiarize with {missing} architecture & syntax.")

            action_plan = [
                f"Prioritize building a small hands-on feature or mini-project utilizing {match_details.missing_required_skills[0]}."
                if match_details.missing_required_skills else "Review system design and scalability questions for this role.",
                "Prepare 2 STAR-method stories emphasizing experiences with " + ", ".join(match_details.matched_required_skills[:3]),
                "Align your resume summary to explicitly highlight required keywords: " + ", ".join(match_details.matched_required_skills[:4]),
            ]
        else:
            # General recommendations when no resume is attached
            recommended_topics = [f"Deep dive into {s} fundamentals and interview patterns" for s in required_skills[:4]]
            action_plan = [
                "Map your existing college projects against the required technical stack.",
                "Prepare for technical coding rounds covering data structures and problem-solving.",
                "Review the listed responsibilities to prepare contextual behavioral examples."
            ]

        match_id = f"jd_{uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_role = role_title or "Software Development Engineer"

        result = {
            "match_id": match_id,
            "role_title": resolved_role,
            "company_name": company_name,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "key_responsibilities": responsibilities,
            "skill_match": match_details.model_dump() if match_details else None,
            "recommended_learning_topics": recommended_topics,
            "preparation_action_plan": action_plan,
            "created_at": now_iso,
        }

        # Persist to MongoDB
        self.mongo.save_jd_match(result)
        return result

    def get_match_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent JD match histories."""
        return self.mongo.list_jd_matches(limit=limit)
