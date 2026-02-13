import uuid

import boto3
import structlog
from botocore.exceptions import ClientError

from app.config import settings

logger = structlog.get_logger()


class StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket_name

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)
            logger.info("s3_bucket_created", bucket=self.bucket)

    def upload_file(self, file_data: bytes, content_type: str, prefix: str = "documents") -> str:
        self._ensure_bucket()
        key = f"{prefix}/{uuid.uuid4().hex}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_data,
            ContentType=content_type,
        )
        logger.info("s3_file_uploaded", key=key, size=len(file_data))
        return key

    def download_file(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        data: bytes = response["Body"].read()
        return data

    def delete_file(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)
        logger.info("s3_file_deleted", key=key)


storage_service = StorageService()
