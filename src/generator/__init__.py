"""RAG Generator für Athleten-Stories und Q&A mit Alibaba Cloud."""

from .config import GeneratorConfig
from .retriever import FAISSRetriever
from .llm_client import QwenClient
from .rag_generator import RAGGenerator

__all__ = [
    'GeneratorConfig',
    'FAISSRetriever',
    'QwenClient',
    'RAGGenerator',
]


__version__ = '1.0.0'

