import os
import uuid
from datetime import datetime
from typing import Protocol
from fastapi import UploadFile

class StorageProvider(Protocol):
    async def save_file(self, file: UploadFile, directory: str, filename_prefix: str = "") -> dict:
        ...

    def get_file_path(self, file_path: str) -> str:
        ...


class LocalStorageProvider:
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = base_upload_dir
        if not os.path.exists(self.base_upload_dir):
            os.makedirs(self.base_upload_dir)

    async def save_file(self, file: UploadFile, directory: str, filename_prefix: str = "") -> dict:
        # Create full directory path
        full_dir = os.path.join(self.base_upload_dir, directory)
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)

        # Generate unique filename: {timestamp}_{uuid}_{original_filename}
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = file.filename.replace(" ", "_")
        
        if filename_prefix:
            stored_filename = f"{filename_prefix}_{timestamp}_{unique_id}_{safe_filename}"
        else:
            stored_filename = f"{timestamp}_{unique_id}_{safe_filename}"
            
        file_path = os.path.join(full_dir, stored_filename)

        # Calculate file size while saving
        file_size = 0
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024) # read 1MB chunks
                if not chunk:
                    break
                buffer.write(chunk)
                file_size += len(chunk)
                
        # Return metadata
        return {
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": file.content_type
        }

    def get_file_path(self, file_path: str) -> str:
        # In a cloud provider, this might return a signed URL.
        # For local storage, we just return the absolute path to serve the file directly.
        if os.path.isabs(file_path):
            return file_path
        return os.path.abspath(file_path)

# Singleton instance
storage_provider = LocalStorageProvider()
