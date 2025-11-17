# 🚀 Generator - Wie benutze ich es?

## ⚙️ Schritt 0: API-Key setzen (WICHTIG!)

```bash
export DASHSCOPE_API_KEY="sk-dein-api-key-hier"
```

## ✅ Schritt 1: Terminal öffnen und ins Verzeichnis wechseln

```bash
cd /Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/generator
```

## ✅ Schritt 2: Virtual Environment aktivieren

```bash
source venv/bin/activate
```

Du solltest jetzt `(venv)` vor deinem Prompt sehen.

## ✅ Schritt 3: Qwen mit RAG abfragen

### **Einfache Frage stellen:**

```bash
python -m cli ask "Was sind die Erfolge von Kristen Santos-Griswold?"
```

### **Frage mit Athlet-Filter (EMPFOHLEN):**

```bash
python -m cli ask "Was gibt es Neues?" --athlete "Kristen Santos-Griswold"
```

### **Deine spezifische Frage:**

```bash
python -m cli ask "Was gibt es Neues? Berichte über privates Umfeld und voranstehende Turniere" --athlete "Kristen Santos-Griswold"
```

### **Ohne Quellen-Anzeige:**

```bash
python -m cli ask "Was gibt es Neues?" --athlete "Kristen Santos-Griswold" --no-sources
```

### **Antwort als JSON speichern:**

```bash
python -m cli ask "Was gibt es Neues?" --athlete "Kristen Santos-Griswold" -o antwort.json
```

## 📖 Story generieren

```bash
# Profil-Story
python -m cli story "Kristen Santos-Griswold" --type profile --style engaging

# Achievement-Story
python -m cli story "Kristen Santos-Griswold" --type achievement --style dramatic

# In Datei speichern
python -m cli story "Kristen Santos-Griswold" -o story.txt
```

## 🔍 Nur Vektor-Suche (ohne LLM)

```bash
python -m cli search "Olympic medals" --athlete "Kristen Santos-Griswold" --top-k 5
```

## 📝 Python-Script verwenden

Erstelle eine Datei `meine_abfrage.py`:

```python
from generator import RAGGenerator

# Initialisiere
generator = RAGGenerator()

# Stelle Frage
result = generator.generate(
    query="Was gibt es Neues bei Kristen Santos-Griswold?",
    athlete_name="Kristen Santos-Griswold",
    include_sources=True
)

# Zeige Antwort
print(result['answer'])

# Zeige Quellen
for source in result['sources']:
    print(f"Quelle: {source['athlete']} - {source['topic']}")

# Cleanup
generator.close()
```

Dann ausführen:

```bash
python meine_abfrage.py
```

## 🎯 Vollständiges Beispiel

```bash
# 1. Ins Verzeichnis
cd /Users/kaplank/Privat/FFHS/Deepl_Hackathon/ai-skating/src/generator

# 2. venv aktivieren
source venv/bin/activate

# 3. Frage stellen
python -m cli ask "Was gibt es Neues bei Kristen Santos-Griswold? Berichte über privates Umfeld und voranstehende Turniere" --athlete "Kristen Santos-Griswold"
```

## ⚙️ Optionen anpassen

Du kannst auch Umgebungsvariablen setzen:

```bash
# Mehr Kontext-Chunks
export TOP_K_CHUNKS=10

# Andere Temperatur (kreativer)
export TEMPERATURE=0.9

# Dann normale Abfrage
python -m cli ask "Erzähl mir über Kristen" --athlete "Kristen Santos-Griswold"
```

## 🆘 Troubleshooting

### "Module not found"
```bash
# Stelle sicher dass venv aktiviert ist
### "DASHSCOPE_API_KEY muss gesetzt sein" oder "Unauthorized"
```bash
# Setze den API-Key
export DASHSCOPE_API_KEY="sk-dein-key-hier"

# Überprüfe ob gesetzt
echo $DASHSCOPE_API_KEY
```

Oder setze direkt in der config.py (Zeile 31-33).
# Installiere Dependencies
pip install -r requirements.txt
```

### "QWEN_API_KEY muss gesetzt sein"
Der Key ist bereits in `config.py` hardcoded, sollte also funktionieren!

### "Keine Ergebnisse gefunden"
Prüfe ob FAISS-Daten vorhanden sind:
```bash
python -m cli search "test" --top-k 1
```

Wenn 0 Ergebnisse: Du musst zuerst im `transformer` Modul Daten indexieren!

## 📊 Alle verfügbaren Befehle

```bash
# Hilfe anzeigen
python -m cli --help

# Hilfe für 'ask' Befehl
python -m cli ask --help

# Hilfe für 'story' Befehl
python -m cli story --help

# Hilfe für 'search' Befehl
python -m cli search --help
```

