import filetype
import hashlib
import os
import shutil
import asyncio
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Vercel serverless environment filesystem is read-only except /tmp
if "VERCEL" in os.environ:
    VAULT_DIR = Path("/tmp/vault")
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    # Copy pre-existing vault files to /tmp/vault
    src_vault = Path("vault")
    if src_vault.exists():
        for item in src_vault.glob("**/*"):
            if item.is_file():
                relative_path = item.relative_to(src_vault)
                dest_path = VAULT_DIR / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                if not dest_path.exists():
                    try:
                        shutil.copy2(item, dest_path)
                    except Exception as e:
                        print(f"Error copying vault file {item} to /tmp/vault: {e}")
else:
    VAULT_DIR = Path("vault")
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

def get_file_mime_type(file_bytes: bytes) -> str:
    """Uses pure-python filetype to return the MIME type of a byte string."""
    kind = filetype.guess(file_bytes)
    if kind:
        return kind.mime
    return "application/octet-stream"


async def calculate_file_hash(file: UploadFile) -> str:
    """Calculates SHA-256 hash by reading the file in 1MB chunks."""
    sha256_hash = hashlib.sha256()
    
    # Ensure we are at the beginning
    await file.seek(0)
    
    # Read the file in 1MB chunks
    while chunk := await file.read(1024 * 1024):
        sha256_hash.update(chunk)
        
    # Reset cursor for future operations
    await file.seek(0)
    
    return sha256_hash.hexdigest()

async def save_file_to_disk(upload_file: UploadFile, file_hash: str):
    """
    Saves the file to the local disk in the 'vault/' directory using its hash as the name.
    Performs content de-duplication: skips write if the hash already exists.
    """
    file_path = VAULT_DIR / file_hash
    
    if file_path.exists():
        # De-duplication: file already exists
        return
        
    # Ensure cursor is at the beginning
    await upload_file.seek(0)
    
    # Use shutil.copyfileobj to stream the file to disk in chunks
    def _write_file():
        with open(file_path, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
            
    try:
        # Run synchronous file writing in a thread pool to avoid blocking the event loop
        await asyncio.to_thread(_write_file)
    except Exception as e:
        print(f"Error writing to disk: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file to local storage.")
