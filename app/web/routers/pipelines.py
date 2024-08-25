import logging
import traceback
from threading import Thread

from sentry_sdk import capture_exception

from fastapi import APIRouter, status, Response, Depends

from app.domain import (
    ExerciseChatPipelineExecutionDTO,
    CourseChatPipelineExecutionDTO,
)
from app.web.status.status_update import (
    ExerciseChatStatusCallback,
    CourseChatStatusCallback,
)
from app.pipeline.chat.course_chat_pipeline import CourseChatPipeline
from app.pipeline.chat.exercise_chat_pipeline import ExerciseChatPipeline
from app.dependencies import TokenValidator
from app.domain import FeatureDTO

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


def run_exercise_chat_pipeline_worker(dto: ExerciseChatPipelineExecutionDTO):
    try:
        callback = ExerciseChatStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = ExerciseChatPipeline(callback=callback)
    except Exception as e:
        logger.error(f"Error preparing exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/tutor-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_exercise_chat_pipeline(variant: str, dto: ExerciseChatPipelineExecutionDTO):
    thread = Thread(target=run_exercise_chat_pipeline_worker, args=(dto,))
    thread.start()


def run_course_chat_pipeline_worker(dto, variant):
    try:
        callback = CourseChatStatusCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        pipeline = CourseChatPipeline(callback=callback, variant=variant)
    except Exception as e:
        logger.error(f"Error preparing exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/course-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_course_chat_pipeline(variant: str, dto: CourseChatPipelineExecutionDTO):
    thread = Thread(target=run_course_chat_pipeline_worker, args=(dto, variant))
    thread.start()


@router.get("/{feature}/variants")
def get_pipeline(feature: str):
    """
    Get the pipeline variants for the given feature.
    """
    match feature:
        case "CHAT":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default chat variant.",
                )
            ]
        case "PROGRAMMING_EXERCISE_CHAT":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default programming exercise chat variant.",
                )
            ]
        case "COURSE_CHAT":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default course chat variant.",
                )
            ]
        case "COMPETENCY_GENERATION":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default competency generation variant.",
                )
            ]
        case "LECTURE_INGESTION":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default lecture ingestion variant.",
                )
            ]
        case _:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
