class TextExtractionService:

    @staticmethod
    def extract_google_doc(text: str) -> str:
        return text

    @staticmethod
    def extract_txt(file_bytes: bytes) -> str:
        return file_bytes.decode(
            "utf-8",
            errors="ignore"
        )