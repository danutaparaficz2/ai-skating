"""RAG-Generator für Athleten-Informationen."""

import logging
from typing import Optional, Dict, Any, List

from .config import GeneratorConfig
from .retriever import FAISSRetriever
from .llm_client import QwenClient
from .prompts import PromptTemplates
from .web_search import get_web_searcher

logger = logging.getLogger(__name__)


class RAGGenerator:
    """RAG-Generator kombiniert FAISS-Retrieval mit Qwen LLM."""

    def __init__(self, config: Optional[GeneratorConfig] = None):
        """
        Initialisiert den RAG-Generator.

        Args:
            config: Generator-Konfiguration
        """
        self.config = config or GeneratorConfig()
        self.config.validate()

        # Initialisiere Komponenten
        self.retriever = FAISSRetriever(
            faiss_index_path=self.config.faiss_index_path,
            mongo_uri=self.config.mongo_uri,
            mongo_db=self.config.mongo_db,
            mongo_collection=self.config.mongo_collection,
            embedding_model=self.config.embedding_model
        )

        self.llm = QwenClient(
            api_key=self.config.qwen_api_key,
            base_url=self.config.qwen_base_url,
            model=self.config.qwen_model
        )

        # Web-Searcher (Singleton)
        self.web_searcher = get_web_searcher()

        logger.info("RAG-Generator initialisiert")

    def generate(
        self,
        query: str,
        athlete_name: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generiert eine Antwort basierend auf der Query mit RAG.

        Args:
            query: Benutzer-Frage
            athlete_name: Optional: Filter auf bestimmten Athleten
            include_sources: Ob Quellen in Response inkludiert werden sollen

        Returns:
            Dictionary mit 'answer', 'sources' und 'metadata'
        """
        logger.info(f"Generiere Antwort für Query: '{query[:50]}...'")

        # 1. Retrieve: Hole relevante Chunks aus FAISS
        chunks = self.retriever.retrieve(
            query=query,
            athlete_name=athlete_name,
            top_k=self.config.top_k_chunks,
            min_similarity=self.config.min_similarity
        )

        if not chunks:
            return {
                "answer": "Leider habe ich keine relevanten Informationen zu dieser Frage gefunden.",
                "sources": [],
                "metadata": {
                    "chunks_used": 0,
                    "athlete_filter": athlete_name
                }
            }

        # 2. Prepare: Erstelle Kontext aus Chunks
        context = self._format_context(chunks)

        # 3. Prompt: Baue RAG-Prompt
        prompt = self._build_rag_prompt(query, context, athlete_name)

        # 4. Generate: LLM-Generierung
        answer = self.llm.generate(
            prompt=prompt,
            system_prompt=self.config.system_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        # 5. Response zusammenstellen
        response = {
            "answer": answer.strip(),
            "sources": self._format_sources(chunks) if include_sources else [],
            "metadata": {
                "chunks_used": len(chunks),
                "athlete_filter": athlete_name,
                "model": self.config.qwen_model,
                "top_similarity": chunks[0]["similarity"] if chunks else 0.0
            }
        }

        logger.info(f"Antwort generiert (Chunks: {len(chunks)})")
        return response

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Formatiert Chunks zu Kontext-String."""
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Information {i}]\n"
                f"Athlet: {chunk['athlete_name']}\n"
                f"Text: {chunk['text']}\n"
            )

        return "\n".join(context_parts)

    def _build_rag_prompt(
        self,
        query: str,
        context: str,
        athlete_name: Optional[str] = None
    ) -> str:
        """Baut den RAG-Prompt."""

        prompt = f"""Basierend auf den folgenden Informationen über Short-Track-Athleten, beantworte die Frage des Nutzers.

KONTEXT:
{context} 

FRAGE: {query}
"""

        if athlete_name:
            prompt += f"\n(Fokus auf Athlet: {athlete_name})"

        prompt += """

ANTWORT:
Gib eine präzise, informative Antwort basierend auf dem bereitgestellten Kontext. 
Wenn die Information nicht im Kontext vorhanden ist, sage das klar.
Zitiere relevante Details aus dem Kontext wenn passend."""

        return prompt

    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formatiert Chunks zu Source-Referenzen."""
        sources = []

        for i, chunk in enumerate(chunks, 1):
            sources.append({
                "id": i,
                "athlete": chunk["athlete_name"],
                "similarity": round(chunk["similarity"], 3),
                "url": chunk.get("metadata", {}).get("url", ""),
                "topic": chunk.get("metadata", {}).get("topic", ""),
                "preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            })

        return sources

    def chat(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        athlete_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat-Funktion mit Conversation-History.

        Args:
            query: Aktuelle Frage
            conversation_history: Bisherige Chat-Nachrichten
            athlete_name: Optional Athlet-Filter

        Returns:
            Response mit Answer und aktualisierter History
        """
        # Hole Kontext für aktuelle Query
        chunks = self.retriever.retrieve(
            query=query,
            athlete_name=athlete_name,
            top_k=self.config.top_k_chunks,
            min_similarity=self.config.min_similarity
        )

        context = self._format_context(chunks) if chunks else "Keine relevanten Informationen gefunden."

        # Baue Messages
        messages = []

        # System Prompt
        messages.append({
            "role": "system",
            "content": self.config.system_prompt + f"\n\nAktueller Kontext:\n{context}"
        })

        # History
        if conversation_history:
            messages.extend(conversation_history)

        # Aktuelle Query
        messages.append({
            "role": "user",
            "content": query
        })

        # LLM Call
        response = self.llm.chat_completion(
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        answer = response['choices'][0]['message']['content']

        # Aktualisiere History
        updated_history = (conversation_history or []) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer}
        ]

        return {
            "answer": answer,
            "conversation_history": updated_history,
            "sources": self._format_sources(chunks),
            "metadata": {
                "chunks_used": len(chunks),
                "athlete_filter": athlete_name
            }
        }

    def generate_story(
        self,
        athlete_name: str,
        story_type: str = "profile",
        style: str = "engaging",
        enable_web_search: bool = True
    ) -> Dict[str, Any]:
        """
        Generiert eine Story über einen Athleten.

        Args:
            athlete_name: Name des Athleten
            story_type: Art der Story ("profile", "achievement", "journey")
            style: Schreibstil ("engaging", "formal", "dramatic")
            enable_web_search: Ob Websuche aktiviert werden soll (default: True)

        Returns:
            Dictionary mit 'story', 'sources', 'metadata' und 'web_search_enabled'
        """
        logger.info(f"Generiere Story für: {athlete_name} (Typ: {story_type}, Stil: {style})")

        # 1. Hole umfassende Informationen über den Athleten aus FAISS - SPORTLICHER FOKUS
        chunks = self.retriever.retrieve(
            query=f"{athlete_name} training performance competition form results",
            athlete_name=athlete_name,
            top_k=10,
            min_similarity=0.2
        )

        # 2. Formatiere FAISS-Kontext
        if chunks:
            faiss_context = self._format_context(chunks)
        else:
            # Professioneller Fallback ohne "keine Informationen"
            faiss_context = f"({athlete_name} ist ein aufstrebender Short-Track Athlet mit vielversprechendem Potential.)"

        # 3. Web-Suche (falls aktiviert) - FOKUS AUF SPORTLICHE FORM
        web_context = ""
        web_results = []

        if enable_web_search:
            logger.info(f"🌐 Führe Web-Suche durch für Story: {athlete_name}")
            try:
                # Suche nach SPORTLICHEN Informationen - Form, Training, Wettkämpfe
                web_results = self.web_searcher.search(
                    f"{athlete_name} short track training performance 2025 results",
                    num_results=5
                )
                if web_results:
                    web_context = self.web_searcher.format_results_for_context(web_results)
                    logger.info(f"✅ {len(web_results)} Web-Ergebnisse für Story gefunden")
            except Exception as e:
                logger.error(f"Web-Suche für Story fehlgeschlagen: {e}")
                web_context = ""

        # 4. Kombiniere Kontext
        if enable_web_search and web_context:
            combined_context = f"""=== DATENBANK ===
{faiss_context}

=== WEB-RECHERCHE ===
{web_context}
"""
        else:
            combined_context = faiss_context

        # 5. Story-spezifischer Prompt
        prompts = {
            "profile": f"Erstelle ein professionelles Athleten-Profil über {athlete_name} für die offizielle Website.",
            "achievement": f"Beschreibe die sportlichen Erfolge von {athlete_name} in einem packenden Feature-Stil.",
            "journey": f"Erzähle die Karriere-Geschichte von {athlete_name} als fesselnden Sport-Artikel."
        }

        style_instructions = {
            "engaging": "Schreibe in einem mitreißenden, journalistischen Stil der Leser fesselt.",
            "formal": "Verwende einen professionellen, sachlichen Sport-Journalismus Stil.",
            "dramatic": "Nutze einen packenden, emotionalen Erzählstil mit Spannung."
        }

        prompt = f"""{prompts.get(story_type, prompts['profile'])}
{style_instructions.get(style, style_instructions['engaging'])}

WICHTIG: 
- Fasse dich KURZ - maximal 2-3 prägnante Sätze
- Schreibe positiv und professionell
- NIEMALS erwähnen dass Informationen fehlen
- Fokus auf verfügbare Stärken und Potenzial

VERFÜGBARE INFORMATIONEN:
{combined_context}

DEIN PROFIL-TEXT (2-3 Sätze):"""

        system_prompt = "Du bist ein erfahrener Sportjournalist, der fesselnde Geschichten über Athleten schreibt. Halte dich KURZ - maximal 2-3 Sätze!"
        if enable_web_search:
            system_prompt += " Du hast Zugang zu aktuellen Informationen aus dem Internet."

        story = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=200  # Kurze Antwort (2-3 Sätze)
        )

        return {
            "story": story.strip(),
            "sources": self._format_sources(chunks),
            "web_sources": [
                {
                    "id": i,
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", "")[:150],
                    "url": r.get("url", "")
                }
                for i, r in enumerate(web_results, 1)
            ] if enable_web_search and web_results else [],
            "metadata": {
                "chunks_used": len(chunks),
                "web_results_used": len(web_results) if enable_web_search else 0,
                "athlete_name": athlete_name,
                "story_type": story_type,
                "style": style,
                "web_search_enabled": enable_web_search,
                "model": self.config.qwen_model
            },
            "web_search_enabled": enable_web_search
        }

    def generate_private_update(
        self,
        athlete_name: str,
        enable_web_search: bool = True
    ) -> Dict[str, Any]:
        """
        Generiert ein Private Update für einen Athleten.

        👉 FEST KODIERT: Fragt automatisch nach privatem Umfeld und anstehenden Turnieren.

        Args:
            athlete_name: Name des Athleten
            enable_web_search: Ob Websuche aktiviert werden soll (empfohlen: True)

        Returns:
            Dictionary mit 'answer', 'sources', 'metadata' und 'web_search_enabled'
        """
        logger.info(f"Generiere Private Update für: {athlete_name}")

        # 1. Hole relevante Chunks aus FAISS
        chunks = self.retriever.retrieve(
            query=f"{athlete_name} personal life family hobbies interests personality",
            athlete_name=athlete_name,
            top_k=8,  # Mehr Kontext für umfassendes Update
            min_similarity=0.2  # Niedrigerer Threshold für mehr Informationen
        )

        # 2. Formatiere FAISS-Kontext
        if chunks:
            faiss_context = self._format_context(chunks)
        else:
            faiss_context = "(Keine Informationen in der lokalen Datenbank verfügbar)"

        # 3. Führe Web-Suche durch (falls aktiviert) - FOKUS AUF PRIVATES LEBEN
        web_context = ""
        web_results = []

        if enable_web_search:
            logger.info(f"🌐 Führe Web-Suche durch für: {athlete_name}")

            # Suche nach PRIVATEM UMFELD - nicht sportliche Erfolge!
            search_queries = [
                f"{athlete_name} family personal life",
                f"{athlete_name} hobbies interests hometown",
                f"{athlete_name} personality background"
            ]

            all_web_results = []
            for search_query in search_queries:
                try:
                    results = self.web_searcher.search(search_query, num_results=3)
                    all_web_results.extend(results)
                except Exception as e:
                    logger.error(f"Web-Suche fehlgeschlagen für '{search_query}': {e}")

            if all_web_results:
                web_results = all_web_results[:5]  # Top 5 Web-Ergebnisse
                web_context = self.web_searcher.format_results_for_context(web_results)
                logger.info(f"✅ {len(web_results)} Web-Ergebnisse gefunden")
            else:
                web_context = "(Keine aktuellen Web-Ergebnisse verfügbar)"
                logger.warning("⚠️ Keine Web-Ergebnisse gefunden")

        # 4. Kombiniere FAISS + Web-Kontext
        combined_context = f"""=== LOKALE DATENBANK (FAISS) ===
{faiss_context}

=== AKTUELLE WEB-SUCHE ===
{web_context if enable_web_search else '(Web-Suche deaktiviert)'}
"""

        # 5. Baue fest kodierten Prompt
        prompt = PromptTemplates.build_private_update_prompt(
            athlete_name=athlete_name,
            context=combined_context,
            enable_web_search=enable_web_search
        )

        # 6. Generiere Antwort mit LLM
        answer = self.llm.generate(
            prompt=prompt,
            system_prompt=PromptTemplates.SYSTEM_PRIVATE_UPDATE,
            temperature=0.7,
            max_tokens=200  # Kurze Antwort (2-3 Sätze)
        )

        # 7. Baue Response
        response = {
            "answer": answer.strip(),
            "sources": self._format_sources(chunks) if chunks else [],
            "web_sources": [
                {
                    "id": i,
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", "")[:150],
                    "url": r.get("url", "")
                }
                for i, r in enumerate(web_results, 1)
            ] if enable_web_search and web_results else [],
            "metadata": {
                "athlete_name": athlete_name,
                "chunks_used": len(chunks),
                "web_results_used": len(web_results) if enable_web_search else 0,
                "web_search_enabled": enable_web_search,
                "model": self.config.qwen_model,
                "query_type": "private_update"
            },
            "web_search_enabled": enable_web_search
        }

        logger.info(f"Private Update generiert (FAISS: {len(chunks)} Chunks, Web: {len(web_results) if enable_web_search else 0} Ergebnisse)")
        return response

    def close(self):
        """Schließt alle Verbindungen."""
        self.retriever.close()
        logger.info("RAG-Generator geschlossen")

