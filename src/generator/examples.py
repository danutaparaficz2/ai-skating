"""Beispiele für die Verwendung des RAG-Generators."""

import os
from generator import RAGGenerator, GeneratorConfig

# Setze API Key (in Production: als Umgebungsvariable)
os.environ["QWEN_API_KEY"] = "your-api-key-here"


def example_simple_question():
    """Beispiel: Einfache Frage stellen."""
    print("\n=== Beispiel 1: Einfache Frage ===")

    generator = RAGGenerator()

    result = generator.generate(
        query="Was sind die größten Erfolge von Kristen Santos-Griswold?",
        athlete_name="Kristen Santos-Griswold"
    )

    print(f"\nAntwort: {result['answer']}")
    print(f"\nQuellen: {len(result['sources'])} Chunks verwendet")

    generator.close()


def example_chat():
    """Beispiel: Chat-Konversation."""
    print("\n=== Beispiel 2: Chat-Konversation ===")

    generator = RAGGenerator()

    # Erste Frage
    result1 = generator.chat(
        query="Erzähl mir über Kristen Santos-Griswold",
        athlete_name="Kristen Santos-Griswold"
    )

    print(f"\n👤: Erzähl mir über Kristen Santos-Griswold")
    print(f"🤖: {result1['answer']}")

    # Follow-up Frage (mit History)
    result2 = generator.chat(
        query="Was sind ihre wichtigsten Erfolge?",
        conversation_history=result1['conversation_history'],
        athlete_name="Kristen Santos-Griswold"
    )

    print(f"\n👤: Was sind ihre wichtigsten Erfolge?")
    print(f"🤖: {result2['answer']}")

    generator.close()


def example_story():
    """Beispiel: Story generieren."""
    print("\n=== Beispiel 3: Story generieren ===")

    generator = RAGGenerator()

    story = generator.generate_story(
        athlete_name="Kristen Santos-Griswold",
        story_type="profile",
        style="engaging"
    )

    print(f"\n{story}")

    generator.close()


def example_custom_config():
    """Beispiel: Custom Konfiguration."""
    print("\n=== Beispiel 4: Custom Config ===")

    config = GeneratorConfig(
        top_k_chunks=10,  # Mehr Kontext
        min_similarity=0.4,  # Höherer Threshold
        temperature=0.9,  # Mehr Kreativität
        qwen_model="qwen-max"  # Besseres Modell
    )

    generator = RAGGenerator(config=config)

    result = generator.generate(
        query="Vergleiche verschiedene Short-Track Athleten"
    )

    print(f"\nAntwort: {result['answer']}")

    generator.close()


def example_retrieval_only():
    """Beispiel: Nur Retrieval ohne LLM."""
    print("\n=== Beispiel 5: Nur Retrieval ===")

    from generator import FAISSRetriever

    retriever = FAISSRetriever(
        faiss_index_path="/Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/transformer/faiss_indexes",
        mongo_uri="mongodb://localhost:27017/",
        mongo_db="crawler",
        mongo_collection="athlete_chunks"
    )

    chunks = retriever.retrieve(
        query="Olympic medals",
        top_k=5
    )

    print(f"\nGefunden: {len(chunks)} Chunks")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n[{i}] {chunk['athlete_name']} (Similarity: {chunk['similarity']:.3f})")
        print(f"    {chunk['text'][:100]}...")

    retriever.close()


if __name__ == "__main__":
    print("RAG Generator - Beispiele")
    print("="*60)

    # Wähle ein Beispiel:
    example_simple_question()
    # example_chat()
    # example_story()
    # example_custom_config()
    # example_retrieval_only()

