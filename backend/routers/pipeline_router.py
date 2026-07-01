from uuid import UUID

from fastapi import APIRouter, Depends

from auth.clerk import get_authenticated_client
from celery_app import celery_app
from schemas import PipelineJobResponse, TaskStatusResponse
from tasks.pipeline_tasks import run_pipeline_for_client

router = APIRouter(tags=["pipeline"])


@router.post("/pipeline/run", response_model=PipelineJobResponse)
def run_pipeline(client_id: UUID = Depends(get_authenticated_client)):
    task = run_pipeline_for_client.delay(str(client_id))
    return PipelineJobResponse(job_id=task.id, status="queued")


@router.get("/pipeline/status/{job_id}", response_model=TaskStatusResponse)
def pipeline_status(
    job_id: str,
    _: UUID = Depends(get_authenticated_client),  # require valid token
):
    result = celery_app.AsyncResult(job_id)
    return TaskStatusResponse(
        job_id=job_id,
        status=result.state,
        result=result.result if result.state == "SUCCESS" else None,
    )
