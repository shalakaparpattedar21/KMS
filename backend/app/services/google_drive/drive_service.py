import requests


class DriveService:

    @staticmethod
    def get_files(access_token: str):

        response = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            params={
                "pageSize": 100,
                "fields": (
                    "files("
                    "id,"
                    "name,"
                    "mimeType,"
                    "owners,"
                    "size,"
                    "modifiedTime,"
                    "webViewLink"
                    ")"
                )
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def download_file(
        access_token: str,
        file_id: str
    ):
        """
        Downloads regular files:
        PDF, DOCX, TXT, etc.
        """

        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        response.raise_for_status()

        return response.content

    @staticmethod
    def export_google_doc(
        access_token: str,
        file_id: str
    ):
        """
        Exports Google Docs as plain text.
        """

        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
            params={
                "mimeType": "text/plain"
            },
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        response.raise_for_status()

        return response.text