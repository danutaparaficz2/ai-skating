"""Vektorspeicher für Chunk-Embeddings mit FAISS."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import faiss
import pickle
from pathlib import Path
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class VectorStore:
    """Verwaltet die Speicherung und Suche von Chunk-Embeddings mit FAISS."""

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str,
                 index_path: str = "./faiss_indexes", embedding_dimension: int = 768):
        """
        Initialisiert den FAISS-Vektorspeicher.

        Args:
            mongo_uri: MongoDB-Verbindungs-URI (für Metadaten)
            db_name: Datenbankname
            collection_name: Collection-Name für Metadaten
            index_path: Pfad zum Speichern der FAISS-Indizes
            embedding_dimension: Dimension der Embeddings (default: 768 für all-mpnet-base-v2)
        """
        # MongoDB für Metadaten
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.metadata_collection = self.db[collection_name + "_metadata"]

        # FAISS Setup
        self.embedding_dimension = embedding_dimension
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)

        # FAISS Index (Inner Product für cosine similarity bei normalisierten Vektoren)
        self.index = faiss.IndexFlatIP(embedding_dimension)

        # Mapping von FAISS-IDs zu Metadaten-IDs
        self.faiss_id_to_metadata_id = {}
        self.next_faiss_id = 0

        # Lade existierenden Index falls vorhanden
        self._load_index()

        logger.info(f"FAISS VectorStore initialisiert (Dimension: {embedding_dimension})")
        logger.info(f"Index-Pfad: {self.index_path}")
        logger.info(f"Aktuelle Vektoren im Index: {self.index.ntotal}")

    def _load_index(self):
        """Lädt existierende FAISS-Indizes und Metadaten."""
        index_file = self.index_path / "faiss.index"
        mapping_file = self.index_path / "id_mapping.pkl"

        if index_file.exists() and mapping_file.exists():
            try:
                # FAISS Index laden
                self.index = faiss.read_index(str(index_file))

                # ID-Mapping laden
                with open(mapping_file, 'rb') as f:
                    data = pickle.load(f)
                    self.faiss_id_to_metadata_id = data['mapping']
                    self.next_faiss_id = data['next_id']

                logger.info(f"FAISS Index geladen: {self.index.ntotal} Vektoren")
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Index: {e}. Erstelle neuen Index.")
                self.index = faiss.IndexFlatIP(self.embedding_dimension)
                self.faiss_id_to_metadata_id = {}
                self.next_faiss_id = 0
        else:
            logger.info("Kein existierender Index gefunden. Starte mit leerem Index.")

    def _save_index(self):
        """Speichert FAISS-Index und Metadaten persistent."""
        try:
            index_file = self.index_path / "faiss.index"
            mapping_file = self.index_path / "id_mapping.pkl"

            # FAISS Index speichern
            faiss.write_index(self.index, str(index_file))

            # ID-Mapping speichern
            with open(mapping_file, 'wb') as f:
                pickle.dump({
                    'mapping': self.faiss_id_to_metadata_id,
                    'next_id': self.next_faiss_id
                }, f)

            logger.debug(f"FAISS Index gespeichert: {self.index.ntotal} Vektoren")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Index: {e}")

    def index_chunks(self, chunks: List[Dict[str, Any]], skip_duplicates: bool = True) -> int:
        """
        Speichert Chunks im FAISS-Vektorspeicher.

        Args:
            chunks: Liste von Chunks mit Embeddings
            skip_duplicates: Ob Duplikate übersprungen werden sollen

        Returns:
            Anzahl der erfolgreich eingefügten Chunks
        """
        if not chunks:
            logger.warning("Keine Chunks zum Indexieren.")
            return 0

        now = datetime.utcnow()
        inserted_count = 0
        embeddings_to_add = []

        for chunk in chunks:
            # Prüfe auf Duplikate
            if skip_duplicates:
                duplicate_filter = {
                    "metadata.source_doc_id": chunk.get("metadata", {}).get("source_doc_id"),
                    "chunk_index": chunk.get("chunk_index")
                }
                if self.metadata_collection.find_one(duplicate_filter):
                    logger.debug(f"Chunk bereits vorhanden (Source: {chunk.get('metadata', {}).get('source_doc_id')}, Index: {chunk.get('chunk_index')})")
                    continue

            # Embedding extrahieren und normalisieren (für cosine similarity)
            embedding = np.array(chunk.get("embedding", []), dtype=np.float32)

            if len(embedding) == 0 or len(embedding) != self.embedding_dimension:
                logger.warning(f"Ungültiges Embedding (Dimension: {len(embedding)})")
                continue

            # Normalisiere für cosine similarity mit Inner Product
            faiss.normalize_L2(embedding.reshape(1, -1))

            # Speichere Metadaten in MongoDB
            metadata = {
                "faiss_id": self.next_faiss_id,
                "text": chunk.get("text"),
                "athlete_name": chunk.get("athlete_name"),
                "chunk_index": chunk.get("chunk_index"),
                "token_count": chunk.get("token_count"),
                "metadata": chunk.get("metadata", {}),
                "embedding_model": chunk.get("embedding_model"),
                "embedding_dimension": chunk.get("embedding_dimension"),
                "indexed_at": now
            }

            try:
                result = self.metadata_collection.insert_one(metadata)
                metadata_id = result.inserted_id

                # Füge zu FAISS hinzu
                embeddings_to_add.append(embedding)
                self.faiss_id_to_metadata_id[self.next_faiss_id] = str(metadata_id)
                self.next_faiss_id += 1
                inserted_count += 1

            except Exception as e:
                logger.error(f"Fehler beim Einfügen der Metadaten: {e}")

        # Batch-Add zu FAISS
        if embeddings_to_add:
            embeddings_array = np.vstack(embeddings_to_add)
            self.index.add(embeddings_array)

            # Index speichern
            self._save_index()

        logger.info(f"{inserted_count} von {len(chunks)} Chunks erfolgreich in FAISS indexiert.")
        logger.info(f"FAISS Index enthält jetzt {self.index.ntotal} Vektoren.")
        return inserted_count

    def get_indexed_doc_ids(self, athlete_name: str) -> set:
        """
        Gibt die IDs aller bereits indexierten Quelldokumente für einen Athleten zurück.

        Args:
            athlete_name: Name des Athleten

        Returns:
            Set von Dokument-IDs
        """
        pipeline = [
            {"$match": {"athlete_name": athlete_name}},
            {"$group": {"_id": "$metadata.source_doc_id"}}
        ]

        results = self.metadata_collection.aggregate(pipeline)
        doc_ids = {doc["_id"] for doc in results if doc["_id"]}

        logger.debug(f"{len(doc_ids)} bereits indexierte Dokumente für {athlete_name} gefunden.")
        return doc_ids

    def search_similar(self, query_embedding: np.ndarray, athlete_name: Optional[str] = None,
                       top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Sucht ähnliche Chunks mit FAISS basierend auf einem Query-Embedding.

        Args:
            query_embedding: Das Embedding der Suchanfrage
            athlete_name: Optional: Beschränke Suche auf bestimmten Athleten
            top_k: Anzahl der zurückzugebenden Ergebnisse

        Returns:
            Liste der ähnlichsten Chunks mit Similarity-Score
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS Index ist leer.")
            return []

        # Query-Embedding normalisieren
        query_vec = query_embedding.astype(np.float32).reshape(1, -1)
        faiss.normalize_L2(query_vec)

        # FAISS Suche durchführen
        # Bei athleten-spezifischer Suche: hole mehr Ergebnisse und filtere
        search_k = top_k * 10 if athlete_name else top_k
        search_k = min(search_k, self.index.ntotal)

        distances, indices = self.index.search(query_vec, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS gibt -1 zurück wenn nicht genug Ergebnisse
                continue

            # Hole Metadaten aus MongoDB
            metadata_id = self.faiss_id_to_metadata_id.get(int(idx))
            if not metadata_id:
                continue

            try:
                from bson.objectid import ObjectId
                metadata = self.metadata_collection.find_one({"_id": ObjectId(metadata_id)})
            except:
                metadata = self.metadata_collection.find_one({"_id": metadata_id})

            if not metadata:
                continue

            # Filter nach Athlet falls angegeben
            if athlete_name and metadata.get("athlete_name") != athlete_name:
                continue

            # Cosine similarity (da wir Inner Product mit normalisierten Vektoren verwenden)
            similarity = float(dist)

            results.append({
                "chunk": metadata,
                "similarity": similarity,
                "faiss_id": int(idx)
            })

            # Stoppe wenn genug Ergebnisse
            if len(results) >= top_k:
                break

        logger.debug(f"FAISS Suche: {len(results)} Ergebnisse gefunden")
        return results[:top_k]

    def get_stats(self, athlete_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Gibt Statistiken über den FAISS-Vektorspeicher zurück.

        Args:
            athlete_name: Optional: Statistiken nur für bestimmten Athleten

        Returns:
            Dictionary mit Statistiken
        """
        match_filter = {}
        if athlete_name:
            match_filter["athlete_name"] = athlete_name

        total_chunks = self.metadata_collection.count_documents(match_filter)

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": "$athlete_name",
                "count": {"$sum": 1}
            }}
        ]

        athletes_stats = list(self.metadata_collection.aggregate(pipeline))

        stats = {
            "total_chunks": total_chunks,
            "faiss_vectors": self.index.ntotal,
            "athletes": athletes_stats,
            "index_path": str(self.index_path),
            "embedding_dimension": self.embedding_dimension
        }

        if athlete_name:
            stats["athlete_name"] = athlete_name

        return stats

    def delete_athlete_chunks(self, athlete_name: str) -> int:
        """
        Löscht alle Chunks eines Athleten.

        HINWEIS: FAISS unterstützt kein effizientes Löschen einzelner Vektoren.
        Diese Methode löscht nur die Metadaten. Für vollständiges Löschen muss
        der Index neu aufgebaut werden.

        Args:
            athlete_name: Name des Athleten

        Returns:
            Anzahl der gelöschten Chunks (nur Metadaten)
        """
        result = self.metadata_collection.delete_many({"athlete_name": athlete_name})
        logger.warning(f"{result.deleted_count} Metadaten-Einträge für {athlete_name} gelöscht.")
        logger.warning("FAISS-Vektoren bleiben im Index. Für vollständige Löschung Index neu aufbauen.")
        return result.deleted_count

    def rebuild_index(self):
        """
        Baut den FAISS-Index komplett neu auf (z.B. nach Löschungen).
        Lädt alle Metadaten aus MongoDB und erstellt neuen Index.
        """
        logger.info("Baue FAISS-Index neu auf...")

        # Neuen Index erstellen
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.faiss_id_to_metadata_id = {}
        self.next_faiss_id = 0

        # Alle Metadaten laden
        all_metadata = list(self.metadata_collection.find())

        if not all_metadata:
            logger.info("Keine Metadaten gefunden. Index bleibt leer.")
            self._save_index()
            return

        # TODO: Embeddings müssten neu generiert oder separat gespeichert werden
        # Für jetzt nur Warnung
        logger.warning("Index-Rebuild benötigt gespeicherte Embeddings. Implementierung ausstehend.")
        self._save_index()

    def close(self):
        """Schließt die MongoDB-Verbindung und speichert den FAISS-Index."""
        self._save_index()
        self.mongo_client.close()
        logger.info("FAISS VectorStore geschlossen und Index gespeichert.")

