"""File utility functions."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import get_settings

settings = get_settings()


def ensure_storage_dir() -> Path:
    """Ensure storage directory exists and return path."""
    storage_path = Path(settings.storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def get_file_path(filename: str) -> Path:
    """Get full path for a file in storage."""
    return ensure_storage_dir() / filename


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension."""
    ext = Path(original_filename).suffix.lower()
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


async def save_upload_file(upload_file: UploadFile) -> tuple[str, str, int]:
    """
    Save an uploaded file to storage.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        Tuple of (unique_filename, file_path, file_size)
    """
    ensure_storage_dir()

    original_filename = upload_file.filename or "unknown"
    unique_filename = generate_unique_filename(original_filename)
    file_path = get_file_path(unique_filename)

    # Write file in chunks
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await upload_file.read(8192):
            f.write(chunk)
            file_size += len(chunk)

    return unique_filename, str(file_path), file_size


def delete_file(filename: str) -> bool:
    """Delete a file from storage."""
    file_path = get_file_path(filename)
    if file_path.exists():
        file_path.unlink()
        return True
    return False
