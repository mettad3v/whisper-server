import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from celery_app import celery
from worker import transcribe_audio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Whisper AI Backend",
    description="CPU-based audio transcription service using Whisper AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development. In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Create recordings directory if it doesn't exist
RECORDINGS_DIR = Path("recordings")
RECORDINGS_DIR.mkdir(exist_ok=True)

# Supported MIME types
SUPPORTED_MIME_TYPES = {
    'audio/mpeg',      # mp3
    'audio/wav',       # wav
    'audio/x-wav',     # wav
    'audio/m4a',       # m4a
    'audio/x-m4a',     # m4a (common variant)
    'audio/mp4',       # m4a
    'audio/ogg',       # ogg
    'audio/webm',      # webm
}

class TranscriptionRequest(BaseModel):
    job_id: str
    status: str

class TranscriptionResponse(BaseModel):
    job_id: str
    status: str
    text: Optional[str] = None
    language: Optional[str] = None
    duration: Optional[float] = None
    language_probability: Optional[float] = None
    error: Optional[str] = None

@app.post("/transcribe", response_model=TranscriptionRequest)
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Upload an audio file for transcription.

    Supported formats: mp3, wav, m4a, ogg, webm
    Maximum file size: ~100MB (configurable)
    """
    # Validate file type
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Supported types: {', '.join(SUPPORTED_MIME_TYPES)}"
        )

    # Save uploaded file temporarily with temporary name
    temp_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix.lower() if file.filename else '.tmp'
    temp_filename = f"{temp_id}{file_extension}"
    temp_path = RECORDINGS_DIR / temp_filename

    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Submit job to Celery and get the task ID
        task = transcribe_audio.delay(str(temp_path))
        job_id = task.id  # Use Celery's task ID as the job ID

        logger.info(f"Received transcription request: job_id={job_id}, file={file.filename}, size={temp_path.stat().st_size} bytes")

        return TranscriptionRequest(
            job_id=job_id,
            status="queued"
        )

    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to process upload for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload"
        )

@app.get("/job/{job_id}", response_model=TranscriptionResponse)
async def get_job_status(job_id: str):
    """
    Get the status and result of a transcription job.
    """
    try:
        # Get task result from Celery
        task_result = celery.AsyncResult(job_id)

        if task_result.state == "PENDING":
            # Job hasn't started yet
            return TranscriptionResponse(
                job_id=job_id,
                status="queued"
            )
        elif task_result.state == "PROGRESS":
            # Job is in progress
            return TranscriptionResponse(
                job_id=job_id,
                status="processing"
            )
        elif task_result.state == "SUCCESS":
            # Job completed successfully
            result = task_result.result
            return TranscriptionResponse(
                job_id=job_id,
                status="completed",
                text=result.get("text"),
                language=result.get("language"),
                duration=result.get("duration"),
                language_probability=result.get("language_probability")
            )
        elif task_result.state == "FAILURE":
            # Job failed
            return TranscriptionResponse(
                job_id=job_id,
                status="failed",
                error=str(task_result.info.get('error', 'Unknown error'))
            )
        else:
            # Unknown state
            return TranscriptionResponse(
                job_id=job_id,
                status="unknown",
                error=f"Unknown job state: {task_result.state}"
            )

    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
