import os
import io
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from pypdf import PdfReader
import docx
from schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Modular loader for extracting text and metadata from PDF, TXT, and DOCX documents.
    Supports both file system paths and in-memory file-like objects (e.g., Streamlit uploads).
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}

    @classmethod
    def load(cls, file_source: Union[str, Path, io.BytesIO], file_name: Optional[str] = None) -> List[Document]:
        """
        Extract text and metadata from a file path or file-like object.

        Args:
            file_source: Path to document or io.BytesIO/file-like object.
            file_name: Explicit file name if file_source is BytesIO.

        Returns:
            List of Document objects with page content and metadata (source, page, file_type).
        """
        if isinstance(file_source, (str, Path)):
            path = Path(file_source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            name = path.name
            ext = path.suffix.lower()
            with open(path, "rb") as f:
                stream = io.BytesIO(f.read())
        else:
            if not file_name:
                raise ValueError("file_name must be provided when passing a stream or BytesIO.")
            name = file_name
            ext = Path(name).suffix.lower()
            stream = file_source

        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{ext}'. Supported formats: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

        logger.info(f"Extracting content from '{name}' ({ext})")

        if ext == ".pdf":
            return cls._load_pdf(stream, name)
        elif ext == ".docx":
            return cls._load_docx(stream, name)
        elif ext == ".txt":
            return cls._load_txt(stream, name)
        else:
            raise ValueError(f"No parser available for extension: {ext}")

    @classmethod
    def _load_pdf(cls, stream: io.BytesIO, file_name: str) -> List[Document]:
        """Extract text from PDF page by page preserving 1-based page numbers."""
        stream.seek(0)
        reader = PdfReader(stream)
        documents: List[Document] = []
        total_pages = len(reader.pages)

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                text = page.extract_text() or ""
                cleaned_text = text.strip()
                if cleaned_text:
                    documents.append(
                        Document(
                            page_content=cleaned_text,
                            metadata={
                                "source": file_name,
                                "file_type": "pdf",
                                "page": page_num,
                                "total_pages": total_pages,
                            },
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num} of {file_name}: {e}")

        if not documents:
            logger.warning(f"No readable text extracted from PDF '{file_name}'.")

        return documents

    @classmethod
    def _load_docx(cls, stream: io.BytesIO, file_name: str) -> List[Document]:
        """Extract text paragraphs and tables from DOCX."""
        stream.seek(0)
        doc = docx.Document(stream)
        paragraphs: List[str] = []

        # Extract paragraphs
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                paragraphs.append(t)

        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    paragraphs.append(" | ".join(row_text))

        full_text = "\n\n".join(paragraphs)
        if not full_text.strip():
            logger.warning(f"No readable text extracted from DOCX '{file_name}'.")
            return []

        # DOCX format does not have deterministic physical pages without rendering engine;
        # We assign page 1 as standard baseline.
        return [
            Document(
                page_content=full_text,
                metadata={
                    "source": file_name,
                    "file_type": "docx",
                    "page": 1,
                    "total_pages": 1,
                },
            )
        ]

    @classmethod
    def _load_txt(cls, stream: io.BytesIO, file_name: str) -> List[Document]:
        """Extract text from plain text files with encoding fallbacks."""
        stream.seek(0)
        raw_bytes = stream.read()

        text = None
        for encoding in ("utf-8", "latin-1", "cp1252", "ascii"):
            try:
                text = raw_bytes.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        if text is None:
            raise UnicodeDecodeError("Could not decode file content with supported encodings.")

        cleaned = text.strip()
        if not cleaned:
            logger.warning(f"Empty text file '{file_name}'.")
            return []

        return [
            Document(
                page_content=cleaned,
                metadata={
                    "source": file_name,
                    "file_type": "txt",
                    "page": 1,
                    "total_pages": 1,
                },
            )
        ]
