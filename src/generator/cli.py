"""Command-Line Interface für den RAG-Generator."""

import argparse
import logging
import json
import sys
import os

# Füge das parent-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import RAGGenerator, GeneratorConfig


def setup_logging(verbose: bool = False):
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def ask_command(args):
    """Stellt eine Frage via RAG."""
    generator = RAGGenerator()

    try:
        result = generator.generate(
            query=args.query,
            athlete_name=args.athlete,
            include_sources=not args.no_sources
        )

        print()
        print("="*60)
        print("💬 Antwort:")
        print("="*60)
        print(result['answer'])

        if result['sources'] and not args.no_sources:
            print(f"\n📚 Quellen ({len(result['sources'])}):")
            for source in result['sources']:
                print(f"\n  [{source['id']}] {source['athlete']} (Similarity: {source['similarity']})")
                print(f"      URL: {source['url']}")
                print(f"      {source['preview'][:150]}...")

        print(f"\n📊 Metadaten:")
        print(f"  Chunks verwendet: {result['metadata']['chunks_used']}")
        print(f"  Modell: {result['metadata']['model']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Vollständige Antwort gespeichert: {args.output}")

    finally:
        generator.close()


def story_command(args):
    """Generiert eine Story über einen Athleten."""
    generator = RAGGenerator()

    try:
        result = generator.generate_story(
            athlete_name=args.athlete,
            story_type=args.type,
            style=args.style,
            enable_web_search=args.enable_web_search
        )

        print()
        print("="*60)
        print(f"📖 Story: {args.athlete}")
        print("="*60)
        if result['web_search_enabled']:
            print("🌐 Websuche: AKTIVIERT")
        print(f"📝 Typ: {args.type} | Stil: {args.style}")
        print("="*60)
        print()
        print(result['story'])
        print()
        print("="*60)

        if result['sources'] and not args.no_sources:
            print(f"\n📚 Quellen aus Datenbank ({len(result['sources'])}):")
            for source in result['sources'][:5]:  # Top 5 Quellen
                print(f"  [{source['id']}] {source['athlete']} (Similarity: {source['similarity']})")
                print(f"      {source['preview'][:100]}...")

        # Zeige Web-Quellen
        if result.get('web_sources') and not args.no_sources:
            print(f"\n🌐 Web-Quellen ({len(result['web_sources'])}):")
            for source in result['web_sources']:
                print(f"  [WEB {source['id']}] {source['title']}")
                print(f"      URL: {source['url']}")

        print(f"\n📊 Metadaten:")
        print(f"  Chunks verwendet: {result['metadata']['chunks_used']}")
        print(f"  Web-Ergebnisse: {result['metadata'].get('web_results_used', 0)}")
        print(f"  Story-Typ: {result['metadata']['story_type']}")
        print(f"  Stil: {result['metadata']['style']}")
        print(f"  Websuche: {'Ja' if result['web_search_enabled'] else 'Nein'}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Story gespeichert: {args.output}")

    finally:
        generator.close()


def private_update_command(args):
    """Generiert ein Private Update für einen Athleten (fest kodierte Frage)."""
    generator = RAGGenerator()

    try:
        result = generator.generate_private_update(
            athlete_name=args.athlete,
            enable_web_search=args.enable_web_search
        )

        print()
        print("="*60)
        print(f"🏠 Private Update: {args.athlete}")
        print("="*60)
        if result['web_search_enabled']:
            print("🌐 Websuche: AKTIVIERT")
        print()
        print(result['answer'])

        # Zeige FAISS-Quellen
        if result['sources'] and not args.no_sources:
            print(f"\n📚 Quellen aus Datenbank ({len(result['sources'])}):")
            for source in result['sources']:
                print(f"\n  [{source['id']}] {source['athlete']} (Similarity: {source['similarity']})")
                print(f"      {source['preview'][:100]}...")

        # Zeige Web-Quellen
        if result.get('web_sources') and not args.no_sources:
            print(f"\n🌐 Web-Quellen ({len(result['web_sources'])}):")
            for source in result['web_sources']:
                print(f"\n  [WEB {source['id']}] {source['title']}")
                print(f"      URL: {source['url']}")
                print(f"      {source['snippet']}...")

        print(f"\n📊 Metadaten:")
        print(f"  Chunks verwendet: {result['metadata']['chunks_used']}")
        print(f"  Web-Ergebnisse: {result['metadata'].get('web_results_used', 0)}")
        print(f"  Websuche: {'Ja' if result['web_search_enabled'] else 'Nein'}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Update gespeichert: {args.output}")

    finally:
        generator.close()


def search_command(args):
    """Sucht in der Vektor-Datenbank."""
    config = GeneratorConfig()
    config.validate()

    from generator.retriever import FAISSRetriever

    retriever = FAISSRetriever(
        faiss_index_path=config.faiss_index_path,
        mongo_uri=config.mongo_uri,
        mongo_db=config.mongo_db,
        mongo_collection=config.mongo_collection,
        embedding_model=config.embedding_model
    )

    try:
        results = retriever.retrieve(
            query=args.query,
            athlete_name=args.athlete,
            top_k=args.top_k,
            min_similarity=args.min_similarity
        )

        print()
        print("="*60)
        print(f"🔍 Suchergebnisse für: '{args.query}'")
        print("="*60)

        if not results:
            print("\n❌ Keine Ergebnisse gefunden.")
        else:
            for i, result in enumerate(results, 1):
                print(f"\n[{i}] Athlet: {result['athlete_name']}")
                print(f"    Ähnlichkeit: {result['similarity']:.3f}")
                print(f"    Topic: {result['metadata'].get('topic', 'N/A')}")
                print(f"    URL: {result['metadata'].get('url', 'N/A')}")
                print(f"    Text: {result['text'][:200]}...")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Ergebnisse gespeichert: {args.output}")

    finally:
        retriever.close()


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description='RAG-Generator für Athleten-Informationen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Stelle eine Frage
  %(prog)s ask "Was sind die größten Erfolge von Kristen Santos-Griswold?"
  
  # Frage mit Athlet-Filter
  %(prog)s ask "Welche Medaillen hat sie gewonnen?" --athlete "Kristen Santos-Griswold"
  
  # Private Update (fest kodierte Frage mit Websuche)
  %(prog)s private-update "Kristen Santos-Griswold" --enable-web-search
  
  # Generiere eine Story
  %(prog)s story "Kristen Santos-Griswold" --type profile --style engaging
  
  # Suche in der Vektor-DB
  %(prog)s search "Olympic medals" --athlete "Kristen Santos-Griswold" --top-k 3
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose logging (DEBUG level)')

    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')

    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Stelle eine Frage')
    ask_parser.add_argument('query', help='Deine Frage')
    ask_parser.add_argument('--athlete', help='Filter auf bestimmten Athleten')
    ask_parser.add_argument('--no-sources', action='store_true',
                           help='Keine Quellen anzeigen')
    ask_parser.add_argument('-o', '--output', help='Speichere Antwort als JSON')

    # Private Update command (FEST KODIERT)
    private_parser = subparsers.add_parser('private-update',
                                            help='Private Update für Athleten (fest kodiert)')
    private_parser.add_argument('athlete', help='Name des Athleten')
    private_parser.add_argument('--enable-web-search', action='store_true', default=True,
                               help='Aktiviere Websuche (default: True)')
    private_parser.add_argument('--no-web-search', dest='enable_web_search',
                               action='store_false',
                               help='Deaktiviere Websuche')
    private_parser.add_argument('--no-sources', action='store_true',
                               help='Keine Quellen anzeigen')
    private_parser.add_argument('-o', '--output', help='Speichere Update als JSON')

    # Story command
    story_parser = subparsers.add_parser('story', help='Generiere eine Story')
    story_parser.add_argument('athlete', help='Name des Athleten')
    story_parser.add_argument('--type', choices=['profile', 'achievement', 'journey'],
                             default='profile', help='Art der Story')
    story_parser.add_argument('--style', choices=['engaging', 'formal', 'dramatic'],
                             default='engaging', help='Schreibstil')
    story_parser.add_argument('--enable-web-search', action='store_true', default=True,
                             help='Aktiviere Websuche für aktuelle Informationen (default: True)')
    story_parser.add_argument('--no-web-search', dest='enable_web_search',
                             action='store_false',
                             help='Deaktiviere Websuche')
    story_parser.add_argument('--no-sources', action='store_true',
                             help='Keine Quellen anzeigen')
    story_parser.add_argument('-o', '--output', help='Speichere Story in Datei')

    # Search command
    search_parser = subparsers.add_parser('search', help='Suche in Vektor-DB')
    search_parser.add_argument('query', help='Suchanfrage')
    search_parser.add_argument('--athlete', help='Filter auf bestimmten Athleten')
    search_parser.add_argument('--top-k', type=int, default=5,
                              help='Anzahl Ergebnisse (default: 5)')
    search_parser.add_argument('--min-similarity', type=float, default=0.0,
                              help='Minimale Ähnlichkeit (default: 0.0)')
    search_parser.add_argument('-o', '--output', help='Speichere Ergebnisse als JSON')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)

    # Dispatch to appropriate function
    if args.command == 'ask':
        ask_command(args)
    elif args.command == 'private-update':
        private_update_command(args)
    elif args.command == 'story':
        story_command(args)
    elif args.command == 'search':
        search_command(args)


if __name__ == '__main__':
    main()

