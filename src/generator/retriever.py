"""Retriever für semantische Suche in FAISS-Index."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class FAISSRetriever:
    """Retriever für semantische Suche in FAISS-Index mit MongoDB-Metadaten."""

    def __init__(
        self,
        faiss_index_path: str,
        mongo_uri: str = "mongodb://localhost:27017",
        mongo_db: str = "crawler",
        mongo_collection: str = "athlete_chunks_embeddings",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    ):
        """
        Initialisiert den FAISS Retriever.

        Args:
            faiss_index_path: Pfad zum FAISS-Index-Ordner
            mongo_uri: MongoDB-Verbindungs-URI
            mongo_db: Datenbankname
            mongo_collection: Collection-Name (ohne _metadata Suffix)
            embedding_model: Embedding-Modell (muss gleich sein wie bei Indexierung!)
        """
        self.index_path = Path(faiss_index_path)

        # MongoDB-Verbindung für Metadaten
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[mongo_db]
        self.metadata_collection = self.db[mongo_collection + "_metadata"]

        # Lade FAISS-Index und ID-Mapping
        self._load_faiss_index()

        # Embedding-Modell (für Query-Embeddings)
        logger.info(f"Lade Embedding-Modell: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)

        logger.info(f"FAISS Retriever initialisiert mit {self.index.ntotal} Vektoren")

    def _load_faiss_index(self):
        """Lädt den FAISS-Index und ID-Mapping."""
        index_file = self.index_path / "faiss.index"
        mapping_file = self.index_path / "id_mapping.pkl"

        if not index_file.exists():
            raise FileNotFoundError(f"FAISS-Index nicht gefunden: {index_file}")

        # FAISS Index laden
        self.index = faiss.read_index(str(index_file))
        logger.info(f"FAISS-Index geladen: {self.index.ntotal} Vektoren")

        # ID-Mapping laden
        if mapping_file.exists():
            with open(mapping_file, 'rb') as f:
                data = pickle.load(f)
                self.faiss_id_to_metadata_id = data.get('mapping', {})
            logger.info(f"ID-Mapping geladen: {len(self.faiss_id_to_metadata_id)} Einträge")
        else:
            raise FileNotFoundError(f"ID-Mapping nicht gefunden: {mapping_file}")

    def retrieve(
        self,
        query: str,
        athlete_name: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Sucht ähnliche Chunks für eine Query.

        Args:
            query: Suchanfrage
            athlete_name: Optional: Filter auf bestimmten Athleten
            top_k: Anzahl Ergebnisse
            min_similarity: Minimale Ähnlichkeit (0-1)

        Returns:
            Liste von Chunks mit Similarity-Scores
        """
        logger.info(f"Suche für Query: '{query[:50]}...'")

        # 1. Erstelle Query-Embedding
        query_embedding = self.embedder.encode(query, convert_to_numpy=True)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')

        # Normalisiere für Cosine Similarity
        faiss.normalize_L2(query_embedding)

        # 2. FAISS-Suche (hole mehr als top_k wenn Athlet-Filter aktiv)
        search_k = top_k * 10 if athlete_name else top_k
        similarities, indices = self.index.search(query_embedding, search_k)

        # 3. Hole Metadaten aus MongoDB
        results = []
        for idx, similarity in zip(indices[0], similarities[0]):
            if similarity < min_similarity:
                continue

            # Hole Metadaten aus MongoDB
            metadata_id = self.faiss_id_to_metadata_id.get(int(idx))
            if not metadata_id:
                logger.warning(f"Keine Metadaten-ID für FAISS-ID {idx}")
                continue

            try:
                metadata = self.metadata_collection.find_one({"_id": ObjectId(metadata_id)})
                if not metadata:
                    logger.warning(f"Metadaten nicht gefunden: {metadata_id}")
                    continue

                # Athlet-Filter
                if athlete_name and metadata.get('athlete_name') != athlete_name:
                    continue

                results.append({
                    "text": metadata.get("text", ""),
                    "athlete_name": metadata.get("athlete_name"),
                    "similarity": float(similarity),
                    "metadata": {
                        "topic": metadata.get("metadata", {}).get("topic"),
                        "url": metadata.get("metadata", {}).get("url"),
                        "title": metadata.get("metadata", {}).get("title"),
                        "source_doc_id": metadata.get("metadata", {}).get("source_doc_id")
                    }
                })

                # Stoppe wenn genug Ergebnisse
                if len(results) >= top_k:
                    break

            except Exception as e:
                logger.error(f"Fehler beim Laden der Metadaten: {e}")
                continue

        logger.info(f"{len(results)} relevante Chunks gefunden")
        return results

    def close(self):
        """Schließt MongoDB-Verbindung."""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
            logger.info("MongoDB-Verbindung geschlossen")

