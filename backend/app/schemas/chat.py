from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    id: int
    title: str


class SendMessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    role: str
    content: str


class SessionResponse(BaseModel):
    id: int
    title: str

