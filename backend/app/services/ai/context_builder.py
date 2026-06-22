class ContextBuilder:

    @staticmethod
    def build(results):

        context = ""

        # Emails
        for email in results.get("emails", []):

            context += f"""
EMAIL

Subject:
{email.subject}

Sender:
{email.sender}

Body:
{email.body}

-------------------------
"""

        # Documents
        for doc in results.get("documents", []):

            context += f"""
DOCUMENT

Title:
{doc.name}
"""

            if hasattr(doc, "contents"):

                for content in doc.contents:

                    context += f"""
{content.content}
"""

            context += "\n-------------------------\n"

        return context