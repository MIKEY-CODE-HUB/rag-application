import io
import logging
from typing import Union, Dict, Any, Optional
from pathlib import Path

from ingestion.document_loader import DocumentLoader, Document
from ingestion.text_splitter import DocumentChunker
from ingestion.deduplication import compute_file_hash, DeduplicationManager
from vectorstore.store import ChromaVectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the end-to-end document ingestion workflow:
    Extraction -> Deduplication -> Chunking -> Embedding -> ChromaDB Vector Storage.
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.dedup_manager = DeduplicationManager(vector_store=self.vector_store)
        logger.info("IngestionPipeline initialized.")

    def ingest(
        self,
        file_source: Union[str, Path, io.BytesIO],
        file_name: Optional[str] = None,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest a single document (PDF, TXT, DOCX) into the vector store.

        Args:
            file_source: Path or BytesIO of document.
            file_name: Optional file name if passing BytesIO.
            force_reindex: If True, bypass duplicate checks.

        Returns:
            Dict containing ingestion summary and status.
        """
        # Determine filename
        if isinstance(file_source, (str, Path)):
            resolved_path = Path(file_source)
            actual_name = resolved_path.name
        else:
            actual_name = file_name or "uploaded_document"

        logger.info(f"Starting ingestion process for: '{actual_name}'")

        # 1. Deduplication Check
        file_hash = compute_file_hash(file_source)
        if not force_reindex:
            is_dup, action = self.dedup_manager.check_duplicate(actual_name, file_hash)
            if is_dup:
                logger.info(f"Skipping ingestion for '{actual_name}' - already indexed with identical hash.")
                return {
                    "status": "skipped",
                    "reason": "duplicate",
                    "file_name": actual_name,
                    "doc_hash": file_hash,
                    "message": f"Document '{actual_name}' is already ingested with identical content.",
                }
            elif action == "update":
                logger.info(f"Updating '{actual_name}' - removing previous chunks.")
                self.vector_store.delete_document(actual_name)

        # 2. Extract Document Content
        raw_docs = DocumentLoader.load(file_source, file_name=actual_name)
        if not raw_docs:
            return {
                "status": "error",
                "reason": "empty_document",
                "file_name": actual_name,
                "message": f"No readable text could be extracted from '{actual_name}'.",
            }

        # Tag raw documents with doc_hash
        for doc in raw_docs:
            doc.metadata["doc_hash"] = file_hash

        # 3. Chunk Document
        chunked_docs = self.chunker.split_documents(raw_docs)
        if not chunked_docs:
            return {
                "status": "error",
                "reason": "chunking_failed",
                "file_name": actual_name,
                "message": f"Document chunking produced zero splits for '{actual_name}'.",
            }

        # 4. Embed and Store in ChromaDB
        indexed_count = self.vector_store.add_documents(chunked_docs)

        total_pages = max([d.metadata.get("page", 1) for d in chunked_docs])
        logger.info(f"Successfully completed ingestion for '{actual_name}' ({indexed_count} chunks indexed).")

        return {
            "status": "success",
            "file_name": actual_name,
            "file_type": chunked_docs[0].metadata.get("file_type", "unknown"),
            "total_pages": total_pages,
            "total_chunks": indexed_count,
            "doc_hash": file_hash,
            "message": f"Successfully indexed {indexed_count} chunks from '{actual_name}'.",
        }
