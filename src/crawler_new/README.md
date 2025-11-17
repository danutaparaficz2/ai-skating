# Wikipedia Short Track Speed Skating Crawler

Dieses Modul crawlt strukturierte Informationen aus der Wikipedia API rund um Short Track Speed Skating.

Als NoSql-Datenbank wird MongoDB verwendet. Docker Container inkl. Volume für die Persistenz mit folgendem Befehl installieren.
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:latest
```
Für die Verbindung sind keine Credentials notwendig. Verbindungs String: **mongodb://localhost:27017**

## Installation PIP

Um pip richtig zu verwenden wurde eine virtuelle Umgebung eingerichtet.
Im Pfad crawleer folgendes ausführen:
```bash
source .venv/bin/activate
```

## Crawler von 10 Athleten

Für den MVP wurden 10 Athleten gecrawlt mit verschiedenen Topics.
Die Dauer für diese Suche mit 10 Results Pro Athlet und Topic inkl. Persistierung in MongoDB war: **15 Minuten**.
Diese Suche hat **500 Tokens** verbraucht.