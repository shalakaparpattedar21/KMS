#backend/app/services/gmail/gmail_service.py

import base64
import requests
from email.mime.text import MIMEText


class GmailService:

    @staticmethod
    def send_email(
        access_token: str,
        to: str,
        subject: str,
        body: str
    ):
        """
        Send a new email
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            response = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"raw": raw_message}
            )

            return response.json()

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def reply_email(
        access_token: str,
        message_id: str,
        thread_id: str,
        content: str
    ):
        """
        Reply to an email within same thread
        """
        try:
            message = MIMEText(content)
            message['thread_id'] = thread_id

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            response = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "raw": raw_message,
                    "threadId": thread_id
                }
            )

            return response.json()

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def forward_email(
        access_token: str,
        message_id: str,
        recipient: str,
        content: str = ""
    ):
        try:

            response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            original = response.json()

            print("[FORWARD] ORIGINAL EMAIL:")
            print(original)

            payload = original.get(
                "payload",
                {}
            )

            headers = payload.get(
                "headers",
                []
            )

            subject = "No Subject"

            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                    break

            forwarded_body = f"""
{content}

-------------------------
FORWARDED EMAIL
-------------------------

Subject: {subject}

Message ID:
{message_id}
"""

            message = MIMEText(
                forwarded_body
            )

            message["to"] = recipient
            message["subject"] = f"Fwd: {subject}"

            raw_message = (
                base64.urlsafe_b64encode(
                    message.as_bytes()
                ).decode()
            )

            send_response = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "raw": raw_message
                }
            )

            print(
                "[FORWARD] GMAIL RESPONSE:"
            )

            print(
                send_response.json()
            )

            return send_response.json()

        except Exception as e:
            return {
                "error": str(e)
            }
    @staticmethod
    def create_draft(
        access_token: str,
        to: str,
        subject: str,
        body: str
    ):
        """
        Create a draft email (not sent)
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            response = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"message": {"raw": raw_message}}
            )

            return response.json()

        except Exception as e:
            return {"error": str(e)}