# Whisper AI Backend

A CPU-based asynchronous audio transcription service using Whisper AI, FastAPI, Celery, and Redis.

## Features

- **Asynchronous Processing**: Queue-based job system prevents API blocking
- **Multi-format Support**: mp3, wav, m4a, ogg, webm with automatic ffmpeg conversion
- **CPU Optimized**: Uses faster-whisper with int8 quantization for CPU-only inference
- **Error Handling**: Failed jobs remain queryable with error details
- **Auto Cleanup**: Temporary files deleted after processing
- **Job Expiration**: Results stored for 24 hours

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server
- ffmpeg (for audio conversion)

### Installation

1. **Clone and setup:**

   ```bash
   git clone <your-repo>
   cd whisper-server
   pip install -r requirements.txt
   ```

2. **Install Redis:**

   ```bash
   # Ubuntu/Debian
   sudo apt install redis-server -y
   sudo systemctl start redis-server

   # macOS
   brew install redis
   brew services start redis
   ```

3. **Install ffmpeg:**

   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg -y

   # macOS
   brew install ffmpeg
   ```

### Running the Service

1. **Start Redis** (if not already running):

   ```bash
   redis-server
   ```

2. **Start the API server:**

   ```bash
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. **Start the Celery worker:**
   ```bash
   celery -A worker.celery worker --loglevel=info --concurrency=4
   ```

The service will be available at `http://localhost:8000`

## API Usage

### Transcribe Audio

Upload an audio file for transcription:

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3"
```

**Response:**

```json
{
  "job_id": "b9b6cda1-43e8-4fdd-9ea1-ef0f1a9c54ac",
  "status": "queued"
}
```

### Check Job Status

Poll for transcription results:

```bash
curl http://localhost:8000/job/b9b6cda1-43e8-4fdd-9ea1-ef0f1a9c54ac
```

**Processing:**

```json
{
  "job_id": "b9b6cda1-43e8-4fdd-9ea1-ef0f1a9c54ac",
  "status": "processing"
}
```

**Completed:**

```json
{
  "job_id": "b9b6cda1-43e8-4fdd-9ea1-ef0f1a9c54ac",
  "status": "completed",
  "text": "Hello world, this is a transcription.",
  "language": "en",
  "duration": 45.2,
  "language_probability": 0.98
}
```

**Failed:**

```json
{
  "job_id": "b9b6cda1-43e8-4fdd-9ea1-ef0f1a9c54ac",
  "status": "failed",
  "error": "Transcription failed: Audio file corrupted"
}
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Worker configuration
CELERY_CONCURRENCY=4

# API configuration
HOST=0.0.0.0
PORT=8000
```

### Performance Tuning

- **Model Size**: Change from "base" to "small" in `worker.py` for faster processing (less accurate)
- **Concurrency**: Adjust `--concurrency=4` based on your CPU cores
- **Job Expiration**: Modify `result_expires` in `celery_app.py` (default: 24 hours)

## Production Deployment

### Using Supervisor

1. Install Supervisor:

   ```bash
   sudo apt install supervisor -y
   ```

2. Create supervisor config `/etc/supervisor/conf.d/whisper.conf`:

   ```ini
   [program:whisper_api]
   command=uvicorn main:app --host 0.0.0.0 --port 8000
   directory=/path/to/whisper-server
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/whisper_api.err.log
   stdout_logfile=/var/log/whisper_api.out.log

   [program:whisper_worker]
   command=celery -A worker.celery worker --loglevel=info --concurrency=4
   directory=/path/to/whisper-server
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/whisper_worker.err.log
   stdout_logfile=/var/log/whisper_worker.out.log
   ```

3. Reload supervisor:
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start all
   ```

### Docker Deployment

Example Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["./start.sh"]
```

## Troubleshooting

### Common Issues

1. **Redis connection failed**: Ensure Redis is running on `localhost:6379`
2. **Model loading failed**: Check available RAM (base model needs ~1GB)
3. **Audio conversion failed**: Ensure ffmpeg is installed and accessible
4. **Worker not processing jobs**: Check Celery logs for errors

### Logs

- API logs: Check console output when running `python main.py`
- Worker logs: Check Celery worker console output
- Supervisor logs: `/var/log/whisper_*.log`

### Health Check

```bash
curl http://localhost:8000/health
```

## API Reference

### Endpoints

- `POST /transcribe` - Upload audio file
- `GET /job/{job_id}` - Get job status/result
- `GET /health` - Health check

### Supported Audio Formats

- MP3 (`audio/mpeg`)
- WAV (`audio/wav`, `audio/x-wav`)
- M4A (`audio/m4a`, `audio/mp4`)
- OGG (`audio/ogg`)
- WebM (`audio/webm`)

Unsupported formats return HTTP 415 with supported types list.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License
