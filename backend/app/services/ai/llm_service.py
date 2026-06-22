from ollama import chat


class LLMService:

    @staticmethod
    def answer(
        question: str,
        context: str
    ):

        prompt = f"""
You are RIIDL AI Assistant.

Answer ONLY from the provided context.

If the answer exists in context:
- Give a clear answer.
- Summarize intelligently.
- Mention relevant details.

If the answer does NOT exist:

Reply exactly:

I could not find that information in the available emails or documents.

CONTEXT:

{context}

QUESTION:

{question}

ANSWER:
"""

        response = chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]