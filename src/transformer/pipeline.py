"""Hauptpipeline für RAG-Indexierung von Athletendaten."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient

from .config import IndexingConfig
from .chunker import TextChunker, TextChunk
from .embedder import EmbeddingGenerator
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class AthleteIndexingPipeline:
    """Pipeline für die Indexierung von Athletendokumenten für RAG."""

    def __init__(self, config: Optional[IndexingConfig] = None):
        """
        Initialisiert die Indexierungs-Pipeline.

        Args:
            config: Konfigurationsobjekt (optional, verwendet Defaults wenn None)
        """
        self.config = config or IndexingConfig()

        # Logging konfigurieren
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # MongoDB-Verbindung für Rohdaten
        self.mongo_client = MongoClient(self.config.mongo_uri)
        self.source_collection = self.mongo_client[self.config.mongo_db][self.config.mongo_collection]

        # Komponenten initialisieren
        self.chunker = TextChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )

        self.embedder = EmbeddingGenerator(
            model_name=self.config.embedding_model
        )

        self.vector_store = VectorStore(
            mongo_uri=self.config.mongo_uri,
            db_name=self.config.mongo_db,
            collection_name=self.config.mongo_chunks_collection,
            index_path=self.config.faiss_index_path,
            embedding_dimension=self.config.vector_dimension
        )

        logger.info("AthleteIndexingPipeline initialisiert.")

    def fetch_documents(self, athlete_name: str, since_days: Optional[int] = None,
                       skip_indexed: bool = True) -> List[Dict[str, Any]]:
        """
        Lädt Dokumente für einen Athleten aus der MongoDB.

        Verarbeitet die verschachtelte Struktur:
        {
            "athlete_name": "...",
            "topic": "...",
            "web": [
                {
                    "markdown": "...",
                    "html": "...",
                    "metadata": {
                        "sourceURL": "...",
                        "statusCode": ...
                    }
                }
            ]
        }

        Args:
            athlete_name: Name des Athleten
            since_days: Nur Dokumente der letzten X Tage (None = alle)
            skip_indexed: Ob bereits indexierte Dokumente übersprungen werden sollen

        Returns:
            Liste von verarbeiteten Dokumenten (flache Struktur)
        """
        logger.info(f"Lade Dokumente für Athlet: {athlete_name}")

        # Query erstellen - NUR nach Athletenname filtern (MVP ohne Zeitfilter)
        query = {"athlete_name": athlete_name}

        logger.info(f"MongoDB Query: {query}")

        # Dokumente aus MongoDB abrufen
        raw_documents = list(self.source_collection.find(query))

        logger.info(f"✅ {len(raw_documents)} MongoDB-Dokumente gefunden")

        if not raw_documents:
            logger.warning(f"⚠️  Keine Dokumente für '{athlete_name}' in MongoDB gefunden!")
            return []

        # Verarbeite die verschachtelte web-Array-Struktur
        processed_documents = []

        for doc in raw_documents:
            athlete = doc.get("athlete_name", "Unknown")
            topic = doc.get("topic", "unknown")
            web_items = doc.get("web", [])

            if not web_items:
                logger.debug(f"Dokument {doc.get('_id')} hat kein 'web'-Array, überspringe")
                continue

            # Extrahiere jeden Eintrag aus dem web-Array
            for idx, web_item in enumerate(web_items):
                # Bevorzuge markdown, fallback auf html oder rawHtml
                text = (web_item.get("markdown") or
                       web_item.get("html") or
                       web_item.get("rawHtml", ""))

                if not text or len(text.strip()) < 100:
                    logger.debug(f"Leerer/zu kurzer Text in web[{idx}], überspringe")
                    continue

                metadata = web_item.get("metadata", {})

                # Erstelle flaches Dokument für weitere Verarbeitung
                processed_doc = {
                    "_id": f"{doc.get('_id')}_{idx}",  # Eindeutige ID
                    "markdown": text,  # Verwende "markdown" als Standard-Textfeld
                    "athlete_name": athlete,
                    "topic": topic,
                    "url": metadata.get("sourceURL", ""),
                    "title": metadata.get("title", ""),
                    "status_code": metadata.get("statusCode"),
                    "scraped_at": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                    "web_index": idx,
                    "original_doc_id": str(doc.get("_id"))
                }

                processed_documents.append(processed_doc)

        logger.info(f"📄 {len(processed_documents)} Textabschnitte aus {len(raw_documents)} Dokumenten extrahiert")

        # Bereits indexierte ausschließen (basierend auf verarbeiteten IDs)
        if skip_indexed:
            indexed_doc_ids = self.vector_store.get_indexed_doc_ids(athlete_name)
            if indexed_doc_ids:
                before_count = len(processed_documents)
                processed_documents = [
                    doc for doc in processed_documents
                    if doc["_id"] not in indexed_doc_ids
                ]
                filtered_count = before_count - len(processed_documents)
                logger.info(f"{filtered_count} bereits indexierte Textabschnitte übersprungen")

        logger.info(f"✅ {len(processed_documents)} neue Textabschnitte für {athlete_name} bereit")
        return processed_documents


    def split_into_chunks(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Teilt Dokumente in Chunks auf.

        Args:
            documents: Liste von Dokumenten

        Returns:
            Liste von Chunk-Dictionaries
        """
        logger.info(f"Teile {len(documents)} Dokumente in Chunks auf...")

        # Chunker verwenden (mit Metadaten-Prefix wenn konfiguriert)
        text_chunks: List[TextChunk] = self.chunker.split_documents(
            documents,
            prepend_metadata=self.config.prepend_metadata_to_chunks
        )

        # TextChunk-Objekte in Dictionaries konvertieren
        chunk_dicts = []
        for chunk in text_chunks:
            chunk_dict = {
                "text": chunk.text,
                "metadata": chunk.metadata,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "athlete_name": chunk.metadata.get("athlete_name")
            }
            chunk_dicts.append(chunk_dict)

        logger.info(f"{len(chunk_dicts)} Chunks erstellt.")
        return chunk_dicts

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Erzeugt Embeddings für Chunks.

        Args:
            chunks: Liste von Chunks

        Returns:
            Liste von Chunks mit Embeddings
        """
        logger.info(f"Erzeuge Embeddings für {len(chunks)} Chunks...")

        enriched_chunks = self.embedder.embed_chunks(
            chunks,
            text_key="text",
            batch_size=self.config.batch_size
        )

        logger.info(f"Embeddings für {len(enriched_chunks)} Chunks erstellt.")
        return enriched_chunks

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Speichert Chunks im Vektorspeicher.

        Args:
            chunks: Liste von Chunks mit Embeddings

        Returns:
            Anzahl der indexierten Chunks
        """
        logger.info(f"Indexiere {len(chunks)} Chunks...")

        indexed_count = self.vector_store.index_chunks(chunks, skip_duplicates=True)

        logger.info(f"{indexed_count} Chunks erfolgreich indexiert.")
        return indexed_count

    def process_athlete_indexing(self, athlete_name: str, since_days: Optional[int] = None,
                                 skip_indexed: bool = True) -> Dict[str, Any]:
        """
        Vollständiger Indexierungsprozess für einen Athleten.

        Args:
            athlete_name: Name des Athleten
            since_days: Nur Dokumente der letzten X Tage (None = alle)
            skip_indexed: Ob bereits indexierte Dokumente übersprungen werden sollen

        Returns:
            Dictionary mit Statistiken über den Prozess
        """
        logger.info(f"=== Starte Indexierung für Athlet: {athlete_name} ===")

        start_time = datetime.utcnow()

        # Schritt 1: Dokumente laden (KEIN Zeitfilter für MVP)
        documents = self.fetch_documents(
            athlete_name=athlete_name,
            since_days=None,  # Immer ALLE Dokumente laden
            skip_indexed=skip_indexed
        )

        if not documents:
            logger.info(f"Keine neuen Dokumente für {athlete_name} gefunden. Indexierung abgebrochen.")
            return {
                "athlete_name": athlete_name,
                "documents_loaded": 0,
                "chunks_created": 0,
                "chunks_indexed": 0,
                "duration_seconds": 0,
                "status": "no_new_documents"
            }

        # Schritt 2: In Chunks aufteilen
        chunks = self.split_into_chunks(documents)

        if not chunks:
            logger.warning(f"Keine Chunks für {athlete_name} erstellt.")
            return {
                "athlete_name": athlete_name,
                "documents_loaded": len(documents),
                "chunks_created": 0,
                "chunks_indexed": 0,
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                "status": "no_chunks_created"
            }

        # Schritt 3: Embeddings erzeugen
        enriched_chunks = self.embed_chunks(chunks)

        # Schritt 4: Chunks indexieren
        indexed_count = self.index_chunks(enriched_chunks)

        # Statistiken
        duration = (datetime.utcnow() - start_time).total_seconds()

        stats = {
            "athlete_name": athlete_name,
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "chunks_indexed": indexed_count,
            "duration_seconds": duration,
            "status": "success"
        }

        logger.info(f"=== Indexierung abgeschlossen für {athlete_name} ===")
        logger.info(f"Zusammenfassung: {stats}")

        return stats

    def process_all_athletes(self, athlete_names: List[str], since_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Indexiert Dokumente für mehrere Athleten.

        Args:
            athlete_names: Liste von Athletennamen
            since_days: Nur Dokumente der letzten X Tage

        Returns:
            Liste von Statistik-Dictionaries pro Athlet
        """
        logger.info(f"=== Starte Batch-Indexierung für {len(athlete_names)} Athleten ===")

        results = []
        for athlete_name in athlete_names:
            try:
                stats = self.process_athlete_indexing(
                    athlete_name=athlete_name,
                    since_days=since_days
                )
                results.append(stats)
            except Exception as e:
                logger.error(f"Fehler bei Indexierung von {athlete_name}: {e}", exc_info=True)
                results.append({
                    "athlete_name": athlete_name,
                    "status": "error",
                    "error": str(e)
                })

        # Gesamtstatistik
        total_docs = sum(r.get("documents_loaded", 0) for r in results)
        total_chunks = sum(r.get("chunks_indexed", 0) for r in results)

        logger.info(f"=== Batch-Indexierung abgeschlossen ===")
        logger.info(f"Gesamt: {len(athlete_names)} Athleten, {total_docs} Dokumente, {total_chunks} Chunks indexiert")

        return results

    def get_vector_store_stats(self, athlete_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Gibt Statistiken über den Vektorspeicher zurück.

        Args:
            athlete_name: Optional: nur für bestimmten Athleten

        Returns:
            Statistik-Dictionary
        """
        return self.vector_store.get_stats(athlete_name=athlete_name)

    def search(self, query: str, athlete_name: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Führt eine semantische Suche durch.

        Args:
            query: Suchanfrage
            athlete_name: Optional: Beschränke auf bestimmten Athleten
            top_k: Anzahl Ergebnisse

        Returns:
            Liste der ähnlichsten Chunks
        """
        logger.info(f"Suche nach: '{query}' (Athlet: {athlete_name or 'alle'})")

        # Query-Embedding erzeugen
        query_embedding = self.embedder.embed_text(query)

        # Suche durchführen
        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            athlete_name=athlete_name,
            top_k=top_k
        )

        logger.info(f"{len(results)} Ergebnisse gefunden.")
        return results

    def close(self):
        """Schließt alle Verbindungen."""
        self.mongo_client.close()
        self.vector_store.close()
        logger.info("Pipeline geschlossen.")

