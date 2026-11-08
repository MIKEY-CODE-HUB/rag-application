import logging
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document as LCDocument
from vectorstore.store import ChromaVectorStore
import config

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Retrieves semantic matches from ChromaDB for a given query,
    formats sources, and filters low-confidence matches.
    """

    def __init__(self, vector_store: Optional[ChromaVectorStore] = None, top_k: int = 4):
        self.vector_store = vector_store or ChromaVectorStore()
        self.top_k = top_k

    def retrieve(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute similarity search and return formatted chunk metadata.

        Args:
            query: Question or search string.
            top_k: Optional override for number of chunks.

        Returns:
            List of dicts: [
                {
                    "content": str,
                    "source": str,
                    "page": int,
                    "chunk_index": int,
                    "chunk_id": str,
                    "score": float,
                    "raw_doc": LCDocument
                }
            ]
        """
        k = top_k or self.top_k
        results = self.vector_store.similarity_search_with_score(query=query, k=k)

        formatted_results: List[Dict[str, Any]] = []
        for doc, score in results:
            meta = doc.metadata or {}
            formatted_results.append({
                "content": doc.page_content,
                "source": meta.get("source", "Unknown Document"),
                "page": meta.get("page", 1),
                "chunk_index": meta.get("chunk_index", 0),
                "chunk_id": meta.get("chunk_id", "unknown_id"),
                "file_type": meta.get("file_type", "unknown"),
                "score": float(score),
                "raw_doc": doc,
            })

        logger.info(f"Retrieved {len(formatted_results)} chunks for query: '{query[:50]}...'")
        return formatted_results
