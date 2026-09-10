"""AWS S3 storage helpers for generated reports.

Uses the default boto3 credential chain, so production deployments can use an
IAM role instead of storing AWS access keys in the application.
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def _client():
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_REGION", "ap-south-1"),
    )


def upload_report(file_path: str, object_key: str) -> Optional[str]:
    """Upload a generated report to S3 and return a presigned download URL.

    S3 upload is optional: if AWS_S3_BUCKET is not configured, the application
    continues using local file storage. This keeps local development unchanged.
    """
    bucket = os.environ.get("AWS_S3_BUCKET")
    if not bucket:
        return None

    try:
        client = _client()

        client.upload_file(
            file_path,
            bucket,
            object_key,
            ExtraArgs={
                "ContentType": _content_type(file_path),
            },
        )

        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
            },
            ExpiresIn=3600,
        )

    except (BotoCoreError, ClientError) as exc:
        # Report generation/download should not fail just because S3 is
        # temporarily unavailable. The local file remains available.
        print(f"S3 upload failed: {exc}")
        return None


def _content_type(file_path: str) -> str:
    if file_path.lower().endswith(".pptx"):
        return (
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        )

    if file_path.lower().endswith(".docx"):
        return (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    return "application/octet-stream"
