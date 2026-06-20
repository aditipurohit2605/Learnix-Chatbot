import os
import logging

import google.generativeai as genai

from config import Config

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self):
        self.api_key = (
            getattr(Config, "GOOGLE_API_KEY", None)
            or os.environ.get("GOOGLE_API_KEY")
        )
        self.model = getattr(Config, "GOOGLE_MODEL", "gemini-2.0-flash")
        self.client_available = False

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.client_available = True
                logger.info("Gemini configured successfully.")
            except Exception:
                logger.exception("Gemini configuration failed")
                self.client_available = False
        else:
            logger.warning("No Gemini API key found. Offline fallback mode active.")

    def is_available(self):
        return self.client_available

    def get_completion(self, messages, use_search=False, web_context=None, **kwargs):
        """
        Generate a completion from Gemini. Returns text or None on failure.
        Never returns user-facing error strings.
        """
        if not self.client_available:
            return None

        generation_config = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            generation_config["max_output_tokens"] = kwargs["max_tokens"]

        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System Instructions:\n{content}")
            elif role == "user":
                prompt_parts.append(f"User:\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant:\n{content}")

        if web_context:
            prompt_parts.insert(
                1,
                f"Web Research Context (use to enrich your answer, cite when relevant):\n{web_context}",
            )

        prompt = "\n\n".join(prompt_parts)

        try:
            tools = None
            if use_search:
                try:
                    tools = [{"google_search_retrieval": {}}]
                except Exception:
                    tools = None

            model = genai.GenerativeModel(model_name=self.model, tools=tools)
            response = model.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None,
            )

            if hasattr(response, "text") and response.text:
                return response.text.strip()

            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                text = "".join(
                    p.text for p in parts if hasattr(p, "text") and p.text
                ).strip()
                if text:
                    return text

            return None

        except Exception:
            logger.exception("Gemini API error")
            if use_search:
                try:
                    model = genai.GenerativeModel(model_name=self.model)
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config if generation_config else None,
                    )
                    if hasattr(response, "text") and response.text:
                        return response.text.strip()
                except Exception:
                    logger.exception("Gemini fallback error")
            return None


ai_client = AIClient()
