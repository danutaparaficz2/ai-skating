"""Konfiguration für den RAG-Generator."""

import os
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Konfiguration für RAG-Generator."""

    # FAISS Index
    faiss_index_path: str = field(
        default_factory=lambda: os.getenv(
            "FAISS_INDEX_PATH",
            "/Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/transformer/faiss_indexes"
        )
    )


    # Embedding Model
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-mpnet-base-v2"
        )
    )

    # MongoDB (für Metadaten)
    mongo_uri: str = field(
        default_factory=lambda: os.getenv("MONGO_URI", "mongodb://localhost:27017")
    )
    mongo_db: str = field(
        default_factory=lambda: os.getenv("MONGO_DB", "crawler")
    )
    mongo_collection: str = field(
        default_factory=lambda: os.getenv("MONGO_COLLECTION", "athlete_chunks_embeddings")
    )

    # Qwen/Alibaba Cloud LLM
    qwen_api_key: str = field(
        default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", "")
    )
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen3-max"  # FEST - nur qwen3-max erlaubt

    # RAG Parameter
    top_k_chunks: int = field(
        default_factory=lambda: int(os.getenv("TOP_K_CHUNKS", "5"))
    )
    min_similarity: float = field(
        default_factory=lambda: float(os.getenv("MIN_SIMILARITY", "0.3"))
    )

    # LLM Generation Parameter
    temperature: float = field(
        default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS", "1000"))
    )

    # System Prompt
    system_prompt: str = field(
        default_factory=lambda: os.getenv(
            "SYSTEM_PROMPT",
            "Du bist ein hilfreicher Assistent für Short-Track Eisschnelllauf-Informationen. "
            "Beantworte Fragen präzise und basierend auf den bereitgestellten Informationen."
        )
    )

    def validate(self):
        """Validiert die Konfiguration."""
        if not self.qwen_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY muss gesetzt sein. "
                "Setze Umgebungsvariable: export DASHSCOPE_API_KEY='your-key'"
            )

        if not os.path.exists(self.faiss_index_path):
            logger.warning(
                f"FAISS Index Pfad existiert nicht: {self.faiss_index_path}"
            )

        logger.info("Generator-Konfiguration validiert")
        logger.info(f"  - FAISS Index: {self.faiss_index_path}")
        logger.info(f"  - Qwen Model: {self.qwen_model}")
        logger.info(f"  - Top K Chunks: {self.top_k_chunks}")

