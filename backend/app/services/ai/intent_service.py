class IntentService:

    @staticmethod
    def detect(question: str):

        q = question.lower()

        if (
            "emails from" in q
            or "mail from" in q
            or "mails sent by" in q
            or "emails sent by" in q
        ):
            return {
                "intent": "search_sender"
            }

        return {
            "intent": "semantic_search"
        }