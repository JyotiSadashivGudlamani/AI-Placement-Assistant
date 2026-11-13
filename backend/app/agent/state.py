"""
LangGraph Agent State definition for Phase 6 Agentic Placement Assistant.
Defines structured state, intent tracking, tool parameters, results, and memory checkpoints.
"""

from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """
    Structured state passed between LangGraph nodes during execution.
    All fields are explicitly tracked to guarantee controlled conversation state.
    """
    session_id: str
    user_id: Optional[str]
    messages: List[BaseMessage]
    user_request: str
    
    # Classification & Routing
    intent: str  # 'rag_qa' | 'resume_analysis' | 'jd_analysis' | 'technical_prep' | 'hr_prep' | 'aptitude' | 'mock_interview_evaluation' | 'general_chat' | 'invalid'
    intent_confidence: float
    extracted_parameters: Dict[str, Any]
    
    # Tool Execution
    tool_name: Optional[str]
    tool_input: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]]
    
    # Response & Synthesis
    final_response: str
    citations: Optional[List[Dict[str, Any]]]
    suggested_actions: Optional[List[str]]
    
    # Control & Resilience
    error: Optional[str]
    retry_count: int
    execution_path: List[str]
