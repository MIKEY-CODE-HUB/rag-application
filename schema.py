from typing import Dict, Any, Optional

class Document:
    """Represents an extracted unit of text with associated metadata."""
    def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"Document(source={self.metadata.get('source')}, page={self.metadata.get('page')}, length={len(self.page_content)})"
