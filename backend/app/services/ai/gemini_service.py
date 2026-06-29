# app/services/ai/gemini_service.py
#
# MIGRATED: google-generativeai → google-genai (latest stable SDK)
#
# What changed:
#   - Old: genai.GenerativeModel().generate_content(prompt, stream=True)
#   - New: client.models.generate_content_stream()
#
# Used only for the follow-up conversational path in chat/routes.py.
# The public interface (GeminiService.answer_question / stream_answer)
# is UNCHANGED so chat/routes.py requires no modifications.

import logging
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

_MODEL = "gemini-2.5-flash"


class GeminiService:

    @staticmethod
    def answer_question(
        question: str,
        context: str,
        conversation_history: str = ""
    ) -> str:
        """
        Build the full prompt for a conversational / follow-up question.
        Returns the assembled prompt string (not a response).
        stream_answer() calls Gemini with this prompt.
        """
        prompt = f"""You are an Enterprise Knowledge Assistant.

You help users understand information found in company documents.

You are given:
1. Conversation History
2. Document Context
3. User Question

RULES:

1. If the user asks a follow-up question (elaborate, explain, why, how, etc):
   - Use the conversation history to understand what they're asking about.
   - Expand upon your previous answer with more details, examples, and explanations.
   - Reference concepts from your previous answer.
   - Do NOT say "I could not find that information" for follow-up questions.

2. If document context IS provided:
   - Answer using the document as the primary source.
   - Be accurate and concise.

3. For new questions without context:
   - Respond: "I could not find that information in the documents."

Conversation History:
{conversation_history}

Document Context:
{context}

Current Question:
{question}

Provide a clear, professional answer.

If the answer exists in the supplied document context,
summarize it naturally instead of copying sentences.

If the information is unavailable and this is NOT a follow-up question,
reply exactly:

"I could not find that information in the available documents.\""""

        logger.debug(f"[GEMINI] Prompt built for: {question!r}")
        return prompt

    @staticmethod
    def stream_answer(prompt: str):
        """
        Stream the response from Gemini using generate_content_stream.
        Yields text chunks as they arrive.
        """
        if _client is None:
            yield "AI responses unavailable — GEMINI_API_KEY is not configured."
            return

        try:
            for chunk in _client.models.generate_content_stream(
                model=_MODEL,
                contents=prompt,
            ):
                text = chunk.text
                if text:
                    yield text

            logger.debug("[GEMINI] Streaming complete")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[GEMINI ERROR] {error_msg}")

            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                yield (
                    "AI service is temporarily unavailable because the usage quota "
                    "has been reached. Please try again in a few minutes."
                )
            else:
                yield "AI response temporarily unavailable. Please try again."