from celery import Celery
from config import REDIS_URL

redis_url = REDIS_URL

celery = Celery(
    "whisper_backend",
    broker=redis_url,
    backend=redis_url
)

# Import tasks to register them
from worker import transcribe_audio  # noqa: F401

# Configuration
celery.conf.update(
    # Track task state
    task_track_started=True,
    # Keep results for 24 hours (86400 seconds)
    result_expires=86400,
    # Disable rate limits
    worker_disable_rate_limits=True,
    # Task routes
    task_routes={
        "worker.transcribe_audio": {"queue": "whisper"},
    },
    # Worker settings
    worker_prefetch_multiplier=1,  # Fair queuing
    task_acks_late=True,  # Acknowledge after task completion
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)
