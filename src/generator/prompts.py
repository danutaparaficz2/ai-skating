"""Prompt-Templates für den RAG-Generator."""

from typing import Optional


class PromptTemplates:
    """Verwaltet alle Prompt-Templates für verschiedene Use-Cases."""

    # ============================================================================
    # SYSTEM PROMPTS
    # ============================================================================

    SYSTEM_QA = """Du bist ein Experte für Eisschnelllauf und Short-Track.
Beantworte Fragen präzise basierend auf dem gegebenen Kontext.
Wenn die Information nicht im Kontext vorhanden ist, sage das klar.
Verwende einen informativen, professionellen Ton."""

    SYSTEM_STORY = """Du bist ein professioneller Sport-Journalist der über Training und Wettkampf berichtet.
Dein Text wird im sportlichen Leistungs-Bereich des Athleten-Profils veröffentlicht.
Fokussiere dich auf SPORTLICHE FORM, Training, Wettkämpfe und Vorbereitung.
Schreibe in einem dynamischen, motivierenden Ton - zeige den Athleten in Action.
Erwähne NIEMALS dass keine Informationen verfügbar sind - fokussiere auf verfügbare sportliche Aspekte.
Bleibe bei den Fakten, füge keine erfundenen Details hinzu."""

    SYSTEM_CHAT = """Du bist ein freundlicher Assistent für Short-Track Eisschnelllauf.
Du beantwortest Fragen im Konversationsstil basierend auf dem Kontext.
Merke dir die bisherige Konversation und baue darauf auf."""

    # ============================================================================
    # USER PROMPT TEMPLATES (Q&A)
    # ============================================================================

    @staticmethod
    def build_qa_prompt(query: str, context: str, athlete_name: Optional[str] = None) -> str:
        """
        Erstellt einen Q&A Prompt.

        👉 ANPASSEN: Hier kannst du das Template für Fragen ändern!
        """
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

    @staticmethod
    def build_detailed_qa_prompt(query: str, context: str, athlete_name: Optional[str] = None) -> str:
        """
        Erstellt einen detaillierten Q&A Prompt mit mehr Struktur.

        👉 TEMPLATE 2: Für ausführlichere Antworten
        """
        prompt = f"""Du bist ein Experte für Short-Track Eisschnelllauf. Analysiere die folgenden Informationen und beantworte die Frage detailliert.

=== VERFÜGBARE INFORMATIONEN ===
{context}

=== FRAGE DES NUTZERS ===
{query}
"""

        if athlete_name:
            prompt += f"\n**Fokus:** {athlete_name}"

        prompt += """

=== DEINE AUFGABE ===
1. Analysiere die verfügbaren Informationen sorgfältig
2. Beantworte die Frage so detailliert wie möglich
3. Strukturiere deine Antwort klar (z.B. mit Aufzählungen wenn sinnvoll)
4. Nenne relevante Fakten und Details
5. Wenn Informationen fehlen, sage das explizit

=== ANTWORT ===
"""

        return prompt

    # ============================================================================
    # STORY TEMPLATES
    # ============================================================================

    STORY_PROMPTS = {
        "profile": "Beschreibe die aktuelle sportliche Form und Trainingsphase von {athlete_name}.",
        "achievement": "Berichte über die jüngsten sportlichen Leistungen und Wettkampfergebnisse von {athlete_name}.",
        "journey": "Erzähle wie {athlete_name} sich auf kommende Wettkämpfe vorbereitet und in welcher Form er ist.",
        "news": "Fasse die neuesten sportlichen Entwicklungen und Trainingshighlights von {athlete_name} zusammen.",
        "training": "Beschreibe den aktuellen Trainingsfokus und die Vorbereitung von {athlete_name}."
    }

    STYLE_INSTRUCTIONS = {
        "engaging": "Schreibe in einem dynamischen, mitreißenden Sportstil der Leser motiviert.",
        "formal": "Verwende einen professionellen, analytischen Sportstil wie in Fachmedien.",
        "dramatic": "Nutze einen packenden, spannungsgeladenen Erzählstil mit Energie.",
        "concise": "Halte dich kurz und knackig, fokussiere auf die sportlichen Kernpunkte.",
        "narrative": "Erzähle wie eine Sport-Reportage mit Spannung und Emotion."
    }

    # ============================================================================
    # PRIVATE UPDATE TEMPLATE (mit Websuche)
    # ============================================================================

    SYSTEM_PRIVATE_UPDATE = """Du bist ein professioneller Lifestyle- und Sport-Journalist, der über das private Umfeld von Athleten schreibt.
Dein Text wird im persönlichen Profil-Bereich des Athleten veröffentlicht.
Fokussiere dich auf PRIVATES LEBEN, Familie, Hobbys, Persönlichkeit - NICHT auf sportliche Erfolge.
Schreibe in einem warmen, menschlichen Ton - zeige den Menschen hinter dem Athleten.
Erwähne NIEMALS dass keine Informationen verfügbar sind - sei kreativ mit verfügbaren Infos.
Fasse dich kurz: 2-3 persönliche, packende Sätze."""

    @staticmethod
    def build_private_update_prompt(athlete_name: str, context: str, enable_web_search: bool = True) -> str:
        """
        Erstellt einen fest kodierten Prompt für Private Updates im Journalisten-Stil.

        👉 FOKUS: PRIVATES UMFELD - Familie, Hobbys, Persönlichkeit, NICHT sportliche Erfolge!

        Args:
            athlete_name: Name des Athleten
            context: Kontext aus FAISS-DB + Web
            enable_web_search: Ob Websuche aktiviert wurde

        Returns:
            Fertiger Prompt für LLM
        """
        prompt = f"""Schreibe ein kurzes, persönliches Update über das PRIVATE UMFELD von {athlete_name}.

VERFÜGBARE INFORMATIONEN:
{context}

JOURNALISTISCHE AUFGABE:
Erstelle einen warmherzigen 2-3 Sätze langen Text über das PRIVATE LEBEN, der:
- Das persönliche Umfeld beschreibt (Familie, Freunde, Heimat)
- Hobbys, Interessen oder Persönlichkeit zeigt
- Den Menschen hinter dem Athleten sichtbar macht
- In einem warmen, persönlichen Ton geschrieben ist

WICHTIGER FOKUS:
✓ PRIVATES LEBEN: Familie, Beziehungen, Freunde
✓ PERSÖNLICHKEIT: Hobbys, Interessen, Charaktereigenschaften
✓ HEIMAT: Wo lebt er, Verbindung zur Heimat
✓ PERSÖNLICHE ENTWICKLUNG: Was bewegt ihn privat
✗ NICHT über Wettkämpfe, Medaillen oder sportliche Erfolge schreiben
✗ NICHT über Training oder Leistung schreiben
✗ NIEMALS erwähnen dass Informationen fehlen

BEISPIEL-TON:
"Abseits der Eisbahn genießt {athlete_name} die Zeit mit seiner Familie in seiner niederländischen Heimat. Der 22-Jährige ist bekannt für seine ruhige, fokussierte Art und entspannt sich gerne bei ausgedehnten Fahrradtouren durch die holländische Landschaft."

ODER (falls wenig Info):
"Der junge Niederländer {athlete_name} ist bodenständig geblieben und pflegt enge Bindungen zu seiner Heimat. In seiner Freizeit schätzt er die Balance zwischen intensivem Sport und entspannten Momenten mit Familie und Freunden."

DEIN PRIVATES UPDATE (2-3 Sätze):"""

        return prompt

    @staticmethod
    def build_story_prompt(
        athlete_name: str,
        context: str,
        story_type: str = "profile",
        style: str = "engaging"
    ) -> str:
        """
        Erstellt einen Story-Prompt.

        👉 ANPASSEN: Hier kannst du Story-Templates ändern!

        Args:
            athlete_name: Name des Athleten
            context: Kontext-Informationen
            story_type: Art der Story (profile, achievement, journey, news, personal)
            style: Schreibstil (engaging, formal, dramatic, concise, narrative)
        """
        story_task = PromptTemplates.STORY_PROMPTS.get(
            story_type,
            PromptTemplates.STORY_PROMPTS["profile"]
        ).format(athlete_name=athlete_name)

        style_instruction = PromptTemplates.STYLE_INSTRUCTIONS.get(
            style,
            PromptTemplates.STYLE_INSTRUCTIONS["engaging"]
        )

        prompt = f"""{story_task}
{style_instruction}

INFORMATIONEN:
{context}

STORY (300-500 Wörter):"""

        return prompt

    # ============================================================================
    # CONTEXT FORMATTING
    # ============================================================================

    @staticmethod
    def format_context_simple(chunks: list) -> str:
        """Einfache Kontext-Formatierung (aktuell verwendet)."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Information {i}]\n"
                f"Athlet: {chunk['athlete_name']}\n"
                f"Text: {chunk['text']}\n"
            )
        return "\n".join(context_parts)

    @staticmethod
    def format_context_detailed(chunks: list) -> str:
        """
        Detaillierte Kontext-Formatierung mit mehr Metadaten.

        👉 ANPASSEN: Alternative Kontext-Formatierung
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            context_parts.append(
                f"=== Quelle {i} (Relevanz: {chunk['similarity']:.2%}) ===\n"
                f"Athlet: {chunk['athlete_name']}\n"
                f"Topic: {metadata.get('topic', 'N/A')}\n"
                f"URL: {metadata.get('url', 'N/A')}\n"
                f"\nInhalt:\n{chunk['text']}\n"
            )
        return "\n".join(context_parts)


# ============================================================================
# HELPER FUNKTIONEN
# ============================================================================

def get_system_prompt(prompt_type: str = "qa") -> str:
    """
    Holt den passenden System-Prompt.

    Args:
        prompt_type: "qa", "story", oder "chat"
    """
    prompts = {
        "qa": PromptTemplates.SYSTEM_QA,
        "story": PromptTemplates.SYSTEM_STORY,
        "chat": PromptTemplates.SYSTEM_CHAT
    }
    return prompts.get(prompt_type, PromptTemplates.SYSTEM_QA)

