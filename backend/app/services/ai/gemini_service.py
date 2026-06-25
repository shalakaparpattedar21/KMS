import logging

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash") if settings.GEMINI_API_KEY else None


class GeminiService:

    @staticmethod
    def answer_question(
        question: str,
        context: str,
        conversation_history: str = ""
    ) -> str:

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

"I could not find that information in the available documents."""

        logger.debug(f"[GEMINI] Generating response for: {question!r}")

        return prompt

    @staticmethod
    def stream_answer(prompt: str):
        """Stream the response from Gemini with error handling."""
        if model is None:
            yield "AI responses unavailable — GEMINI_API_KEY is not configured."
            return

        try:
            response = model.generate_content(prompt, stream=True)

            for chunk in response:
                text = getattr(chunk, "text", "")
                if text:
                    yield text

            logger.debug("[GEMINI] Streaming complete")

        except Exception as e:
            error_msg = str(e)

            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                fallback = (
                    "AI service is temporarily unavailable because the usage quota has been reached. Please try again in a few minutes."
                )
            else:
                fallback = (
                "AI response temporarily unavailable. Please try again."
            )

            logger.error(f"[GEMINI ERROR] {error_msg}")
            yield fallback
