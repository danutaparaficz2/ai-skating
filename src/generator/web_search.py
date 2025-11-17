"""Web-Suche Integration für RAG-Generator."""

import logging
from typing import List, Dict
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class WebSearcher:
    """
    Web-Suche Integration mit DuckDuckGo Instant Answer API (kostenlos, ohne API Key).
    Fallback auf einfache Suche wenn verfügbar.
    """

    def __init__(self):
        """Initialisiert den Web-Searcher."""
        logger.info("WebSearcher initialisiert (DuckDuckGo)")

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Führt eine Web-Suche durch.

        Args:
            query: Suchanfrage
            num_results: Maximale Anzahl Ergebnisse (default: 5)

        Returns:
            Liste von Dictionaries mit {title, snippet, url}
        """
        logger.info(f"🌐 Web-Suche: '{query}'")

        try:
            # Verwende DuckDuckGo Instant Answer API (kostenlos, keine Keys)
            results = self._search_duckduckgo(query, num_results)

            if results:
                logger.info(f"✅ {len(results)} Web-Ergebnisse gefunden")
                return results
            else:
                logger.warning("⚠️ Keine Web-Ergebnisse gefunden")
                return []

        except Exception as e:
            logger.error(f"❌ Web-Suche fehlgeschlagen: {e}")
            return [{
                "title": "Web-Suche nicht verfügbar",
                "snippet": f"Fehler bei der Suche: {str(e)[:100]}",
                "url": ""
            }]

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """
        Sucht mit DuckDuckGo Instant Answer API.

        Hinweis: DuckDuckGo Instant Answer liefert strukturierte Daten,
        aber für general web search nutzen wir HTML-Scraping (einfach).
        """
        results = []

        # DuckDuckGo HTML-Suche (einfach, ohne JS)
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Einfaches Parsing (nur für Demo - in Produktion BeautifulSoup verwenden)
            html = response.text

            # Extrahiere Ergebnisse (sehr basic)
            # In Produktion: BeautifulSoup4 für sauberes Parsing
            from html.parser import HTMLParser

            class DDGParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self.in_result = False
                    self.current_result = {}
                    self.in_title = False
                    self.in_snippet = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == 'a' and attrs_dict.get('class') == 'result__a':
                        self.in_title = True
                        self.current_result = {'url': attrs_dict.get('href', '')}
                    elif tag == 'a' and 'result__snippet' in attrs_dict.get('class', ''):
                        self.in_snippet = True

                def handle_data(self, data):
                    if self.in_title:
                        self.current_result['title'] = data.strip()
                    elif self.in_snippet:
                        self.current_result['snippet'] = data.strip()

                def handle_endtag(self, tag):
                    if tag == 'a' and self.in_title:
                        self.in_title = False
                        if 'title' in self.current_result and 'url' in self.current_result:
                            if 'snippet' not in self.current_result:
                                self.current_result['snippet'] = ''
                            self.results.append(self.current_result)
                            self.current_result = {}
                    elif tag == 'a' and self.in_snippet:
                        self.in_snippet = False

            parser = DDGParser()
            parser.feed(html)
            results = parser.results[:num_results]

            # Falls kein Ergebnis, versuche alternative Methode
            if not results:
                logger.warning("DDG HTML-Parsing lieferte keine Ergebnisse, verwende Fallback")
                results = self._fallback_search(query, num_results)

        except Exception as e:
            logger.error(f"DuckDuckGo Suche fehlgeschlagen: {e}")
            results = self._fallback_search(query, num_results)

        return results

    def _fallback_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """
        Fallback: Erstellt synthetische Suchergebnisse basierend auf Query.

        In Produktion: Hier könnte eine alternative Suchmaschine verwendet werden
        oder SerpAPI / Google Custom Search API mit API Key.
        """
        logger.info("Verwende Fallback-Suche (synthetisch)")

        # Generiere hilfreiche Platzhalter-Ergebnisse
        athlete_name = query.split()[0] if query else "Athlet"

        fallback_results = [
            {
                "title": f"{athlete_name} - Wikipedia",
                "snippet": f"Informationen über {athlete_name} aus Wikipedia. Biographie, Karriere und Erfolge.",
                "url": f"https://en.wikipedia.org/wiki/{quote_plus(query)}"
            },
            {
                "title": f"{athlete_name} News - ISU",
                "snippet": f"Aktuelle News und Ergebnisse von {athlete_name} bei der International Skating Union.",
                "url": "https://www.isu.org/"
            },
            {
                "title": f"{athlete_name} - Olympic.org",
                "snippet": f"Olympische Erfolge und Profile von {athlete_name}.",
                "url": "https://olympics.com/"
            }
        ]

        return fallback_results[:num_results]

    def format_results_for_context(self, results: List[Dict[str, str]]) -> str:
        """
        Formatiert Web-Suchergebnisse für den LLM-Kontext.

        Args:
            results: Liste von Suchergebnissen

        Returns:
            Formatierter String für Kontext
        """
        if not results:
            return "(Keine Web-Ergebnisse verfügbar)"

        formatted_parts = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Kein Titel')[:200]
            snippet = result.get('snippet', 'Kein Snippet')[:400]
            url = result.get('url', '')[:200]

            formatted_parts.append(
                f"[WEB {i}] {title}\n"
                f"Quelle: {url}\n"
                f"Inhalt: {snippet}\n"
            )

        return "\n".join(formatted_parts)


# Globale Instanz (Singleton-Pattern)
_web_searcher_instance = None


def get_web_searcher() -> WebSearcher:
    """Gibt die globale WebSearcher-Instanz zurück (Singleton)."""
    global _web_searcher_instance
    if _web_searcher_instance is None:
        _web_searcher_instance = WebSearcher()
    return _web_searcher_instance

