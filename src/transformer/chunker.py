"""Modul zum Aufteilen von Texten in Chunks für RAG."""

import logging
from typing import List, Dict, Any
import tiktoken
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Repräsentiert einen Text-Chunk mit Metadaten."""
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    token_count: int


class TextChunker:
    """Teilt Texte in überlappende Chunks auf."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, encoding_name: str = "cl100k_base"):
        """
        Initialisiert den TextChunker.

        Args:
            chunk_size: Maximale Anzahl Tokens pro Chunk
            chunk_overlap: Anzahl Tokens Überlappung zwischen Chunks
            encoding_name: Name des Tiktoken-Encodings (cl100k_base für GPT-4)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Konnte Encoding {encoding_name} nicht laden: {e}. Verwende cl100k_base.")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def _build_metadata_prefix(self, metadata: Dict[str, Any]) -> str:
        """
        Erstellt einen Metadaten-Prefix, der dem Chunk-Text vorangestellt wird.
        Dies verbessert die semantische Suche, da Metainformationen mit vektorisiert werden.

        Args:
            metadata: Dictionary mit Metainformationen

        Returns:
            Formatierter Metadaten-String
        """
        parts = []

        # Athletenname (wichtigste Information)
        if metadata.get("athlete_name"):
            parts.append(f"Athlete: {metadata['athlete_name']}")

        # Topic
        if metadata.get("topic"):
            parts.append(f"Topic: {metadata['topic']}")

        # Title
        if metadata.get("title"):
            parts.append(f"Title: {metadata['title']}")

        # Zusammenfügen mit Trennzeichen
        if parts:
            return " | ".join(parts) + "\n\n"
        return ""

    def count_tokens(self, text: str) -> int:
        """Zählt die Tokens in einem Text."""
        return len(self.encoding.encode(text))

    def split_text(self, text: str, metadata: Dict[str, Any], prepend_metadata: bool = True) -> List[TextChunk]:
        """
        Teilt einen Text in Chunks mit Überlappung auf.

        Args:
            text: Der zu teilende Text
            metadata: Metadaten für die Chunks
            prepend_metadata: Ob Metainformationen dem Text vorangestellt werden sollen

        Returns:
            Liste von TextChunk-Objekten
        """
        if not text or not text.strip():
            logger.warning("Leerer Text übergeben, keine Chunks erstellt.")
            return []

        # Optional: Metainformationen voranstellen für bessere semantische Suche
        if prepend_metadata:
            metadata_prefix = self._build_metadata_prefix(metadata)
            text = metadata_prefix + text

        # Text in Tokens konvertieren
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        if total_tokens <= self.chunk_size:
            # Text ist kurz genug, kein Splitting nötig
            return [TextChunk(
                text=text,
                metadata=metadata,
                chunk_index=0,
                token_count=total_tokens
            )]

        chunks = []
        chunk_index = 0
        start = 0

        while start < total_tokens:
            # Ende des aktuellen Chunks
            end = min(start + self.chunk_size, total_tokens)

            # Tokens für diesen Chunk extrahieren
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)

            # Chunk erstellen
            chunks.append(TextChunk(
                text=chunk_text,
                metadata={**metadata, "chunk_index": chunk_index},
                chunk_index=chunk_index,
                token_count=len(chunk_tokens)
            ))

            # Zum nächsten Chunk springen (mit Überlappung)
            start += self.chunk_size - self.chunk_overlap
            chunk_index += 1

        logger.debug(f"Text mit {total_tokens} Tokens in {len(chunks)} Chunks aufgeteilt.")
        return chunks

    def split_documents(self, documents: List[Dict[str, Any]], text_field: str = "markdown",
                       prepend_metadata: bool = True) -> List[TextChunk]:
        """
        Teilt mehrere Dokumente in Chunks auf.

        Args:
            documents: Liste von Dokumenten aus MongoDB
            text_field: Name des Feldes, das den Text enthält
            prepend_metadata: Ob Metainformationen dem Text vorangestellt werden sollen

        Returns:
            Liste aller TextChunks
        """
        all_chunks = []

        for doc in documents:
            text = doc.get(text_field, "")

            if not text:
                # Fallback auf andere mögliche Textfelder
                text = doc.get("text", doc.get("content", ""))

            if not text:
                logger.warning(f"Dokument {doc.get('_id')} hat kein Textfeld '{text_field}'")
                continue

            # Metadaten aus Dokument extrahieren
            metadata = {
                "source_doc_id": str(doc.get("_id")),
                "athlete_name": doc.get("athlete_name"),
                "topic": doc.get("topic"),
                "url": doc.get("url"),
                "title": doc.get("title"),
                "scraped_at": doc.get("scraped_at"),
                "created_at": doc.get("created_at")
            }

            # Text in Chunks aufteilen (mit optionalem Metadaten-Prefix)
            chunks = self.split_text(text, metadata, prepend_metadata=prepend_metadata)
            all_chunks.extend(chunks)

        logger.info(f"{len(documents)} Dokumente in {len(all_chunks)} Chunks aufgeteilt.")
        return all_chunks

