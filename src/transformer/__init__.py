"""RAG-Indexierungs-Pipeline für Athletendaten.

Dieses Modul bietet eine vollständige Pipeline zur Indexierung von
Athletendokumenten für Retrieval-Augmented Generation (RAG).

Hauptkomponenten:
- AthleteIndexingPipeline: Hauptklasse für die Indexierung
- TextChunker: Teilt Texte in überlappende Chunks
- EmbeddingGenerator: Erzeugt Embeddings mit Sentence Transformers
- VectorStore: Speichert und durchsucht Chunk-Embeddings
- IndexingConfig: Konfigurationsparameter

Verwendung:
    from transformer import AthleteIndexingPipeline, IndexingConfig

    # Pipeline initialisieren
    pipeline = AthleteIndexingPipeline()

    # Athleten indexieren
    stats = pipeline.process_athlete_indexing("John Doe", since_days=30)

    # Suche durchführen
    results = pipeline.search("recent competitions", athlete_name="John Doe", top_k=5)
"""

from .config import IndexingConfig
from .pipeline import AthleteIndexingPipeline
from .chunker import TextChunker, TextChunk
from .embedder import EmbeddingGenerator
from .vector_store import VectorStore

__all__ = [
    'AthleteIndexingPipeline',
    'IndexingConfig',
    'TextChunker',
    'TextChunk',
    'EmbeddingGenerator',
    'VectorStore'
]

__version__ = '1.0.0'

