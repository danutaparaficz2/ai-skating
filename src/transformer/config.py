"""Konfiguration für die RAG-Indexierungs-Pipeline."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class IndexingConfig:
    """Konfiguration für den Indexierungsprozess."""

    # MongoDB Verbindung (für Metadaten)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "crawler"
    mongo_collection: str = "firecrawl_results"
    mongo_chunks_collection: str = "athlete_chunks_embeddings"

    # FAISS Vektorspeicher
    faiss_index_path: str = "./faiss_indexes"
    vector_dimension: int = 768  # Dimension für all-mpnet-base-v2

    # Chunking Parameter
    chunk_size: int = 1000  # Anzahl Tokens pro Chunk
    chunk_overlap: int = 200  # Überlappung in Tokens
    prepend_metadata_to_chunks: bool = True  # Metainformationen dem Chunk-Text voranstellen

    # Embedding Modell
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"

    # Zeitfenster
    default_since_days: int = 30

    # Batch-Verarbeitung
    batch_size: int = 32  # Für Embedding-Generierung

    # Logging
    log_level: str = "INFO"

