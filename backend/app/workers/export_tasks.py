import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="export_artifact_pdf", bind=True, max_retries=3)  # type: ignore[untyped-decorator]
def export_artifact_pdf(self: object, artifact_id: str) -> dict[str, str]:
    """Export an artifact to PDF and upload to S3.

    Uses sync SQLAlchemy with psycopg2 (Celery workers are sync).
    """
    from sqlalchemy import create_engine

    from app.config import settings
    from app.core.artifacts.exporters.pdf_exporter import pdf_exporter
    from app.models.artifact import Artifact
    from app.services.storage_service import storage_service

    sync_url = (
        settings.database_url
        .replace("+asyncpg", "+psycopg2")
        .replace("postgresql+psycopg2", "postgresql")
    )
    engine = create_engine(sync_url)
    sync_session_factory = sessionmaker(bind=engine)

    with sync_session_factory() as db:
        db_typed: Session = db
        result = db_typed.execute(
            select(Artifact).where(Artifact.id == uuid.UUID(artifact_id))
        )
        artifact = result.scalar_one_or_none()

        if artifact is None:
            return {"status": "error", "message": "Artifact not found"}

        try:
            pdf_bytes = pdf_exporter.export(
                artifact.type, artifact.title, artifact.content
            )
            storage_key = storage_service.upload_file(
                pdf_bytes, "application/pdf", prefix="exports"
            )
            return {"status": "success", "storage_key": storage_key}
        except Exception as exc:
            logger.error(
                "pdf_export_failed",
                artifact_id=artifact_id,
                error=str(exc),
            )
            return {"status": "error", "message": str(exc)}
