"""S3/MinIO storage service."""

from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings


class StorageService:
    """S3-compatible storage service for file uploads.

    Uses MinIO in development and can be configured for AWS S3
    or other S3-compatible services in production.
    """

    def __init__(self):
        """Initialize the storage client."""
        self.bucket = settings.s3_bucket

        # Configure S3 client
        config = Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
        )

        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.s3_access_key,
            "aws_secret_access_key": settings.s3_secret_key,
            "region_name": settings.s3_region,
            "config": config,
        }

        # Use custom endpoint for MinIO
        if settings.s3_endpoint:
            client_kwargs["endpoint_url"] = settings.s3_endpoint

        self.client = boto3.client(**client_kwargs)

        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchBucket"):
                self.client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration={"LocationConstraint": settings.s3_region}
                    if settings.s3_region != "us-east-1"
                    else {},
                )

    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a file to storage.

        Args:
            file: File-like object to upload.
            key: Storage key (path) for the file.
            content_type: Optional MIME type.

        Returns:
            The storage key.
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
        return key

    async def upload_bytes(
        self,
        content: bytes,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Upload bytes to storage.

        Args:
            content: Bytes to upload.
            key: Storage key for the file.
            content_type: Optional MIME type.

        Returns:
            The storage key.
        """
        return await self.upload_file(BytesIO(content), key, content_type)

    async def download_file(self, key: str) -> bytes:
        """Download a file from storage.

        Args:
            key: Storage key of the file.

        Returns:
            File content as bytes.
        """
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    async def delete_file(self, key: str) -> None:
        """Delete a file from storage.

        Args:
            key: Storage key of the file.
        """
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """Generate a presigned URL for file access.

        Args:
            key: Storage key of the file.
            expires_in: URL expiration time in seconds.
            method: S3 method ('get_object' or 'put_object').

        Returns:
            Presigned URL string.
        """
        return self.client.generate_presigned_url(
            ClientMethod=method,
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage.

        Args:
            key: Storage key to check.

        Returns:
            True if file exists.
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get or create the storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
