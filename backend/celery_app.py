from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "family_office",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.pipeline_tasks", "tasks.scoring_tasks", "tasks.memo_tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "daily-pipeline-6am-utc": {
            "task": "tasks.pipeline_tasks.run_pipeline_for_all_clients",
            "schedule": crontab(hour=6, minute=0),
        }
    },
)
