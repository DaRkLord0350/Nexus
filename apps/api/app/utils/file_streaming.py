import asyncio
import hashlib
import tempfile

from fastapi import HTTPException, UploadFile, status

STREAM_CHUNK_SIZE = 1024 * 1024  # 1MB
SPOOL_MAX_SIZE = 5 * 1024 * 1024  # spill to disk beyond 5MB


async def stream_to_temp_with_checksum(uploaded_file: UploadFile, max_bytes: int) -> tuple[str, int, tempfile.SpooledTemporaryFile]:
    """Streams an UploadFile into a spooled temp file while computing its SHA-256 checksum.

    Shared by FileService and MediaService so upload streaming/size-limit
    enforcement/checksum logic exists in exactly one place.
    """
    spooled = tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_SIZE)
    hasher = hashlib.sha256()
    total = 0

    try:
        while True:
            chunk = await uploaded_file.read(STREAM_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds maximum upload size.")
            hasher.update(chunk)
            await asyncio.to_thread(spooled.write, chunk)
    except HTTPException:
        spooled.close()
        raise

    spooled.seek(0)
    return hasher.hexdigest(), total, spooled
