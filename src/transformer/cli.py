#!/usr/bin/env python3
"""Command-line Interface für die RAG-Indexierungs-Pipeline."""

import argparse
import logging
import json
import sys
import os
from typing import Optional

# Füge das parent-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformer import AthleteIndexingPipeline, IndexingConfig
from pathlib import Path
import shutil


def setup_logging(verbose: bool = False):
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def index_athlete(args):
    """Indexiert einen einzelnen Athleten."""
    config = IndexingConfig(
        mongo_uri=args.mongo_uri,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedding_model=args.embedding_model,
        faiss_index_path=args.faiss_path
    )

    pipeline = AthleteIndexingPipeline(config)

    try:
        stats = pipeline.process_athlete_indexing(
            athlete_name=args.athlete_name,
            since_days=args.since_days,
            skip_indexed=not args.reindex
        )

        print("\n" + "="*60)
        print(f"✅ Indexierung abgeschlossen: {args.athlete_name}")
        print("="*60)
        print(f"📄 Dokumente geladen:  {stats.get('documents_loaded', 0)}")
        print(f"📦 Chunks erstellt:    {stats.get('chunks_created', 0)}")
        print(f"💾 Chunks indexiert:   {stats.get('chunks_indexed', 0)}")
        print(f"⏱️  Dauer:              {stats.get('duration_seconds', 0):.2f}s")
        print(f"✨ Status:             {stats.get('status', 'unknown')}")
        print("="*60)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            print(f"\n💾 Statistiken gespeichert in: {args.output}")

    finally:
        pipeline.close()


def index_batch(args):
    """Indexiert mehrere Athleten aus einer Datei."""
    # Athletennamen aus Datei laden
    with open(args.file, 'r') as f:
        data = json.load(f)
        # Unterstütze sowohl athletes_old.json Format als auch einfache Liste
        if isinstance(data, list):
            if data and isinstance(data[0], dict) and 'name' in data[0]:
                athlete_names = [athlete['name'] for athlete in data]
            else:
                athlete_names = data
        else:
            athlete_names = [line.strip() for line in f if line.strip()]

    print(f"📋 Lade {len(athlete_names)} Athletennamen aus {args.file}")

    config = IndexingConfig(
        mongo_uri=args.mongo_uri,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedding_model=args.embedding_model,
        faiss_index_path=args.faiss_path
    )

    pipeline = AthleteIndexingPipeline(config)

    try:
        results = pipeline.process_all_athletes(
            athlete_names=athlete_names,
            since_days=args.since_days
        )

        # Zusammenfassung
        total_docs = sum(r.get('documents_loaded', 0) for r in results)
        total_chunks = sum(r.get('chunks_indexed', 0) for r in results)
        success_count = sum(1 for r in results if r.get('status') == 'success')

        print("\n" + "="*60)
        print("✅ Batch-Indexierung abgeschlossen")
        print("="*60)
        print(f"👥 Athleten verarbeitet: {len(athlete_names)}")
        print(f"✨ Erfolgreich:          {success_count}")
        print(f"📄 Dokumente geladen:    {total_docs}")
        print(f"💾 Chunks indexiert:     {total_chunks}")
        print("="*60)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Ergebnisse gespeichert in: {args.output}")

    finally:
        pipeline.close()


def search(args):
    """Führt eine semantische Suche durch."""
    config = IndexingConfig(
        mongo_uri=args.mongo_uri,
        embedding_model=args.embedding_model,
        faiss_index_path=args.faiss_path
    )

    pipeline = AthleteIndexingPipeline(config)

    try:
        results = pipeline.search(
            query=args.query,
            athlete_name=args.athlete_name,
            top_k=args.top_k
        )

        print("\n" + "="*60)
        print(f"🔍 Suchergebnisse für: '{args.query}'")
        if args.athlete_name:
            print(f"🏃 Athlet: {args.athlete_name}")
        print("="*60 + "\n")

        if not results:
            print("❌ Keine Ergebnisse gefunden.")
        else:
            for i, result in enumerate(results, 1):
                chunk = result['chunk']
                similarity = result['similarity']
                metadata = chunk.get('metadata', {})

                print(f"#{i} - Ähnlichkeit: {similarity:.4f}")
                print(f"   🏃 Athlet:  {chunk.get('athlete_name', 'N/A')}")
                print(f"   📰 Titel:   {metadata.get('title', 'N/A')}")
                print(f"   🏷️  Topic:   {metadata.get('topic', 'N/A')}")
                print(f"   🔗 URL:     {metadata.get('url', 'N/A')}")

                text = chunk.get('text', '')
                preview = text[:300] + "..." if len(text) > 300 else text
                print(f"   📝 Text:    {preview}")
                print()

        if args.output:
            output_data = [
                {
                    'similarity': r['similarity'],
                    'athlete_name': r['chunk'].get('athlete_name'),
                    'title': r['chunk'].get('metadata', {}).get('title'),
                    'text': r['chunk'].get('text')
                }
                for r in results
            ]
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Ergebnisse gespeichert in: {args.output}")

    finally:
        pipeline.close()


def stats(args):
    """Zeigt Statistiken über den Vektorspeicher."""
    config = IndexingConfig(
        mongo_uri=args.mongo_uri,
        faiss_index_path=args.faiss_path
    )
    pipeline = AthleteIndexingPipeline(config)

    try:
        stats_data = pipeline.get_vector_store_stats(athlete_name=args.athlete_name)

        print("\n" + "="*60)
        print("📊 FAISS Vektorspeicher-Statistiken")
        print("="*60)

        if args.athlete_name:
            print(f"🏃 Athlet: {args.athlete_name}")

        print(f"💾 Gesamt-Chunks:      {stats_data.get('total_chunks', 0)}")
        print(f"🔢 FAISS-Vektoren:     {stats_data.get('faiss_vectors', 0)}")
        print(f"📏 Embedding-Dim:      {stats_data.get('embedding_dimension', 768)}")
        print(f"📂 Index-Pfad:         {stats_data.get('index_path', 'N/A')}")

        athletes = stats_data.get('athletes', [])
        if athletes:
            print(f"\n👥 Chunks pro Athlet:")
            for athlete_info in sorted(athletes, key=lambda x: x.get('count', 0), reverse=True):
                name = athlete_info.get('_id', 'Unbekannt')
                count = athlete_info.get('count', 0)
                print(f"   - {name}: {count}")

        print("="*60)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(stats_data, f, indent=2, default=str)
            print(f"\n💾 Statistiken gespeichert in: {args.output}")

    finally:
        pipeline.close()


def clear_index(args):
    """Löscht alle FAISS-Indizes und Metadaten."""
    config = IndexingConfig(
        mongo_uri=args.mongo_uri,
        faiss_index_path=args.faiss_path
    )

    if not args.yes:
        print("⚠️  WARNUNG: Dies löscht alle FAISS-Indizes und Metadaten!")
        confirm = input("Möchten Sie fortfahren? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Abgebrochen.")
            return

    # Lösche FAISS-Dateien
    index_path = Path(config.faiss_index_path)
    if index_path.exists():
        try:
            shutil.rmtree(index_path)
            print(f"✅ FAISS-Index gelöscht: {index_path}")
        except Exception as e:
            print(f"❌ Fehler beim Löschen des FAISS-Index: {e}")

    # Lösche MongoDB-Metadaten-Collection
    try:
        from pymongo import MongoClient
        client = MongoClient(config.mongo_uri)
        db = client[config.mongo_db]
        collection = db[config.mongo_chunks_collection + "_metadata"]
        result = collection.delete_many({})
        print(f"✅ MongoDB-Metadaten gelöscht: {result.deleted_count} Dokumente")
        client.close()
    except Exception as e:
        print(f"❌ Fehler beim Löschen der MongoDB-Metadaten: {e}")

    print("\n" + "="*60)
    print("✅ Index erfolgreich geleert!")
    print("="*60)


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description='RAG-Indexierungs-Pipeline für Athletendaten',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einzelnen Athleten indexieren
  %(prog)s index "Yuzuru Hanyu" --since-days 30
  
  # Mehrere Athleten indexieren
  %(prog)s batch ../crawler/athletes_old.json --since-days 30
  
  # Suche durchführen
  %(prog)s search "Olympic gold medal" --athlete "Yuzuru Hanyu" --top-k 5
  
  # Statistiken anzeigen
  %(prog)s stats --athlete "Yuzuru Hanyu"
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose logging (DEBUG level)')
    parser.add_argument('--mongo-uri', default='mongodb://localhost:27017',
                       help='MongoDB Connection URI (default: mongodb://localhost:27017)')
    parser.add_argument('--faiss-path', default='./faiss_indexes',
                       help='Pfad für FAISS-Indizes (default: ./faiss_indexes)')

    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')

    # Index command
    index_parser = subparsers.add_parser('index', help='Indexiert einen einzelnen Athleten')
    index_parser.add_argument('athlete_name', help='Name des Athleten')
    index_parser.add_argument('--since-days', type=int, default=30,
                             help='Nur Dokumente der letzten X Tage (default: 30)')
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Löscht alle FAISS-Indizes und Metadaten')
    clear_parser.add_argument('--yes', action='store_true',
                             help='Bestätigung überspringen')

    index_parser.add_argument('--reindex', action='store_true',
                             help='Re-indexiere bereits indexierte Dokumente')
    index_parser.add_argument('--chunk-size', type=int, default=1000,
                             help='Chunk-Größe in Tokens (default: 1000)')
    index_parser.add_argument('--chunk-overlap', type=int, default=200,
                             help='Chunk-Überlappung in Tokens (default: 200)')
    index_parser.add_argument('--embedding-model', default='sentence-transformers/all-mpnet-base-v2',
                             help='Embedding-Modell (default: all-mpnet-base-v2)')
    index_parser.add_argument('-o', '--output', help='Speichere Statistiken in JSON-Datei')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Indexiert mehrere Athleten')
    batch_parser.add_argument('file', help='JSON-Datei mit Athletennamen (athletes_old.json Format)')
    batch_parser.add_argument('--since-days', type=int, default=30,
                             help='Nur Dokumente der letzten X Tage (default: 30)')
    batch_parser.add_argument('--chunk-size', type=int, default=1000,
                             help='Chunk-Größe in Tokens (default: 1000)')
    batch_parser.add_argument('--chunk-overlap', type=int, default=200,
                             help='Chunk-Überlappung in Tokens (default: 200)')
    batch_parser.add_argument('--embedding-model', default='sentence-transformers/all-mpnet-base-v2',
                             help='Embedding-Modell (default: all-mpnet-base-v2)')
    batch_parser.add_argument('-o', '--output', help='Speichere Ergebnisse in JSON-Datei')

    # Search command
    search_parser = subparsers.add_parser('search', help='Semantische Suche')
    search_parser.add_argument('query', help='Suchanfrage')
    search_parser.add_argument('--athlete', dest='athlete_name',
                              help='Beschränke Suche auf bestimmten Athleten')
    search_parser.add_argument('--top-k', type=int, default=5,
                              help='Anzahl Ergebnisse (default: 5)')
    search_parser.add_argument('--embedding-model', default='sentence-transformers/all-mpnet-base-v2',
                              help='Embedding-Modell (default: all-mpnet-base-v2)')
    search_parser.add_argument('-o', '--output', help='Speichere Ergebnisse in JSON-Datei')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Zeige Statistiken')
    stats_parser.add_argument('--athlete', dest='athlete_name',
                             help='Statistiken für bestimmten Athleten')
    stats_parser.add_argument('-o', '--output', help='Speichere Statistiken in JSON-Datei')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)

    # Dispatch to appropriate function
    if args.command == 'index':
        index_athlete(args)
    elif args.command == 'batch':
        index_batch(args)
    elif args.command == 'search':
        search(args)
    elif args.command == 'stats':
        stats(args)
    elif args.command == 'clear':
        clear_index(args)


if __name__ == '__main__':
    main()

