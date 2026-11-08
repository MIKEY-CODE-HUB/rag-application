"""
System prompts and prompt templates for context-grounded RAG.
"""

from typing import List
from langchain_core.documents import Document


RAG_SYSTEM_PROMPT = """You are an expert AI assistant specializing in answering questions accurately based strictly on provided source documents.

CRITICAL INSTRUCTIONS:
1. Base your answer ONLY on the context provided in the 'CONTEXT DOCUMENTS' section below.
2. Do NOT use any external knowledge, assumptions, or unmentioned facts.
3. If the context does not contain sufficient information to answer the question truthfully and completely, you MUST state clearly:
   "I am sorry, but the provided documents do not contain sufficient information to answer this question."
4. Every statement or claim you make MUST cite its source using this format: [Document: <filename>, Page: <page>].
5. Present your response in clear, well-structured Markdown format (using bullet points or concise paragraphs where helpful).
6. Never make up or hallucinate sources or page numbers.
"""


def format_context_for_prompt(retrieved_docs: List[Document]) -> str:
    """
    Format retrieved LangChain documents into a clearly delimited context block.
    """
    if not retrieved_docs:
        return "No relevant context documents found."

    context_segments = []
    for idx, doc in enumerate(retrieved_docs):
        source = doc.metadata.get("source", "Unknown Document")
        page = doc.metadata.get("page", 1)
        chunk_idx = doc.metadata.get("chunk_index", 0)

        segment = (
            f"--- DOCUMENT {idx + 1} ---\n"
            f"Source: {source} (Page: {page}, Chunk: {chunk_idx})\n"
            f"Content:\n{doc.page_content.strip()}\n"
        )
        context_segments.append(segment)

    return "\n".join(context_segments)


def construct_rag_user_prompt(question: str, formatted_context: str) -> str:
    """Construct user message combining question and grounded context."""
    return f"""CONTEXT DOCUMENTS:
{formatted_context}

-------------------------
USER QUESTION:
{question}

Please answer the question accurately using ONLY the context provided above. Always include inline source citations [Document: <filename>, Page: <page>]."""
