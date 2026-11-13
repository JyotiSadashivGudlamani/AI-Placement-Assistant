"""
Ollama LLM service integrating Llama 3.2:3b for context-grounded RAG answering.
Includes prompt templates, history formatting, and source verification.
"""

from typing import Any, Dict, List, Optional
import httpx

from backend.app.core.config import settings


class LLMServiceError(Exception):
    """Base exception for LLM generation errors."""
    pass


class OllamaConnectionError(LLMServiceError):
    """Raised when Ollama cannot be reached."""
    pass


class OllamaResponseError(LLMServiceError):
    """Raised when Ollama returns an error or invalid payload."""
    pass


class LLMService:
    """Service to interface with Ollama (Llama 3.2:3b) with RAG grounding."""

    SYSTEM_PROMPT = (
        "You are an intelligent, precise AI Placement Preparation Assistant.\n"
        "Your mission is to help students with their interview preparation, technical concepts, "
        "placement topics, and resume questions based strictly on the provided DOCUMENT CONTEXT.\n\n"
        "STRICT GROUNDING RULES:\n"
        "1. Base your answer strictly on the facts, code, and definitions directly stated in the DOCUMENT CONTEXT below.\n"
        "2. If the provided DOCUMENT CONTEXT does not contain sufficient or relevant information to answer the user's question, "
        "you MUST explicitly state: \"The provided documents do not contain sufficient information to answer this question.\"\n"
        "3. NEVER invent, extrapolate, or hallucinate document content, facts, or citations.\n"
        "4. When discussing technical concepts (e.g. inheritance, data structures), reference the terminology and explanations from the document.\n"
        "5. Keep your tone professional, encouraging, and structured with headings or bullet points where beneficial."
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL_NAME
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
    ) -> str:
        """Formats retrieved chunks with citations into the grounded user prompt."""
        if not context_chunks:
            return (
                f"DOCUMENT CONTEXT: [No relevant document context found for this query.]\n\n"
                f"QUESTION: {question}\n\n"
                f"Remember: If the document context is insufficient, state that the provided documents do not contain "
                f"sufficient information to answer the question."
            )

        context_blocks = []
        for i, chunk in enumerate(context_chunks, start=1):
            meta = chunk.get("metadata", {})
            filename = meta.get("filename", "document")
            page_num = meta.get("page_number", 1)
            chunk_text = chunk.get("text", "").strip()

            block = (
                f"--- CONTEXT BLOCK {i} [Source: {filename} | Page: {page_num}] ---\n"
                f"{chunk_text}\n"
            )
            context_blocks.append(block)

        formatted_context = "\n".join(context_blocks)

        user_content = (
            f"DOCUMENT CONTEXT:\n"
            f"{formatted_context}\n"
            f"-----------------------------------------\n"
            f"QUESTION: {question}\n\n"
            f"Answer based strictly on the DOCUMENT CONTEXT above. Include references to the relevant source and page numbers."
        )
        return user_content

    async def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Sends prompt and history to Ollama and returns the generated answer."""
        url = f"{self.base_url}/api/chat"

        # Build messages payload
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # Append recent history (up to last 6 messages to protect context window)
        if conversation_history:
            recent_turns = conversation_history[-6:]
            for turn in recent_turns:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Append current user prompt with injected document context
        rag_user_prompt = self.build_rag_prompt(question, context_chunks)
        messages.append({"role": "user", "content": rag_user_prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2,  # Low temperature for factual grounding
                "top_p": 0.9,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

            if response.status_code != 200:
                raise OllamaResponseError(
                    f"Ollama returned HTTP {response.status_code}: {response.text}"
                )

            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "").strip()

            if not content:
                raise OllamaResponseError("Empty content received from Ollama.")

            return content

        except httpx.ConnectError as error:
            raise OllamaConnectionError(
                f"Could not connect to Ollama at {self.base_url}. Ensure the Ollama service is running."
            ) from error
        except httpx.TimeoutException as error:
            raise OllamaResponseError(
                f"Ollama request timed out after {self.timeout} seconds."
            ) from error
        except Exception as error:
            if isinstance(error, LLMServiceError):
                raise
            raise OllamaResponseError(f"Unexpected Ollama error: {str(error)}") from error
