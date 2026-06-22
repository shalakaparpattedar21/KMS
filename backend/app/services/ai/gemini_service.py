import google.generativeai as genai
from app.core.config import settings
genai.configure(
    api_key=settings.GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


class GeminiService:

    @staticmethod
    def answer_question(
        question: str,
        context: str,
        conversation_history: str = ""
    ):

        prompt = f"""
You are an Enterprise Knowledge Assistant.

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

Provide a helpful, concise answer.
"""

        print(f"[GEMINI] Generating response for: {question}\n")

        return prompt

    @staticmethod
    def stream_answer(prompt: str):
        """Stream the response from Gemini with error handling"""
        try:
            response = model.generate_content(
                prompt,
                stream=True
            )
            
            full_text = ""
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    yield chunk.text
            
            print(f"[GEMINI] Streaming complete\n")
        
        except Exception as e:
            error_msg = str(e)
        
            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                fallback = "⚠️ API quota exceeded. Please try again in a minute or upgrade your plan: https://aistudio.google.com"
                yield fallback
                print(f"[GEMINI ERROR] Rate limit hit - returned fallback response\n")
            else:
                fallback = f"⚠️ Error: {error_msg[:100]}"
                yield fallback
                print(f"[GEMINI ERROR] {error_msg}\n")