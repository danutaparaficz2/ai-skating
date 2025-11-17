# Generator - RAG mit FAISS und Alibaba Cloud Qwen

## Übersicht

Der Generator nutzt die vektorisierten Chunks aus der FAISS-Datenbank als Context für LLM-Anfragen über die Alibaba Cloud Qwen API.

## Setup

### 1. Umgebungsvariable setzen

```bash
export QWEN_API_KEY="your-api-key-here"
```

### 2. Dependencies installieren

```bash
cd generator
pip install -r requirements.txt
```

## Verwendung

### CLI - Fragen stellen

```bash
# Allgemeine Frage
python -m cli ask "Was sind die größten Erfolge von Kristen Santos-Griswold?"

# Frage mit Athlet-Filter
python -m cli ask "Welche Medaillen hat sie gewonnen?" --athlete "Kristen Santos-Griswold"

# Ohne Quellen-Anzeige
python -m cli ask "Erzähl mir über ihre Karriere" --no-sources

# Ergebnis als JSON speichern
python -m cli ask "Wer ist Kristen Santos-Griswold?" -o output.json
```

### CLI - Stories generieren

```bash
# Profil-Story
python -m cli story "Kristen Santos-Griswold" --type profile --style engaging

# Achievement-Story
python -m cli story "Kristen Santos-Griswold" --type achievement --style dramatic

# Story in Datei speichern
python -m cli story "Kristen Santos-Griswold" --type journey --style formal -o story.txt
```

### CLI - Vektor-Suche

```bash
# Suche nach bestimmtem Thema
python -m cli search "Olympic medals" --athlete "Kristen Santos-Griswold" --top-k 3

# Suche mit Ähnlichkeits-Filter
python -m cli search "training methods" --min-similarity 0.5 --top-k 10
```

### Python API

```python
from generator import RAGGenerator

# Initialisiere Generator
generator = RAGGenerator()

# Stelle eine Frage
result = generator.generate(
    query="Was sind die größten Erfolge von Kristen Santos-Griswold?",
    athlete_name="Kristen Santos-Griswold",
    include_sources=True
)

print(result['answer'])
print(f"Chunks verwendet: {result['metadata']['chunks_used']}")

# Generiere eine Story
story = generator.generate_story(
    athlete_name="Kristen Santos-Griswold",
    story_type="profile",
    style="engaging"
)

print(story)

# Cleanup
generator.close()
```

## Wie funktioniert RAG?

### 1. **Retrieve** - Relevante Chunks finden

Der Retriever:
- Nimmt deine Frage/Query
- Erstellt ein Embedding der Query
- Sucht in FAISS nach den ähnlichsten Vektoren
- Holt die Metadaten (Text, Athlet, etc.) aus MongoDB

### 2. **Augment** - Context aufbauen

- Die gefundenen Chunks werden formatiert
- Ein Prompt wird erstellt mit:
  - System-Anweisung
  - Context (die gefundenen Chunks)
  - Deine Frage

### 3. **Generate** - LLM generiert Antwort

- Der Prompt wird an Alibaba Cloud Qwen gesendet
- Das LLM generiert eine Antwort basierend auf dem Context
- Die Antwort wird mit Quellen zurückgegeben

## Architektur

```
┌─────────────┐
│   Query     │
│ "Wer ist    │
│  Athlet X?" │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  FAISSRetriever  │  ← Embedding-Modell
│                  │  ← FAISS Index
│                  │  ← MongoDB Metadaten
└────────┬─────────┘
         │
         │ Top-K Chunks
         ▼
┌──────────────────┐
│   RAG Prompt     │
│  ┌────────────┐  │
│  │ Context    │  │
│  │ + Query    │  │
│  └────────────┘  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Qwen LLM       │  ← Alibaba Cloud API
│  (qwen-plus)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Antwort +      │
│   Quellen        │
└──────────────────┘
```

## Datenfluss

1. **FAISS**: Speichert nur Embeddings (768-dim Vektoren)
2. **MongoDB**: Speichert Metadaten (Text, Athlet, URL, etc.)
3. **ID-Mapping**: Verbindet FAISS-IDs mit MongoDB-ObjectIDs

### Beispiel

```
Query: "Welche Medaillen hat Kristen gewonnen?"

1. Retrieve:
   - Query → Embedding
   - FAISS findet ähnlichste Vektoren (z.B. IDs: 42, 87, 103)
   - MongoDB liefert Texte zu diesen IDs

2. Context:
   [Information 1]
   Athlet: Kristen Santos-Griswold
   Text: "At the 2022 Olympics, Kristen won bronze in..."
   
   [Information 2]
   Athlet: Kristen Santos-Griswold
   Text: "Her World Championship gold medal in..."

3. Prompt:
   "Basierend auf folgenden Informationen...
    KONTEXT: [siehe oben]
    FRAGE: Welche Medaillen hat Kristen gewonnen?"

4. LLM generiert:
   "Kristen Santos-Griswold hat mehrere bedeutende Medaillen gewonnen:
    - Bronze bei den Olympischen Spielen 2022...
    - Gold bei der Weltmeisterschaft..."
```

## Konfiguration

Über Umgebungsvariablen:

```bash
# FAISS Index
export FAISS_INDEX_PATH="../transformer/faiss_indexes"

# MongoDB
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="crawler"
export MONGO_COLLECTION="athlete_chunks_embeddings"

# Qwen API
export QWEN_API_KEY="your-key"
export QWEN_MODEL="qwen-plus"  # oder qwen-turbo, qwen-max

# RAG Parameter
export TOP_K_CHUNKS="5"
export MIN_SIMILARITY="0.3"
export TEMPERATURE="0.7"
export MAX_TOKENS="1000"
```

## Tipps

### Bessere Ergebnisse

- **Spezifische Fragen**: "Welche Medaillen 2022?" statt "Medaillen?"
- **Athlet-Filter**: Nutze `--athlete` für fokussierte Antworten
- **Top-K anpassen**: Mehr Chunks = mehr Context, aber auch mehr Tokens
- **Min-Similarity**: Filtere irrelevante Ergebnisse (0.3-0.5 ist gut)

### Debugging

```bash
# Verbose Logging
python -m cli ask "..." -v

# Nur Suche testen (ohne LLM)
python -m cli search "..." --top-k 3

# Quellen inspizieren
python -m cli ask "..." -o result.json
cat result.json | jq '.sources'
```

## Troubleshooting

### "No module named 'pymongo'"
```bash
pip install pymongo
```

### "FAISS-Index nicht gefunden"
```bash
# Prüfe ob FAISS_INDEX_PATH korrekt ist
ls ../transformer/faiss_indexes/

# Oder setze explizit:
export FAISS_INDEX_PATH="/vollständiger/pfad/zu/faiss_indexes"
```

### "QWEN_API_KEY muss gesetzt sein"
```bash
export QWEN_API_KEY="sk-..."
```

### "Keine Ergebnisse gefunden"
- Prüfe ob der FAISS-Index Daten enthält (CLI: `stats` im transformer)
- Senke `min_similarity` auf 0.0
- Erhöhe `top_k`

