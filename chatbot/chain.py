import os
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

import config
from vectorstore.store import ChromaVectorStore
from chatbot.retriever import RAGRetriever
from chatbot.prompts import RAG_SYSTEM_PROMPT, format_context_for_prompt, construct_rag_user_prompt

logger = logging.getLogger(__name__)


class RAGChatbot:
    """
    Retrieval-Augmented Generation (RAG) chatbot using Gemini API
    grounded on ChromaDB vector storage with strict anti-hallucination guardrails.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        vector_store: Optional[ChromaVectorStore] = None,
        top_k: int = 4,
    ):
        self.api_key = api_key or config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or config.GEMINI_MODEL_NAME
        self.vector_store = vector_store or ChromaVectorStore()
        self.retriever = RAGRetriever(vector_store=self.vector_store, top_k=top_k)

        self._client: Optional[genai.Client] = None
        if self.api_key:
            self._init_client()
        else:
            logger.warning("No Gemini API key supplied. Chatbot will run in retrieval-only mode until key is provided.")

    def _init_client(self):
        """Initialize Google GenAI client."""
        try:
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized with model '{self.model_name}'.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            self._client = None

    def set_api_key(self, new_key: str):
        """Update API key dynamically (e.g. from Streamlit UI sidebar)."""
        self.api_key = new_key.strip()
        self._init_client()

    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute full RAG pipeline for a user question:
        1. Query ChromaDB for relevant document chunks.
        2. Construct grounded context.
        3. Call Gemini LLM with strict instructions.
        4. Return response with verified source citations.

        Args:
            question: User's query text.
            top_k: Optional override for number of context chunks.

        Returns:
            Dict containing:
                - answer: str
                - sources: List of source citation dicts
                - query: original question
                - retrieved_chunks_count: int
        """
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "query": question,
                "retrieved_chunks_count": 0,
            }

        # 1. Check if vector store has any documents
        stats = self.vector_store.get_stats()
        if stats.get("total_chunks", 0) == 0:
            return {
                "answer": "I am sorry, but no documents are currently loaded in the database. Please ingest one or more documents (PDF, TXT, DOCX) to begin asking questions.",
                "sources": [],
                "query": question,
                "retrieved_chunks_count": 0,
            }

        # 2. Retrieve relevant document chunks
        retrieved = self.retriever.retrieve(query=question, top_k=top_k)
        if not retrieved:
            return {
                "answer": "I am sorry, but the provided documents do not contain any relevant information for this query.",
                "sources": [],
                "query": question,
                "retrieved_chunks_count": 0,
            }

        # Format sources list for user display
        sources_summary = []
        raw_docs = []
        for item in retrieved:
            raw_docs.append(item["raw_doc"])
            sources_summary.append({
                "source": item["source"],
                "page": item["page"],
                "chunk_index": item["chunk_index"],
                "chunk_id": item["chunk_id"],
                "snippet": item["content"][:200] + ("..." if len(item["content"]) > 200 else ""),
                "score": round(item["score"], 4),
            })

        # 3. Handle missing Gemini API key gracefully
        if not self.api_key or not self._client:
            preview_sources = "\n".join([f"- **{s['source']}** (Page {s['page']}): \"{s['snippet']}\"" for s in sources_summary[:3]])
            return {
                "answer": (
                    "⚠️ **Gemini API Key Required**\n\n"
                    "Semantic search successfully retrieved relevant context chunks, but the Gemini API key is missing.\n\n"
                    "**Retrieved Sources:**\n"
                    f"{preview_sources}\n\n"
                    "👉 *Please enter your Gemini API key in the sidebar or set `GEMINI_API_KEY` in your `.env` file to generate complete AI responses.*"
                ),
                "sources": sources_summary,
                "query": question,
                "retrieved_chunks_count": len(sources_summary),
            }

        # 4. Construct grounded prompt
        context_block = format_context_for_prompt(raw_docs)
        user_prompt = construct_rag_user_prompt(question=question, formatted_context=context_block)

        # 5. Call Gemini API
        try:
            logger.info(f"Invoking Gemini model '{self.model_name}' for query: '{question[:40]}...'")
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=RAG_SYSTEM_PROMPT,
                    temperature=config.TEMPERATURE,
                    max_output_tokens=config.MAX_OUTPUT_TOKENS,
                ),
            )
            answer_text = response.text if response and response.text else "Unable to generate answer."
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            answer_text = f"An error occurred while generating the answer via Gemini API: {str(e)}"

        return {
            "answer": answer_text,
            "sources": sources_summary,
            "query": question,
            "retrieved_chunks_count": len(sources_summary),
        }
