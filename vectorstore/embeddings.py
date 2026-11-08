import logging
import torch
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
import config

logger = logging.getLogger(__name__)

_EMBEDDINGS_INSTANCE: Optional[HuggingFaceEmbeddings] = None


def get_embedding_function(model_name: Optional[str] = None) -> HuggingFaceEmbeddings:
    """
    Get or initialize the HuggingFace embedding function singleton.
    Utilizes Apple Silicon MPS if available, otherwise CPU.
    """
    global _EMBEDDINGS_INSTANCE
    target_model = model_name or config.EMBEDDING_MODEL_NAME

    if _EMBEDDINGS_INSTANCE is not None:
        return _EMBEDDINGS_INSTANCE

    # Determine optimal compute device
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    logger.info(f"Loading HuggingFace embedding model: '{target_model}' on device: '{device}'")

    _EMBEDDINGS_INSTANCE = HuggingFaceEmbeddings(
        model_name=target_model,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("HuggingFace embedding model successfully loaded.")
    return _EMBEDDINGS_INSTANCE
