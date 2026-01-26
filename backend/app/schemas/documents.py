"""Pydantic schemas for Document API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class DocumentTypeEnum(str, Enum):
    """Document type classification."""

    PITCH_DECK = "pitch_deck"
    FINANCIAL_MODEL = "financial_model"
    BUSINESS_PLAN = "business_plan"
    PRODUCT_DOC = "product_doc"
    OTHER = "other"


class DocumentStatusEnum(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


# --- Upload Schemas ---


class DocumentUpload(BaseModel):
    """Schema for document upload request."""

    document_type: DocumentTypeEnum = DocumentTypeEnum.OTHER
    venture_id: str | None = None  # Optional, uses workspace default


class DocumentResponse(BaseModel):
    """Schema for document API responses."""

    id: str
    workspace_id: str
    name: str
    type: DocumentTypeEnum
    mime_type: str
    size: int
    status: DocumentStatusEnum
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""

    documents: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Response after successful upload."""

    document: DocumentResponse
    message: str = "Document uploaded successfully. Processing started."


class DocumentDownloadResponse(BaseModel):
    """Response with download URL."""

    url: str
    expires_in: int = 3600


# --- Chunk Schemas ---


class ChunkResponse(BaseModel):
    """Schema for document chunk responses."""

    id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class DocumentChunksResponse(BaseModel):
    """Response listing document chunks."""

    document_id: str
    chunks: list[ChunkResponse]
    total: int
