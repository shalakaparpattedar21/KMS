# app/services/ai/llm_service.py
#
# MIGRATED: google-generativeai → google-genai (latest stable SDK)
#
# What changed:
#   - Old: genai.GenerativeModel("gemini-2.5-flash") / model.generate_content()
#   - New: genai.Client() / client.models.generate_content()
#
# Model stays as gemini-2.5-flash — correct current model name.
# The public interface (LLMService.answer / LLMService.draft_email_reply)
# is UNCHANGED so chat/routes.py requires no modifications.

import logging
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

_MODEL = "gemini-2.5-flash"

_SYSTEM = (
    "You are RIIDL AI Assistant. "
    "Answer ONLY from the provided context. "
    "If the answer exists in context, give a clear, intelligent summary. "
    "If it does NOT exist, reply exactly: "
    "I could not find that information in the available emails or documents."
)

_DRAFT_SYSTEM = (
    "You are RIIDL AI Assistant helping draft a professional email reply. "
    "Write ONLY the reply body — no Subject, To, From, or headers. "
    "Match the tone to the instruction (professional by default). "
    "Be concise and clear. Do not invent information not in the original email. "
    "End with an appropriate sign-off."
)


class LLMService:

    @staticmethod
    def answer(question: str, context: str) -> str:
        """
        Answer a user question from retrieved context using Gemini.
        Falls back to a safe message if Gemini is unavailable.
        """
        if _client is None:
            return (
                "AI responses are currently unavailable — GEMINI_API_KEY is not set. "
                "Please configure it in the Render environment variables."
            )

        prompt = (
            f"{_SYSTEM}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}\n\n"
            f"ANSWER:"
        )

        try:
            response = _client.models.generate_content(
                model=_MODEL,
                contents=prompt,
            )
            text = response.text
            return text if text else "I couldn't generate a response for this query."

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[LLM] Gemini error: {error_msg}")

            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                return (
                    "AI service is temporarily unavailable because the usage quota "
                    "has been reached. Please try again in a few minutes."
                )
            return "AI response temporarily unavailable. Please try again."

    @staticmethod
    def draft_email_reply(
        original_subject: str,
        original_sender: str,
        original_body: str,
        instruction: str,
    ) -> str:
        """
        Generate a draft email reply using Gemini.
        """
        if _client is None:
            return "AI draft unavailable — GEMINI_API_KEY is not set."

        prompt = (
            f"{_DRAFT_SYSTEM}\n\n"
            f"ORIGINAL EMAIL:\n"
            f"From: {original_sender}\n"
            f"Subject: {original_subject}\n"
            f"Body:\n{original_body}\n\n"
            f"USER INSTRUCTION:\n{instruction}\n\n"
            f"DRAFT REPLY:"
        )

        try:
            response = _client.models.generate_content(
                model=_MODEL,
                contents=prompt,
            )
            return response.text or "Could not generate draft — please try again."

        except Exception as e:
            logger.error(f"[LLM] Gemini draft error: {e}")
            return "Could not generate draft — please try again."