"""Modul zur Erzeugung von Embeddings für Text-Chunks."""

import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Erzeugt Embeddings für Text-Chunks."""

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialisiert den Embedding-Generator.

        Args:
            model_name: Name des Sentence-Transformer-Modells
        """
        self.model_name = model_name
        logger.info(f"Lade Embedding-Modell: {model_name}")

        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Modell geladen. Embedding-Dimension: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Fehler beim Laden des Modells: {e}")
            raise

    def embed_text(self, text: str) -> np.ndarray:
        """
        Erzeugt ein Embedding für einen einzelnen Text.

        Args:
            text: Der Text

        Returns:
            Embedding-Vektor als numpy array
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[np.ndarray]:
        """
        Erzeugt Embeddings für eine Liste von Texten.

        Args:
            texts: Liste von Texten
            batch_size: Batch-Größe für die Verarbeitung
            show_progress: Ob ein Fortschrittsbalken angezeigt werden soll

        Returns:
            Liste von Embedding-Vektoren
        """
        if not texts:
            return []

        logger.info(f"Erzeuge Embeddings für {len(texts)} Texte...")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )

        logger.info(f"{len(embeddings)} Embeddings erfolgreich erzeugt.")
        return embeddings

    def embed_chunks(self, chunks: List[Dict[str, Any]], text_key: str = "text",
                     batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Erzeugt Embeddings für eine Liste von Chunks und fügt sie hinzu.

        Args:
            chunks: Liste von Chunk-Dictionaries
            text_key: Schlüssel für den Text im Dictionary
            batch_size: Batch-Größe

        Returns:
            Liste von Chunks mit hinzugefügtem 'embedding' Feld
        """
        if not chunks:
            logger.warning("Keine Chunks zum Embedden übergeben.")
            return []

        # Texte extrahieren
        texts = [chunk.get(text_key, "") for chunk in chunks]

        # Embeddings erzeugen
        embeddings = self.embed_batch(texts, batch_size=batch_size)

        # Embeddings zu Chunks hinzufügen
        enriched_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_copy = chunk.copy()
            chunk_copy["embedding"] = embedding.tolist()  # Konvertiere zu Liste für MongoDB
            chunk_copy["embedding_model"] = self.model_name
            chunk_copy["embedding_dimension"] = self.embedding_dimension
            enriched_chunks.append(chunk_copy)

        return enriched_chunks

