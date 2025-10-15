import os
import logging
from typing import Optional
from pathlib import Path
import tempfile

from celery import Celery
from faster_whisper import WhisperModel
import ffmpeg

from celery import current_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import celery app
from celery_app import celery

# Global model instance (loaded once at startup)
model: Optional[WhisperModel] = None

@celery.task(bind=True)
def transcribe_audio(self, audio_path: str) -> dict:
    """
    Transcribe audio file using faster-whisper.

    Args:
        audio_path: Path to the audio file

    Returns:
        dict: Transcription result or error
    """
    global model

    try:
        # Load model if not already loaded
        if model is None:
            logger.info("Loading Whisper model...")
            model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("Whisper model loaded successfully")

        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription for job {self.request.id}: {audio_path}")

        # Update task state to started
        self.update_state(state='PROGRESS', meta={'message': 'Starting transcription'})

        # Determine if we need to convert the audio
        file_extension = audio_path.suffix.lower()
        needs_conversion = file_extension not in ['.wav', '.flac']

        working_audio_path = audio_path
        temp_converted_file = None

        if needs_conversion:
            # Convert to WAV for better Whisper compatibility
            logger.info(f"Converting audio format for job {self.request.id}")
            self.update_state(state='PROGRESS', meta={'message': 'Converting audio format'})

            temp_converted_file = Path(tempfile.mktemp(suffix='.wav'))
            try:
                convert_audio(str(audio_path), str(temp_converted_file))
                working_audio_path = temp_converted_file
            except Exception as conversion_error:
                logger.warning(f"Audio conversion failed for job {self.request.id}, trying direct transcription: {conversion_error}")
                # Fall back to original file if conversion fails
                working_audio_path = audio_path

        try:
            # Transcribe the audio
            segments, info = model.transcribe(
                str(working_audio_path),
                beam_size=5,
                language=None,  # Auto-detect language
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(threshold=0.5, min_speech_duration_ms=250)
            )
        finally:
            # Clean up converted file if it was created
            if temp_converted_file and temp_converted_file.exists():
                try:
                    temp_converted_file.unlink()
                    logger.info(f"Cleaned up converted audio file: {temp_converted_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up converted file {temp_converted_file}: {e}")

        # Collect all text segments
        transcription_parts = []
        for segment in segments:
            transcription_parts.append(segment.text)

        full_text = "".join(transcription_parts).strip()

        # Log completion
        duration = info.duration
        logger.info(f"Transcription completed for job {self.request.id}. "
                   f"Duration: {duration:.2f}s, Text length: {len(full_text)} chars")

        # Clean up the audio file
        try:
            audio_path.unlink()
            logger.info(f"Cleaned up audio file: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up audio file {audio_path}: {e}")

        return {
            "status": "completed",
            "text": full_text,
            "language": info.language,
            "duration": duration,
            "language_probability": info.language_probability
        }

    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(f"Job {self.request.id} failed: {error_msg}")

        # Clean up the audio file even on failure
        try:
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Cleaned up audio file after failure: {audio_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up audio file after failure {audio_path}: {cleanup_error}")

        # Mark task as failed
        self.update_state(state='FAILURE', meta={'error': error_msg})

        raise Exception(error_msg)


def convert_audio(input_path: str, output_path: str) -> None:
    """
    Convert audio file to WAV format using ffmpeg.

    Args:
        input_path: Input audio file path
        output_path: Output WAV file path
    """
    try:
        ffmpeg.input(input_path).output(
            output_path,
            acodec='pcm_s16le',  # 16-bit PCM
            ac=1,                # Mono
            ar=16000             # 16kHz sample rate (optimal for Whisper)
        ).run(quiet=True, overwrite_output=True)
        logger.info(f"Converted audio: {input_path} -> {output_path}")
    except ffmpeg.Error as e:
        raise Exception(f"Audio conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
