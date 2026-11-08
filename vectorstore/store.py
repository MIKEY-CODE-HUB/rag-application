import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument

import config
from vectorstore.embeddings import get_embedding_function
from schema import Document

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    Persistent ChromaDB vector store manager.
    Handles embedding storage, retrieval, persistence, deduplication indexing, and collection lifecycle.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
    ):
        self.persist_dir = str(persist_directory or config.CHROMA_PERSIST_DIR)
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.embedding_fn = get_embedding_function(embedding_model_name)

        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False, is_persistent=True),
        )

        # Initialize LangChain Chroma wrapper
        self.store = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_fn,
            persist_directory=self.persist_dir,
        )
        logger.info(
            f"Initialized ChromaVectorStore (dir='{self.persist_dir}', collection='{self.collection_name}')"
        )

    @property
    def collection(self):
        """Access underlying chromadb collection for direct low-level queries."""
        return self.client.get_or_create_collection(name=self.collection_name)

    def add_documents(self, documents: List[Document]) -> int:
        """
        Embed and persist document chunks into ChromaDB.

        Args:
            documents: List of Document objects with page_content and metadata.

        Returns:
            Number of documents added.
        """
        if not documents:
            logger.warning("No documents provided to add to vector store.")
            return 0

        lc_docs: List[LCDocument] = []
        ids: List[str] = []

        for idx, doc in enumerate(documents):
            chunk_id = doc.metadata.get("chunk_id", f"doc_{idx}")
            ids.append(chunk_id)
            lc_docs.append(
                LCDocument(
                    page_content=doc.page_content,
                    metadata=doc.metadata,
                )
            )

        # Add to Chroma
        self.store.add_documents(documents=lc_docs, ids=ids)
        logger.info(f"Successfully indexed and persisted {len(lc_docs)} chunks into ChromaDB.")
        return len(lc_docs)

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> List[Tuple[LCDocument, float]]:
        """
        Perform semantic similarity search against indexed chunks.

        Args:
            query: User search text / query.
            k: Number of relevant chunks to retrieve.

        Returns:
            List of (Document, score) tuples.
        """
        logger.info(f"Executing similarity search for: '{query}' (top_k={k})")
        results = self.store.similarity_search_with_score(query, k=k)
        return results

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve a summary of all distinct documents stored in the database.

        Returns:
            List of dicts: [{'source': str, 'doc_hash': str, 'file_type': str, 'chunk_count': int, 'pages': List[int]}]
        """
        try:
            coll = self.collection
            data = coll.get(include=["metadatas"])
            metadatas = data.get("metadatas") or []

            docs_map: Dict[str, Dict[str, Any]] = {}
            for meta in metadatas:
                if not meta:
                    continue
                source = meta.get("source", "Unknown")
                doc_hash = meta.get("doc_hash", "")
                file_type = meta.get("file_type", "")
                page = meta.get("page", 1)

                if source not in docs_map:
                    docs_map[source] = {
                        "source": source,
                        "doc_hash": doc_hash,
                        "file_type": file_type,
                        "chunk_count": 0,
                        "pages": set(),
                    }

                docs_map[source]["chunk_count"] += 1
                docs_map[source]["pages"].add(page)

            result = []
            for src, info in docs_map.items():
                result.append({
                    "source": info["source"],
                    "doc_hash": info["doc_hash"],
                    "file_type": info["file_type"],
                    "chunk_count": info["chunk_count"],
                    "pages": sorted(list(info["pages"])),
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching indexed documents: {e}")
            return []

    def delete_document(self, source_name: str) -> bool:
        """
        Delete all chunks belonging to a specific source file.

        Args:
            source_name: Name of the source file.

        Returns:
            True if successful.
        """
        try:
            coll = self.collection
            coll.delete(where={"source": source_name})
            logger.info(f"Deleted all records for source: '{source_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete records for source '{source_name}': {e}")
            return False

    def clear_all(self) -> bool:
        """Delete all documents and recreate empty collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            # Recreate empty collection wrapper
            self.store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_fn,
                persist_directory=self.persist_dir,
            )
            logger.info(f"Cleared all entries from collection: '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return total document count and total chunk count."""
        try:
            coll = self.collection
            total_chunks = coll.count()
            docs = self.get_indexed_documents()
            return {
                "total_documents": len(docs),
                "total_chunks": total_chunks,
                "persist_dir": self.persist_dir,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            logger.error(f"Error fetching vector store stats: {e}")
            return {"total_documents": 0, "total_chunks": 0, "error": str(e)}
