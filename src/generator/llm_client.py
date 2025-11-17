"""LLM Client für Alibaba Cloud Qwen API."""

import logging
import os
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class QwenClient:
    """Client für Alibaba Cloud Qwen API (OpenAI-kompatibel)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-turbo"
    ):
        """
        Initialisiert den Qwen Client.

        Args:
            api_key: Alibaba Cloud API Key (oder aus DASHSCOPE_API_KEY env)
            base_url: API Base URL
            model: Modell-Name (qwen-turbo, qwen-plus, qwen-max, qwen3-max)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY muss gesetzt sein!")

        self.base_url = base_url.rstrip('/')
        self.model = model

        logger.info(f"Qwen Client initialisiert mit Modell: {model}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.8,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Sendet Chat-Completion-Request an Qwen API.

        Args:
            messages: Liste von Messages [{"role": "user", "content": "..."}]
            temperature: Kreativität (0-2)
            max_tokens: Maximale Token-Anzahl
            top_p: Nucleus Sampling
            stream: Streaming aktivieren

        Returns:
            API Response
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }

        try:
            logger.debug(f"Sende Request an Qwen API: {len(messages)} messages")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Qwen API Response erhalten (Tokens: {result.get('usage', {}).get('total_tokens', 'N/A')})")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API Fehler: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Einfache Text-Generierung.

        Args:
            prompt: User Prompt
            system_prompt: Optional System Prompt
            temperature: Kreativität
            max_tokens: Max Tokens

        Returns:
            Generierter Text
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response['choices'][0]['message']['content']

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generierung mit Kontext (für RAG).

        Args:
            query: Benutzer-Frage
            context: RAG-Kontext
            system_prompt: System Prompt
            temperature: Kreativität
            max_tokens: Max Tokens

        Returns:
            Generierte Antwort
        """
        prompt = f"""Kontext:
{context}

Frage: {query}

Antwort basierend auf dem Kontext:"""

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

