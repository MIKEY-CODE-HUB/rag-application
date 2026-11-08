import logging
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from schema import Document

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Configurable document chunker utilizing RecursiveCharacterTextSplitter
    while preserving and augmenting document metadata.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
        )
        logger.info(
            f"Initialized DocumentChunker (chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap})"
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into chunks, propagating and enriching metadata.

        Args:
            documents: List of Document objects.

        Returns:
            List of chunked Document objects with updated metadata.
        """
        chunked_docs: List[Document] = []

        for doc_idx, doc in enumerate(documents):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", 1)
            file_type = doc.metadata.get("file_type", "unknown")
            doc_hash = doc.metadata.get("doc_hash", "")

            # Split text
            text_splits = self._splitter.split_text(doc.page_content)
            total_chunks = len(text_splits)

            for chunk_idx, text_chunk in enumerate(text_splits):
                chunk_meta = {
                    **doc.metadata,
                    "source": source,
                    "page": page,
                    "file_type": file_type,
                    "doc_hash": doc_hash,
                    "chunk_index": chunk_idx,
                    "total_chunks_in_segment": total_chunks,
                    "chunk_id": f"{source}_p{page}_c{chunk_idx}",
                }
                chunked_docs.append(Document(page_content=text_chunk, metadata=chunk_meta))

        logger.info(f"Split {len(documents)} document sections into {len(chunked_docs)} chunks.")
        return chunked_docs
