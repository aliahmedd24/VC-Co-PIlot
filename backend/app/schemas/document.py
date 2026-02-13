from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    id: str
    name: str
    type: DocumentType
    status: DocumentStatus
    mime_type: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
