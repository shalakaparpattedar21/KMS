from app.database.base import Base
from app.database.session import engine
from app.models.document_content import DocumentContent
from app.models.user import User
from app.models.document import Document
from app.models.email import Email

def init_db():
    print("Registered tables:", Base.metadata.tables.keys())

    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully")