"""
Query Transformation Service.
Provides query rewriting and multi-query expansion for improved retrieval coverage.
"""

from typing import List, Optional
import httpx

from backend.app.core.config import settings


class QueryTransformService:
    """Service to expand, clarify, and generate multi-query variations."""

    _instance: Optional["QueryTransformService"] = None

    def __init__(self, ollama_url: Optional[str] = None, model_name: Optional[str] = None):
        self.ollama_url = (ollama_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL_NAME

    @classmethod
    def get_instance(cls) -> "QueryTransformService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def rule_based_rewrite(query: str) -> str:
        """
        Fast heuristic query expansion for common placement/technical terms.
        Enriches short student questions with relevant technical keywords.
        """
        q_lower = query.lower().strip()
        additions = []

        if "inheritance" in q_lower and "extends" not in q_lower:
            additions.append("extends superclass subclass")
        if "polymorphism" in q_lower and "overriding" not in q_lower:
            additions.append("method overriding dynamic dispatch")
        if "interface" in q_lower and "implements" not in q_lower:
            additions.append("implements abstract methods contract")
        if "skill" in q_lower or "technology" in q_lower:
            additions.append("programming languages tools frameworks")
        if "project" in q_lower or "experience" in q_lower:
            additions.append("architecture development implementation")

        if additions:
            return f"{query} {' '.join(additions)}"
        return query

    async def rewrite_query_llm(self, query: str) -> str:
        """
        Uses Llama 3.2:3b to rewrite a conversational query into a search-optimized technical query.
        Falls back to rule-based rewrite on failure or timeout.
        """
        prompt = (
            f"You are a technical search optimization engine. Rewrite the following placement question into a single, "
            f"clear, keyword-rich technical query for searching document textbooks and resumes. "
            f"Do not answer the question. Return ONLY the rewritten query without quotes or preamble.\n\n"
            f"Question: {query}\n"
            f"Rewritten Query:"
        )

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                if resp.status_code == 200:
                    rewritten = resp.json().get("message", {}).get("content", "").strip()
                    if rewritten and len(rewritten) < 200:
                        return rewritten
        except Exception:
            pass

        return self.rule_based_rewrite(query)

    async def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generates alternative perspectives of the question to improve recall.
        Always includes the original query as the first item.
        """
        queries = [query]

        # Add rule-based rewritten query
        rewritten = self.rule_based_rewrite(query)
        if rewritten != query:
            queries.append(rewritten)

        # Attempt LLM query expansion
        prompt = (
            f"Generate {num_queries - 1} diverse search queries related to the following technical placement question. "
            f"Each query should capture a different perspective, sub-concept, or technical synonym. "
            f"Provide one query per line without numbering.\n\n"
            f"Original Question: {query}\n"
            f"Alternative Queries:"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.4},
                    },
                )
                if resp.status_code == 200:
                    text = resp.json().get("message", {}).get("content", "").strip()
                    for line in text.split("\n"):
                        clean_line = line.strip().lstrip("1234567890.- ")
                        if clean_line and clean_line != query and clean_line not in queries:
                            queries.append(clean_line)
                            if len(queries) >= num_queries:
                                break
        except Exception:
            pass

        return queries[:num_queries]
