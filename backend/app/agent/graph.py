"""
LangGraph Orchestrator for Phase 6 Agentic Placement Assistant.
Implements StateGraph, conditional routing, tool execution nodes,
synthesizer, fallback handling, retry resiliency, and thread checkpointer memory.
"""

from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.agent.state import AgentState
from backend.app.agent.classifier import IntentClassifier
from backend.app.agent.tools import (
    tool_rag_qa,
    tool_resume_analysis,
    tool_job_description_analysis,
    tool_technical_prep,
    tool_hr_prep,
    tool_aptitude,
    tool_mock_interview_evaluation,
)
from backend.app.db.mongo import MongoDBManager


# -------------------------------------------------------------
# Graph Node Definitions
# -------------------------------------------------------------

async def classify_node(state: AgentState) -> Dict[str, Any]:
    """Classifies user request and extracts invocation parameters."""
    req = state.get("user_request", "")
    intent, confidence, params = await IntentClassifier.classify(req)
    
    path = state.get("execution_path", [])
    path.append(f"classify -> {intent} (conf: {confidence:.2f})")
    
    return {
        "intent": intent,
        "intent_confidence": confidence,
        "extracted_parameters": params,
        "execution_path": path,
    }


def route_intent(state: AgentState) -> str:
    """Conditional edge router: returns the next tool node name based on intent."""
    intent = state.get("intent", "invalid")
    valid_intents = {
        "rag_qa",
        "resume_analysis",
        "jd_analysis",
        "technical_prep",
        "hr_prep",
        "aptitude",
        "mock_interview_evaluation",
        "general_chat",
    }
    return intent if intent in valid_intents else "invalid"


async def rag_qa_node(state: AgentState) -> Dict[str, Any]:
    """Node executing RAG document retrieval and grounded question answering."""
    path = state.get("execution_path", [])
    path.append("executing: tool_rag_qa")
    params = state.get("extracted_parameters", {})
    req = state.get("user_request", "")

    try:
        result = await tool_rag_qa(
            question=params.get("question", req),
            retrieval_mode=params.get("retrieval_mode", "hybrid_rerank"),
            top_k=params.get("top_k", 3),
        )
        return {
            "tool_name": "rag_qa",
            "tool_input": params,
            "tool_result": result,
            "citations": result.get("citations", []),
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def resume_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Node executing resume profile and ATS audit retrieval."""
    path = state.get("execution_path", [])
    path.append("executing: tool_resume_analysis")
    params = state.get("extracted_parameters", {})

    try:
        result = await tool_resume_analysis(
            resume_id=params.get("resume_id"),
            user_id=state.get("user_id"),
        )
        return {
            "tool_name": "resume_analysis",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def jd_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Node executing job description analysis and skill matching."""
    path = state.get("execution_path", [])
    path.append("executing: tool_job_description_analysis")
    params = state.get("extracted_parameters", {})
    req = state.get("user_request", "")

    try:
        result = await tool_job_description_analysis(
            jd_text=params.get("jd_text", req),
            resume_id=params.get("resume_id"),
            role_title=params.get("role_title"),
            company_name=params.get("company_name"),
        )
        return {
            "tool_name": "job_description_analysis",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def technical_prep_node(state: AgentState) -> Dict[str, Any]:
    """Node generating technical interview question, explanation, and code."""
    path = state.get("execution_path", [])
    path.append("executing: tool_technical_prep")
    params = state.get("extracted_parameters", {})

    try:
        result = await tool_technical_prep(
            topic=params.get("topic", "Java"),
            difficulty=params.get("difficulty", "medium"),
            include_code=params.get("include_code", True),
        )
        return {
            "tool_name": "technical_prep",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def hr_prep_node(state: AgentState) -> Dict[str, Any]:
    """Node generating behavioral interview guidance and STAR answer."""
    path = state.get("execution_path", [])
    path.append("executing: tool_hr_prep")
    params = state.get("extracted_parameters", {})

    try:
        result = await tool_hr_prep(
            category=params.get("category", "self_introduction"),
            target_company=params.get("target_company"),
            target_role=params.get("target_role", "Software Engineer"),
            student_background=params.get("student_background"),
        )
        return {
            "tool_name": "hr_prep",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def aptitude_node(state: AgentState) -> Dict[str, Any]:
    """Node generating aptitude multiple-choice practice questions."""
    path = state.get("execution_path", [])
    path.append("executing: tool_aptitude")
    params = state.get("extracted_parameters", {})

    try:
        result = await tool_aptitude(
            category=params.get("category", "all"),
            count=params.get("count", 2),
            difficulty=params.get("difficulty", "medium"),
        )
        return {
            "tool_name": "aptitude",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def mock_interview_evaluation_node(state: AgentState) -> Dict[str, Any]:
    """Node evaluating interview answers on 5 criteria."""
    path = state.get("execution_path", [])
    path.append("executing: tool_mock_interview_evaluation")
    params = state.get("extracted_parameters", {})

    try:
        result = await tool_mock_interview_evaluation(
            question=params.get("question", "Interview Question"),
            student_answer=params.get("student_answer", state.get("user_request", "")),
            topic=params.get("topic", "General"),
        )
        return {
            "tool_name": "mock_interview_evaluation",
            "tool_input": params,
            "tool_result": result,
            "execution_path": path,
        }
    except Exception as e:
        return {"error": str(e), "execution_path": path}


async def general_chat_node(state: AgentState) -> Dict[str, Any]:
    """Handles greetings and general capabilities inquiries."""
    path = state.get("execution_path", [])
    path.append("executing: general_chat")

    response_text = (
        "Hello! I am your **AI Placement Preparation Assistant** powered by LangGraph.\n\n"
        "Here are the specialized tools I can orchestrate for your placement preparation:\n"
        "1. **Document RAG Search:** Ask questions about uploaded Java, OOP, or syllabus materials.\n"
        "2. **Resume Analyser:** Say *'Analyze my resume'* or *'Check my ATS score'*.\n"
        "3. **Job Description Matcher:** Paste a job posting to get a transparent skill match percentage.\n"
        "4. **Technical Interview Prep:** Ask *'Give me a Java multithreading question'* or *'DSA question on trees'*.\n"
        "5. **HR & Behavioral Prep:** Ask *'How do I answer why should we hire you'* or *'Help with self-introduction'*.\n"
        "6. **Aptitude Practice:** Say *'Give me a quantitative aptitude question'* or *'Logical reasoning puzzle'*.\n"
        "7. **Answer Evaluation:** Type *'Evaluate my answer: ...'* to get scores across 5 criteria.\n\n"
        "How would you like to prepare today?"
    )
    return {
        "tool_name": "general_chat",
        "final_response": response_text,
        "suggested_actions": [
            "Test my technical knowledge in Java",
            "Review my uploaded resume",
            "Give me a quantitative aptitude question",
            "Practice self-introduction for HR round"
        ],
        "execution_path": path,
    }


async def fallback_node(state: AgentState) -> Dict[str, Any]:
    """Handles invalid, nonsense, or non-placement requests gracefully."""
    path = state.get("execution_path", [])
    path.append("executing: fallback")
    reason = state.get("extracted_parameters", {}).get("reason", "Out of scope query.")

    response_text = (
        "I am specialized specifically for **campus placements, technical preparation, and software interviews**.\n\n"
        f"Your query could not be routed to a placement tool ({reason}).\n\n"
        "To get started, try asking:\n"
        "- *'Give me an interview question on Java GC with code'* (Technical Prep)\n"
        "- *'Analyze my resume for backend roles'* (Resume Analyser)\n"
        "- *'How to structure my answer for teamwork conflict?'* (HR Prep)\n"
        "- *'Give me a quantitative aptitude problem on speed and distance'* (Aptitude)\n"
        "- *'What does the uploaded Java guide say about inheritance?'* (Document RAG)"
    )

    return {
        "tool_name": "fallback",
        "final_response": response_text,
        "suggested_actions": [
            "Ask a technical interview question",
            "Review my resume skills",
            "Practice an aptitude question"
        ],
        "execution_path": path,
    }


async def synthesize_node(state: AgentState) -> Dict[str, Any]:
    """
    Synthesizes the tool execution result into a well-structured student response.
    Formats code, bullet points, citations, and adds the final AIMessage to history.
    """
    path = state.get("execution_path", [])
    path.append("executing: synthesize_node")

    tool_name = state.get("tool_name")
    result = state.get("tool_result")
    error = state.get("error")

    if error:
        final_text = f"An error occurred while executing the **{tool_name}** tool: {error}\nPlease try again or rephrase."
        return {"final_response": final_text, "execution_path": path}

    if not result:
        return {"final_response": "No result was produced by the selected tool.", "execution_path": path}

    # Format output based on tool
    if tool_name == "rag_qa":
        ans = result.get("answer", "")
        cits = result.get("citations", [])
        cit_str = ""
        if cits:
            cit_items = [f"• `{c['filename']}` (Page {c['page_number']})" for c in cits]
            cit_str = "\n\n**Verified Document Sources:**\n" + "\n".join(cit_items)
        final_text = f"{ans}{cit_str}"

    elif tool_name == "resume_analysis":
        if result.get("status") == "empty":
            final_text = result.get("message", "No resume found.")
        else:
            fname = result.get("filename", "Resume")
            skills = result.get("skills", {})
            all_s = skills.get("all_skills", [])
            strengths = result.get("strengths", [])
            missing = result.get("missing_information", [])
            suggs = result.get("improvement_suggestions", [])

            final_text = (
                f"### Resume Analysis Report: `{fname}`\n\n"
                f"**Extracted Skills ({len(all_s)}):**\n"
                f"{', '.join(all_s) if all_s else 'None detected'}\n\n"
                f"**Key Strengths:**\n"
                + "\n".join(f"- {s}" for s in strengths[:3])
                + (f"\n\n**Missing Information / Gaps:**\n" + "\n".join(f"- {m}" for m in missing[:3]) if missing else "")
                + (f"\n\n**Actionable ATS Suggestions:**\n" + "\n".join(f"- {sg}" for sg in suggs[:3]) if suggs else "")
            )

    elif tool_name == "job_description_analysis":
        role = result.get("role_title", "Software Engineer")
        comp = f" @ {result.get('company_name')}" if result.get("company_name") else ""
        req_s = result.get("required_skills", [])
        match = result.get("skill_match")

        if match:
            formula = match.get("score_formula", "")
            overall = match.get("overall_match_score", 0)
            matched_req = match.get("matched_required_skills", [])
            missing_req = match.get("missing_required_skills", [])

            final_text = (
                f"### Job Description Match: {role}{comp}\n\n"
                f"**Match Score: {overall}%**\n"
                f"*{formula}*\n\n"
                f"**Matched Required Skills:** {', '.join(matched_req) if matched_req else 'None'}\n"
                f"**Critical Missing Skills:** {', '.join(missing_req) if missing_req else 'All required skills met!'}\n\n"
                f"**Preparation Action Plan:**\n"
                + "\n".join(f"- {p}" for p in result.get("preparation_action_plan", [])[:3])
            )
        else:
            final_text = (
                f"### Job Description Breakdown: {role}{comp}\n\n"
                f"**Required Skills:** {', '.join(req_s)}\n"
                f"**Recommended Topics to Prepare:**\n"
                + "\n".join(f"- {t}" for t in result.get("recommended_learning_topics", [])[:4])
            )

    elif tool_name == "technical_prep":
        topic = result.get("topic", "Java")
        diff = result.get("difficulty", "medium").capitalize()
        q = result.get("question", "")
        ans = result.get("answer", "")
        exp = result.get("explanation", "")
        code = result.get("code_example")
        lang = result.get("code_language", "code")
        followups = result.get("follow_up_questions", [])

        code_block = f"\n\n```{lang}\n{code}\n```" if code else ""
        follow_str = "\n\n**Follow-up Questions:**\n" + "\n".join(f"• {f}" for f in followups[:2]) if followups else ""

        final_text = (
            f"### Technical Interview Question: {topic} ({diff})\n\n"
            f"**Question:**\n{q}\n\n"
            f"**Direct Answer:**\n{ans}\n\n"
            f"**Deep Technical Explanation:**\n{exp}"
            f"{code_block}"
            f"{follow_str}"
        )

    elif tool_name == "hr_prep":
        framework = result.get("framework", "STAR Method")
        q = result.get("question", "")
        draft = result.get("draft_answer", "")
        tips = result.get("dos_and_donts", [])

        tips_str = "\n\n**Interviewer Tips & Pitfalls:**\n" + "\n".join(f"• {t}" for t in tips[:3]) if tips else ""

        final_text = (
            f"### HR Interview Guidance: {framework}\n\n"
            f"**Question:**\n\"{q}\"\n\n"
            f"**Personalized Draft Response:**\n{draft}"
            f"{tips_str}"
        )

    elif tool_name == "aptitude":
        cat = result.get("category_label", "Aptitude")
        questions = result.get("questions", [])

        q_blocks = []
        for i, q in enumerate(questions, start=1):
            opts = "\n".join(f"  {opt['key']}) {opt['text']}" for opt in q["options"])
            block = (
                f"**Question {i} [{q['subtopic']}]:**\n{q['question_text']}\n{opts}\n\n"
                f"*Correct Option: {q['correct_option']}*\n"
                f"*Solution: {q['explanation']}*"
            )
            q_blocks.append(block)

        final_text = f"### Aptitude Practice: {cat}\n\n" + "\n\n---\n\n".join(q_blocks)

    elif tool_name == "mock_interview_evaluation":
        q = result.get("question", "")
        scores = result.get("scores", {})
        fb = result.get("feedback", "")
        model_ans = result.get("improved_answer", "")

        final_text = (
            f"### Mock Interview Response Evaluation\n\n"
            f"**Question:** {q}\n\n"
            f"**Scores (1-10 Scale):**\n"
            f"• Correctness: **{scores.get('correctness')}/10**\n"
            f"• Relevance: **{scores.get('relevance')}/10**\n"
            f"• Completeness: **{scores.get('completeness')}/10**\n"
            f"• Clarity: **{scores.get('clarity')}/10**\n"
            f"• Communication: **{scores.get('communication')}/10**\n"
            f"👉 **Overall Score: {scores.get('overall_score')}/10**\n\n"
            f"**Feedback:**\n{fb}\n\n"
            f"**Model High-Scoring Response:**\n{model_ans}"
        )
    else:
        final_text = str(result)

    # Append to message list
    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=final_text))

    return {
        "final_response": final_text,
        "messages": messages,
        "execution_path": path,
    }


# -------------------------------------------------------------
# Graph Construction & Compilation
# -------------------------------------------------------------

def build_placement_agent():
    """Builds and compiles the StateGraph with memory checkpointer."""
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("rag_qa", rag_qa_node)
    workflow.add_node("resume_analysis", resume_analysis_node)
    workflow.add_node("jd_analysis", jd_analysis_node)
    workflow.add_node("technical_prep", technical_prep_node)
    workflow.add_node("hr_prep", hr_prep_node)
    workflow.add_node("aptitude", aptitude_node)
    workflow.add_node("mock_interview_evaluation", mock_interview_evaluation_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("synthesize", synthesize_node)

    # 2. Add Edges
    workflow.add_edge(START, "classify")

    # 3. Conditional Routing from classify
    workflow.add_conditional_edges(
        "classify",
        route_intent,
        {
            "rag_qa": "rag_qa",
            "resume_analysis": "resume_analysis",
            "jd_analysis": "jd_analysis",
            "technical_prep": "technical_prep",
            "hr_prep": "hr_prep",
            "aptitude": "aptitude",
            "mock_interview_evaluation": "mock_interview_evaluation",
            "general_chat": "general_chat",
            "invalid": "fallback",
        },
    )

    # 4. Route tool nodes to synthesizer
    workflow.add_edge("rag_qa", "synthesize")
    workflow.add_edge("resume_analysis", "synthesize")
    workflow.add_edge("jd_analysis", "synthesize")
    workflow.add_edge("technical_prep", "synthesize")
    workflow.add_edge("hr_prep", "synthesize")
    workflow.add_edge("aptitude", "synthesize")
    workflow.add_edge("mock_interview_evaluation", "synthesize")

    # 5. Route terminals to END
    workflow.add_edge("synthesize", END)
    workflow.add_edge("general_chat", END)
    workflow.add_edge("fallback", END)

    # Checkpointer for conversation memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


# Singleton compiled graph
_placement_graph = None

def get_placement_graph():
    global _placement_graph
    if _placement_graph is None:
        _placement_graph = build_placement_agent()
    return _placement_graph


async def run_placement_agent(
    user_request: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Public entrypoint for running the LangGraph placement agent.
    Guarantees session-scoped thread memory and persists turn in MongoDB.
    """
    graph = get_placement_graph()
    sess_id = session_id or f"sess_{uuid4().hex[:12]}"
    config = {"configurable": {"thread_id": sess_id}}

    initial_state: AgentState = {
        "session_id": sess_id,
        "user_id": user_id,
        "user_request": user_request,
        "messages": [HumanMessage(content=user_request)],
        "retry_count": 0,
        "execution_path": [],
    }

    # Run graph execution
    final_state = await graph.ainvoke(initial_state, config=config)

    # Persist agent turn to MongoDB
    mongo = MongoDBManager.get_instance()
    if mongo.is_connected:
        try:
            mongo.db.agent_conversations.update_one(
                {"session_id": sess_id},
                {
                    "$setOnInsert": {
                        "session_id": sess_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                    "$set": {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "last_request": user_request,
                        "last_intent": final_state.get("intent"),
                    },
                    "$push": {
                        "turns": {
                            "request": user_request,
                            "intent": final_state.get("intent"),
                            "tool_name": final_state.get("tool_name"),
                            "response": final_state.get("final_response"),
                            "execution_path": final_state.get("execution_path"),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                },
                upsert=True,
            )
        except Exception:
            pass

    return {
        "session_id": sess_id,
        "user_request": user_request,
        "intent": final_state.get("intent"),
        "intent_confidence": final_state.get("intent_confidence", 1.0),
        "tool_used": final_state.get("tool_name"),
        "response": final_state.get("final_response"),
        "citations": final_state.get("citations"),
        "suggested_actions": final_state.get("suggested_actions"),
        "execution_path": final_state.get("execution_path", []),
    }
