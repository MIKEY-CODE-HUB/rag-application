import hashlib
import io
import logging
from typing import Union, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_file_hash(file_source: Union[str, Path, io.BytesIO, bytes]) -> str:
    """
    Compute SHA-256 hash for a given file path, BytesIO stream, or raw bytes.

    Args:
        file_source: Path, BytesIO, or bytes.

    Returns:
        Hexadecimal SHA-256 string.
    """
    sha256 = hashlib.sha256()

    if isinstance(file_source, bytes):
        sha256.update(file_source)
    elif isinstance(file_source, (str, Path)):
        with open(file_source, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
    elif isinstance(file_source, io.BytesIO):
        curr_pos = file_source.tell()
        file_source.seek(0)
        for chunk in iter(lambda: file_source.read(65536), b""):
            sha256.update(chunk)
        file_source.seek(curr_pos)
    else:
        raise ValueError(f"Unsupported file_source type: {type(file_source)}")

    return sha256.hexdigest()


class DeduplicationManager:
    """
    Manages document deduplication using cryptographic content hashing
    and metadata comparison with existing vector store records.
    """

    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    def check_duplicate(self, file_name: str, file_hash: str) -> Tuple[bool, str]:
        """
        Check if document is an exact duplicate, an update, or a new document.

        Returns:
            Tuple of (is_duplicate: bool, action_description: str)
            - (True, "exact_duplicate"): Document with same hash already indexed.
            - (False, "update"): Document with same name exists with different hash.
            - (False, "new"): Completely new document.
        """
        if not self.vector_store:
            return False, "new"

        existing_docs = self.vector_store.get_indexed_documents()

        for doc in existing_docs:
            if doc.get("doc_hash") == file_hash:
                logger.info(f"Duplicate document detected for '{file_name}' (Hash: {file_hash[:8]}...)")
                return True, "exact_duplicate"
            if doc.get("source") == file_name:
                logger.info(f"Document '{file_name}' found with differing hash. Will update/replace.")
                return False, "update"

        return False, "new"
