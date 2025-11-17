# Generator Module - RAG mit Alibaba Cloud

Retrieval-Augmented Generation (RAG) System für Athleten-Informationen mit FAISS Vector Store und Alibaba Cloud Qwen API.

## 📋 Überblick

Dieses Modul ermöglicht:
- ✅ Semantische Suche in Athleten-Dokumenten (FAISS)
- ✅ Q&A über Athleten mit kontextbasierter Generierung
- ✅ Chat-Konversationen mit History
- ✅ Automatische Story-Generierung
- ✅ Integration mit Alibaba Cloud Qwen LLM

## 🏗️ Architektur

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  RAGGenerator       │
│  - Orchestriert     │
│    Pipeline         │
└──────┬──────────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌──────────────┐   ┌─────────────┐
│ Retriever    │   │ LLM Client  │
│ - FAISS      │   │ - Qwen API  │
│ - MongoDB    │   └─────────────┘
└──────────────┘
```

## 📦 Komponenten

### 1. `config.py`
Zentrale Konfiguration für:
- FAISS Index Pfade
- MongoDB Verbindungen
- Qwen API Settings
- RAG Parameter (top_k, similarity)
- LLM Parameter (temperature, max_tokens)

### 2. `retriever.py`
**FAISSRetriever** - Semantische Suche
- Lädt FAISS-Index und Metadaten
- Query → Embedding → Ähnlichkeitssuche
- Filtert nach Athlet, Similarity-Threshold
- Gibt relevante Chunks mit Metadaten zurück

### 3. `llm_client.py`
**QwenClient** - Alibaba Cloud Integration
- OpenAI-kompatible API
- Chat Completion
- Text Generation
- Context-basierte Generation

### 4. `rag_generator.py`
**RAGGenerator** - Hauptklasse
- `generate()`: Einzelne Frage beantworten
- `chat()`: Konversation mit History
- `generate_story()`: Story-Generierung
- Orchestriert Retrieval + Generation

### 5. `cli.py`
Command-Line Interface
- `ask`: Frage stellen
- `story`: Story generieren
- `chat`: Interaktiver Chat

## 🚀 Installation

```bash
cd /Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/generator
pip install -r requirements.txt
```

## ⚙️ Konfiguration

### API Key setzen

```bash
export QWEN_API_KEY="sk-your-alibaba-cloud-key"
```

### Weitere Optionen (optional)

```bash
# Pfade
export FAISS_INDEX_PATH="/path/to/faiss_indexes"
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB="crawler"

# RAG Parameter
export TOP_K_CHUNKS=5
export MIN_SIMILARITY=0.3

# LLM Parameter
export QWEN_MODEL="qwen-plus"
export TEMPERATURE=0.7
export MAX_TOKENS=1000
```

## 💻 Verwendung

### CLI

```bash
# Frage stellen
python -m cli ask "Was sind die Erfolge von Kristen Santos-Griswold?"

# Mit Athleten-Filter
python -m cli ask "Welche Medaillen hat sie gewonnen?" \
  --athlete "Kristen Santos-Griswold"

# Story generieren
python -m cli story "Kristen Santos-Griswold" \
  --type profile \
  --style engaging \
  -o story.txt

# Interaktiver Chat
python -m cli chat --athlete "Kristen Santos-Griswold"
```

### Python API

```python
from generator import RAGGenerator

# Initialisierung
generator = RAGGenerator()

# Frage stellen
result = generator.generate(
    query="Was sind die größten Erfolge?",
    athlete_name="Kristen Santos-Griswold"
)

print(result['answer'])
print(f"Quellen: {result['sources']}")

# Cleanup
generator.close()
```

Siehe [QUICKSTART.md](QUICKSTART.md) für mehr Beispiele.

## 📊 Response Format

```python
{
    "answer": "Generierte Antwort basierend auf Chunks...",
    "sources": [
        {
            "id": 1,
            "athlete": "Kristen Santos-Griswold",
            "similarity": 0.89,
            "url": "https://example.com",
            "topic": "achievements",
            "preview": "Text preview..."
        }
    ],
    "metadata": {
        "chunks_used": 5,
        "athlete_filter": "Kristen Santos-Griswold",
        "model": "qwen-plus",
        "top_similarity": 0.89
    }
}
```

## 🎯 Use Cases

### 1. Q&A System
```python
result = generator.generate(
    query="Wie viele Olympia-Medaillen hat Kristen Santos-Griswold?",
    athlete_name="Kristen Santos-Griswold"
)
```

### 2. Story Generation
```python
story = generator.generate_story(
    athlete_name="Kristen Santos-Griswold",
    story_type="achievement",
    style="dramatic"
)
```

### 3. Chat Interface
```python
# Erste Frage
r1 = generator.chat(query="Erzähl mir über Kristen")

# Follow-up mit Kontext
r2 = generator.chat(
    query="Was sind ihre größten Erfolge?",
    conversation_history=r1['conversation_history']
)
```

### 4. Multi-Athleten-Vergleich
```python
result = generator.generate(
    query="Vergleiche die Erfolge verschiedener Short-Track Athleten"
    # Kein athlete_name Filter → sucht über alle
)
```

## 🔧 Advanced Usage

### Custom Config

```python
from generator import GeneratorConfig, RAGGenerator

config = GeneratorConfig(
    # Mehr Kontext holen
    top_k_chunks=10,
    min_similarity=0.2,
    
    # LLM Settings
    qwen_model="qwen-max",  # Bestes Modell
    temperature=0.9,
    max_tokens=2000,
    
    # Custom System Prompt
    system_prompt="Du bist ein Experte für Short-Track Eisschnelllauf..."
)

generator = RAGGenerator(config=config)
```

### Nur Retrieval (ohne LLM)

```python
from generator import FAISSRetriever

retriever = FAISSRetriever(
    faiss_index_path="...",
    mongo_uri="mongodb://localhost:27017/",
    mongo_db="crawler",
    mongo_collection="athlete_chunks"
)

chunks = retriever.retrieve(
    query="Olympic medals",
    athlete_name="Kristen Santos-Griswold",
    top_k=10
)

for chunk in chunks:
    print(f"{chunk['similarity']:.2f}: {chunk['text'][:100]}")
```

## 🧪 Testing

```bash
# Teste mit Beispielen
python examples.py

# CLI Test
python -m cli ask "Test question" --athlete "Kristen Santos-Griswold" -v
```

## 📈 Performance Optimierung

### 1. Top-K Parameter
- Weniger Chunks (top_k=3): Schneller, weniger Kontext
- Mehr Chunks (top_k=10): Langsamer, mehr Kontext

### 2. Similarity Threshold
- Höher (0.5): Nur sehr relevante Chunks
- Niedriger (0.2): Mehr Chunks, evtl. weniger relevant

### 3. Modell-Wahl
- `qwen-turbo`: Schnell, günstig
- `qwen-plus`: Ausgewogen (Default)
- `qwen-max`: Beste Qualität, langsamer

### 4. Batch Processing
```python
# Mehrere Fragen zusammen verarbeiten
questions = [...]
for q in questions:
    result = generator.generate(q)
```

## 🔍 Troubleshooting

### Problem: API Key Error
```
ValueError: QWEN_API_KEY muss gesetzt sein
```
**Lösung**: `export QWEN_API_KEY="your-key"`

### Problem: FAISS Index nicht gefunden
```
FileNotFoundError: FAISS-Index nicht gefunden
```
**Lösung**: Führe zuerst Transformer aus
```bash
cd ../transformer
python -m cli index "Athlete Name"
```

### Problem: Keine Chunks gefunden
```
Leider habe ich keine relevanten Informationen gefunden
```
**Lösung**: 
- Prüfe ob Athlet in MongoDB existiert
- Verringere `min_similarity`
- Erhöhe `top_k_chunks`

### Problem: Schlechte Antwort-Qualität
**Lösung**:
- Verwende `qwen-max` statt `qwen-plus`
- Erhöhe `top_k_chunks` für mehr Kontext
- Passe `system_prompt` an

## 📚 Weitere Dokumentation

- [QUICKSTART.md](QUICKSTART.md) - Quick Start Guide
- [examples.py](examples.py) - Code-Beispiele
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation Details

## 🔗 Dependencies

- `sentence-transformers`: Embedding-Generierung
- `faiss-cpu`: Vector Store
- `pymongo`: MongoDB-Zugriff
- `requests`: Alibaba Cloud API
- `torch`: ML Backend

## 📝 Lizenz

Internes Projekt - FFHS Deep Learning Hackathon

## 🤝 Contributing

Siehe Hauptprojekt README für Details.

