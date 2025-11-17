# Generator Module - Quick Start

RAG (Retrieval-Augmented Generation) für Athleten-Informationen mit Alibaba Cloud Qwen API.

## Setup

### 1. Dependencies installieren

```bash
cd /Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/generator
pip install -r requirements.txt
```

### 2. API Key setzen

**Alibaba Cloud API Key** als Umgebungsvariable:

```bash
export QWEN_API_KEY="your-alibaba-cloud-api-key"
```

Oder in deinem Code:
```python
import os
os.environ["QWEN_API_KEY"] = "your-key"
```

### 3. FAISS Index vorbereiten

Stelle sicher, dass der Transformer bereits gelaufen ist und FAISS-Indizes erstellt hat:

```bash
cd ../transformer
python -m cli index "Kristen Santos-Griswold" --since-days 30
```

## Verwendung

### CLI (Command Line)

#### Frage stellen
```bash
python -m cli ask "Was sind die Erfolge von Kristen Santos-Griswold?" \
  --athlete "Kristen Santos-Griswold"
```

#### Story generieren
```bash
python -m cli story "Kristen Santos-Griswold" \
  --type profile \
  --style engaging
```

#### Interaktiver Chat
```bash
python -m cli chat --athlete "Kristen Santos-Griswold"
```

### Python API

#### Einfache Frage

```python
from generator import RAGGenerator

generator = RAGGenerator()

result = generator.generate(
    query="Was sind die größten Erfolge von Kristen Santos-Griswold?",
    athlete_name="Kristen Santos-Griswold"
)

print(result['answer'])
print(f"Quellen: {len(result['sources'])}")

generator.close()
```

#### Chat mit History

```python
from generator import RAGGenerator

generator = RAGGenerator()

# Erste Frage
result1 = generator.chat(
    query="Erzähl mir über Kristen Santos-Griswold",
    athlete_name="Kristen Santos-Griswold"
)

# Follow-up (mit Kontext)
result2 = generator.chat(
    query="Was sind ihre wichtigsten Erfolge?",
    conversation_history=result1['conversation_history'],
    athlete_name="Kristen Santos-Griswold"
)

generator.close()
```

#### Story generieren

```python
from generator import RAGGenerator

generator = RAGGenerator()

story = generator.generate_story(
    athlete_name="Kristen Santos-Griswold",
    story_type="profile",  # "profile", "achievement", "journey"
    style="engaging"  # "engaging", "formal", "dramatic"
)

print(story)
generator.close()
```

## Konfiguration

### Umgebungsvariablen

```bash
# Alibaba Cloud
export QWEN_API_KEY="your-key"
export QWEN_MODEL="qwen-plus"  # oder qwen-turbo, qwen-max

# FAISS Index
export FAISS_INDEX_PATH="/path/to/faiss_indexes"

# MongoDB
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB="crawler"
export MONGO_CHUNKS_COLLECTION="athlete_chunks"

# RAG Parameter
export TOP_K_CHUNKS=5
export MIN_SIMILARITY=0.3

# LLM Parameter
export TEMPERATURE=0.7
export MAX_TOKENS=1000
```

### Custom Config im Code

```python
from generator import RAGGenerator, GeneratorConfig

config = GeneratorConfig(
    qwen_model="qwen-max",  # Besseres Modell
    top_k_chunks=10,  # Mehr Kontext
    min_similarity=0.4,  # Höherer Threshold
    temperature=0.9  # Mehr Kreativität
)

generator = RAGGenerator(config=config)
```

## Verfügbare Qwen Modelle

- **qwen-turbo**: Schnell, günstiger
- **qwen-plus**: Ausgewogen (Default)
- **qwen-max**: Beste Qualität

## Response Format

```python
{
    "answer": "Die generierte Antwort...",
    "sources": [
        {
            "id": 1,
            "athlete": "Kristen Santos-Griswold",
            "similarity": 0.89,
            "url": "https://...",
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

## Troubleshooting

### API Key Error
```
ValueError: QWEN_API_KEY muss gesetzt sein
```
→ Setze `export QWEN_API_KEY="your-key"`

### FAISS Index nicht gefunden
```
FileNotFoundError: FAISS-Index nicht gefunden
```
→ Führe zuerst den Transformer aus: `cd ../transformer && python -m cli index "Athlete"`

### Keine Chunks gefunden
```
Leider habe ich keine relevanten Informationen gefunden
```
→ Prüfe ob Athlet in MongoDB vorhanden ist
→ Verringere `min_similarity` in Config

## Beispiele

Siehe `examples.py` für vollständige Code-Beispiele.

```bash
python examples.py
```

## Performance Tipps

1. **Batch-Processing**: Verarbeite mehrere Fragen zusammen
2. **Cache**: Implementiere Caching für häufige Queries
3. **Modell-Wahl**: `qwen-turbo` für schnelle Antworten, `qwen-max` für Qualität
4. **Top-K**: Weniger Chunks = schneller, mehr Chunks = mehr Kontext

## Next Steps

- [ ] API-Endpoint erstellen (FastAPI)
- [ ] Web-Interface bauen
- [ ] Caching implementieren
- [ ] Multi-Athleten-Vergleiche
- [ ] Streaming für längere Antworten

