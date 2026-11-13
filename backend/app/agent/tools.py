"""
Modular tools for LangGraph Agent.
Wraps existing Phase 1–5 backend services without duplicating business logic.
Provides strict error handling, structured parameter extraction, and session scoping.
"""

from typing import Any, Dict, List, Optional

from backend.app.services.advanced_rag import AdvancedRAGService
from backend.app.services.llm import LLMService
from backend.app.services.resume_analyzer import ResumeAnalyzerService
from backend.app.services.jd_analyzer import JDAnalyzerService
from backend.app.services.technical_prep import TechnicalPrepService
from backend.app.services.hr_prep import HRPrepService
from backend.app.services.aptitude_service import AptitudeService
from backend.app.services.mock_interview_service import MockInterviewService
from backend.app.db.mongo import MongoDBManager


# -------------------------------------------------------------
# Tool 1: Document-Based RAG Question Answering
# -------------------------------------------------------------
async def tool_rag_qa(
    question: str,
    retrieval_mode: str = "hybrid_rerank",
    top_k: int = 3,
    category: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves relevant chunks from indexed documents and generates grounded response."""
    rag_service = AdvancedRAGService.get_instance()
    llm = LLMService()

    where_filter: Dict[str, Any] = {}
    if category:
        where_filter["category"] = category
    if document_id:
        where_filter["document_id"] = document_id

    chunks = await rag_service.retrieve(
        query=question,
        mode=retrieval_mode,
        top_k=top_k,
        where=where_filter if where_filter else None,
    )

    answer = await llm.generate_answer(
        question=question,
        context_chunks=chunks,
    )

    citations = []
    seen = set()
    for ch in chunks:
        meta = ch.get("metadata", {})
        fname = meta.get("filename", "document")
        pnum = meta.get("page_number", 1)
        if (fname, pnum) not in seen:
            seen.add((fname, pnum))
            citations.append({
                "filename": fname,
                "page_number": pnum,
                "similarity": ch.get("similarity", 0.0),
            })

    return {
        "tool": "rag_qa",
        "question": question,
        "answer": answer,
        "citations": citations,
        "chunks_retrieved": len(chunks),
        "retrieval_mode": retrieval_mode,
    }


# -------------------------------------------------------------
# Tool 2: Resume Analysis Tool
# -------------------------------------------------------------
async def tool_resume_analysis(
    resume_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves candidate's analyzed resume profile, skills, education, and ATS audit."""
    analyzer = ResumeAnalyzerService.get_instance()

    if resume_id:
        profile = analyzer.get_resume(resume_id)
        if not profile:
            return {
                "tool": "resume_analysis",
                "status": "not_found",
                "message": f"Resume with ID '{resume_id}' was not found.",
            }
        return {
            "tool": "resume_analysis",
            "status": "success",
            "resume_id": resume_id,
            "filename": profile.get("filename"),
            "contact_info": profile.get("contact_info", {}),
            "skills": profile.get("skills", {}),
            "education": profile.get("education", []),
            "projects": profile.get("projects", []),
            "strengths": profile.get("strengths", []),
            "missing_information": profile.get("missing_information", []),
            "improvement_suggestions": profile.get("improvement_suggestions", []),
        }

    # Fetch latest uploaded resume
    resumes = analyzer.list_resumes()
    if not resumes:
        return {
            "tool": "resume_analysis",
            "status": "empty",
            "message": "No resumes have been uploaded yet. Please upload a PDF or DOCX resume first.",
        }

    latest = resumes[0]
    return {
        "tool": "resume_analysis",
        "status": "success",
        "resume_id": latest.get("resume_id"),
        "filename": latest.get("filename"),
        "contact_info": latest.get("contact_info", {}),
        "skills": latest.get("skills", {}),
        "education": latest.get("education", []),
        "projects": latest.get("projects", []),
        "strengths": latest.get("strengths", []),
        "missing_information": latest.get("missing_information", []),
        "improvement_suggestions": latest.get("improvement_suggestions", []),
    }


# -------------------------------------------------------------
# Tool 3: Job Description Analysis Tool
# -------------------------------------------------------------
async def tool_job_description_analysis(
    jd_text: str,
    resume_id: Optional[str] = None,
    role_title: Optional[str] = None,
    company_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Extracts required skills and responsibilities from JD and matches against candidate skills."""
    jd_service = JDAnalyzerService.get_instance()
    
    # If no resume_id given, use the latest resume in system if available
    if not resume_id:
        analyzer = ResumeAnalyzerService.get_instance()
        resumes = analyzer.list_resumes()
        if resumes:
            resume_id = resumes[0].get("resume_id")

    analysis = await jd_service.analyze_job_description(
        jd_text=jd_text,
        role_title=role_title or "Software Engineer",
        company_name=company_name,
        resume_id=resume_id,
    )

    return {
        "tool": "job_description_analysis",
        "role_title": analysis.get("role_title"),
        "company_name": analysis.get("company_name"),
        "required_skills": analysis.get("required_skills", []),
        "preferred_skills": analysis.get("preferred_skills", []),
        "skill_match": analysis.get("skill_match"),
        "recommended_learning_topics": analysis.get("recommended_learning_topics", []),
        "preparation_action_plan": analysis.get("preparation_action_plan", []),
    }


# -------------------------------------------------------------
# Tool 4: Technical Question Generation Tool
# -------------------------------------------------------------
async def tool_technical_prep(
    topic: str = "Java",
    difficulty: str = "medium",
    subtopic: Optional[str] = None,
    include_code: bool = True,
) -> Dict[str, Any]:
    """Generates an interview question with technical explanation, code sample, and follow-ups."""
    tech_service = TechnicalPrepService.get_instance()
    q_data = await tech_service.generate_question(
        topic=topic,
        difficulty=difficulty,
        subtopic=subtopic,
        include_code=include_code,
    )

    return {
        "tool": "technical_prep",
        "question_id": q_data.get("question_id"),
        "topic": q_data.get("topic"),
        "subtopic": q_data.get("subtopic"),
        "difficulty": q_data.get("difficulty"),
        "question": q_data.get("question"),
        "answer": q_data.get("answer"),
        "explanation": q_data.get("explanation"),
        "code_example": q_data.get("code_example"),
        "code_language": q_data.get("code_language"),
        "follow_up_questions": q_data.get("follow_up_questions", []),
        "key_takeaways": q_data.get("key_takeaways", []),
    }


# -------------------------------------------------------------
# Tool 5: HR Question Generation Tool
# -------------------------------------------------------------
async def tool_hr_prep(
    category: str = "self_introduction",
    target_company: Optional[str] = None,
    target_role: Optional[str] = "Software Engineer",
    student_background: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates behavioral interview guidance, framework (STAR), and personalized draft answer."""
    hr_service = HRPrepService.get_instance()
    
    # If student_background is omitted, check if resume exists in system to personalize
    if not student_background:
        analyzer = ResumeAnalyzerService.get_instance()
        resumes = analyzer.list_resumes()
        if resumes:
            top_skills = resumes[0].get("skills", {}).get("all_skills", [])[:5]
            student_background = f"Skills in {', '.join(top_skills)} from uploaded resume."

    guidance = await hr_service.generate_hr_guidance(
        category=category,
        target_company=target_company,
        target_role=target_role,
        student_background=student_background,
    )

    return {
        "tool": "hr_prep",
        "draft_id": guidance.get("draft_id"),
        "category": guidance.get("category"),
        "category_label": guidance.get("category_label"),
        "question": guidance.get("question"),
        "framework": guidance.get("framework"),
        "draft_answer": guidance.get("draft_answer"),
        "dos_and_donts": guidance.get("dos_and_donts", []),
        "follow_up_questions": guidance.get("follow_up_questions", []),
    }


# -------------------------------------------------------------
# Tool 6: Aptitude Practice Question Tool
# -------------------------------------------------------------
async def tool_aptitude(
    category: str = "all",
    count: int = 2,
    difficulty: str = "medium",
) -> Dict[str, Any]:
    """Generates multiple-choice aptitude practice questions with options and explanations."""
    apt_service = AptitudeService.get_instance()
    quiz = apt_service.generate_quiz(
        category=category,
        difficulty=difficulty,
        count=count,
    )

    # For the agentic response, also attach explanations so the agent can teach or quiz
    q_map = {q["question_id"]: q for q in apt_service.question_map.values()}
    detailed_questions = []
    for q in quiz.get("questions", []):
        full = q_map.get(q.question_id, {})
        detailed_questions.append({
            "question_id": q.question_id,
            "category": q.category,
            "subtopic": q.subtopic,
            "question_text": q.question_text,
            "options": [{"key": opt.key, "text": opt.text} for opt in q.options],
            "correct_option": full.get("correct_option"),
            "explanation": full.get("explanation"),
        })

    return {
        "tool": "aptitude",
        "category": quiz.get("category"),
        "category_label": quiz.get("category_label"),
        "total_questions": len(detailed_questions),
        "questions": detailed_questions,
    }


# -------------------------------------------------------------
# Tool 7: Mock Interview Evaluation Tool
# -------------------------------------------------------------
async def tool_mock_interview_evaluation(
    question: str,
    student_answer: str,
    topic: str = "General",
    difficulty: str = "medium",
    interview_type: str = "technical",
) -> Dict[str, Any]:
    """Evaluates a student's interview response on 5 criteria and generates improved model answer."""
    mock_service = MockInterviewService.get_instance()
    evaluation = await mock_service._evaluate_response(
        question=question,
        student_answer=student_answer,
        interview_type=interview_type,
        topic=topic,
        difficulty=difficulty,
    )

    return {
        "tool": "mock_interview_evaluation",
        "question": question,
        "student_answer": student_answer,
        "scores": evaluation.get("scores", {}),
        "feedback": evaluation.get("feedback", ""),
        "improved_answer": evaluation.get("improved_answer", ""),
    }
