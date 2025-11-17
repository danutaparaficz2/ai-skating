# 🏠 Private Update - Verwendungsanleitung

## Was ist Private Update?

Private Update ist ein **fest kodierter** CLI-Befehl, der automatisch folgende Frage stellt:

> **"Was gibt es Neues im privaten Umfeld des Athleten?"**

Die Antwort umfasst:
- 🏠 Privates Umfeld (Familie, persönliche Geschichten)
- 🏆 Anstehende Turniere und Events
- 📰 Besondere Entwicklungen oder News

**Ausgabeformat:** 3-4 prägnante Sätze

---

## 🚀 Verwendung

### Basis-Befehl

```bash
cd /Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/generator
source venv/bin/activate
python -m cli private-update "Athleten-Name"
```

### Mit Websuche (empfohlen)

```bash
python -m cli private-update "Kristen Santos-Griswold" --enable-web-search
```

### Ohne Websuche

```bash
python -m cli private-update "Kristen Santos-Griswold" --no-web-search
```

### Ohne Quellen-Anzeige

```bash
python -m cli private-update "Kristen Santos-Griswold" --no-sources
```

### Output als JSON speichern

```bash
python -m cli private-update "Kristen Santos-Griswold" -o update.json
```

---

## 📋 Beispiel-Output

```
============================================================
🏠 Private Update: Kristen Santos-Griswold
============================================================
🌐 Websuche: AKTIVIERT

Kristen Santos-Griswold, die aus Fairfield, Connecticut stammt und zwei Hunde 
namens Bear und Koda hat, konzentriert sich derzeit auf ihre Genesung von einer 
Rückenverletzung. Sie hat sich vom U.S. Championships-Rennen 2026 zurückgezogen, 
wird aber beim ersten Weltcup-Auftritt in Montreal (9.–12. Oktober 2025) 
wieder antreten. Neben ihrer Karriere arbeitet sie an einem Doktortitel mit 
dem Ziel, später als Physiotherapeutin zu arbeiten.

📚 Quellen (8):
  [1] Kristen Santos-Griswold (Similarity: 0.66)
  ...

📊 Metadaten:
  Chunks verwendet: 8
  Websuche: Ja
```

---

## ⚙️ Wie funktioniert es?

1. **Retrieval:** Holt 8 relevante Chunks aus FAISS-DB
2. **Template:** Verwendet fest kodierten Prompt (`build_private_update_prompt`)
3. **LLM:** Sendet Anfrage an Qwen3-Max mit Websuche-Hinweis
4. **Output:** Formatiert Antwort mit Quellen und Metadaten

---

## 🔧 Anpassungen

### Template ändern

Bearbeite `/generator/prompts.py`:

```python
@staticmethod
def build_private_update_prompt(athlete_name: str, context: str, enable_web_search: bool = True) -> str:
    # 👉 HIER KANNST DU DAS TEMPLATE ANPASSEN!
    
    prompt = f"""Was gibt es Neues im privaten Umfeld von {athlete_name}?
    
    AUFGABE:
    Fasse in 3-4 prägnanten Sätzen zusammen:
    1. Was läuft privat im Umfeld des Athleten (Familie, persönliches)
    2. Welche anstehenden Turniere oder Events sind geplant
    3. Gibt es besondere Entwicklungen oder News
    """
    return prompt
```

### System Prompt ändern

```python
SYSTEM_PRIVATE_UPDATE = """Du bist ein Experte für Short-Track Eisschnelllauf...
👉 HIER SYSTEM-PROMPT ANPASSEN
"""
```

### Parameter ändern

In `rag_generator.py` → `generate_private_update()`:

```python
chunks = self.retriever.retrieve(
    query=f"{athlete_name} personal life family upcoming tournaments events",
    athlete_name=athlete_name,
    top_k=8,  # 👉 Anzahl Chunks
    min_similarity=0.2  # 👉 Ähnlichkeits-Schwelle
)
```

---

## 🆚 Unterschied zu `ask`

| Feature | `private-update` | `ask` |
|---------|------------------|-------|
| Frage | ✅ Fest kodiert | ❌ Manuell eingeben |
| Template | ✅ Private Update Template | ❌ Allgemeines Q&A Template |
| Websuche | ✅ Option verfügbar | ❌ Nicht verfügbar |
| Chunks | 8 (mehr Kontext) | 5 (Standard) |
| Output | 3-4 Sätze | Variable Länge |

---

## 💡 Use Cases

- **Social Media Posts:** Schnelle Updates für Fans
- **Newsletter:** Private News-Abschnitt
- **Dashboard:** Widget mit aktuellen Athlete-Updates
- **API:** Endpoint für Frontend

---

## 🐛 Troubleshooting

### Keine Ergebnisse

```bash
# Prüfe ob Daten in FAISS-DB vorhanden sind
python -m cli search "Athleten-Name" --top-k 10
```

### API-Fehler

```bash
# Prüfe API-Key
echo $DASHSCOPE_API_KEY

# Setze Key
export DASHSCOPE_API_KEY='your-key-here'
```

### Websuche funktioniert nicht

Die Websuche ist aktuell ein **Hinweis** im Prompt an das LLM.
Für echte Websuche müsste eine externe API integriert werden (z.B. Google Custom Search API).

---

## 📚 Weitere Befehle

```bash
# Stelle eigene Frage
python -m cli ask "Deine Frage" --athlete "Name"

# Generiere Story
python -m cli story "Name" --type profile --style engaging

# Suche in Vektor-DB
python -m cli search "Query" --athlete "Name" --top-k 5
```

---

**Viel Erfolg! 🚀**

