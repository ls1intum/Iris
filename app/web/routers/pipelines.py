import logging
import traceback
from threading import Thread

from sentry_sdk import capture_exception

from fastapi import APIRouter, status, Response, Depends

from app.domain import (
    ExerciseChatPipelineExecutionDTO,
    CourseChatPipelineExecutionDTO,
    CompetencyExtractionPipelineExecutionDTO,
)
from app.domain.chat.lecture_chat.lecture_chat_pipeline_execution_dto import (
    LectureChatPipelineExecutionDTO,
)
from app.pipeline.chat.lecture_chat_pipeline import LectureChatPipeline
from app.web.status.status_update import (
    ExerciseChatStatusCallback,
    CourseChatStatusCallback,
    CompetencyExtractionCallback,
    LectureChatCallback,
)
from app.pipeline.chat.course_chat_pipeline import CourseChatPipeline
from app.pipeline.chat.exercise_chat_pipeline import ExerciseChatPipeline
from app.dependencies import TokenValidator
from app.domain import FeatureDTO
from app.pipeline.competency_extraction_pipeline import CompetencyExtractionPipeline
from app.domain.text_exercise_chat_pipeline_execution_dto import (
    TextExerciseChatPipelineExecutionDTO,
)
from app.pipeline.text_exercise_chat_pipeline import TextExerciseChatPipeline
from app.web.status.status_update import TextExerciseChatCallback

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


def run_text_exercise_chat_pipeline_worker(dto, variant):
    try:
        callback = TextExerciseChatCallback(
            run_id=dto.execution.settings.authentication_token,
            base_url=dto.execution.settings.artemis_base_url,
            initial_stages=dto.execution.initial_stages,
        )
        match variant:
            case "default" | "text_exercise_chat_pipeline_reference_impl":
                pipeline = TextExerciseChatPipeline(callback=callback)
            case _:
                raise ValueError(f"Unknown variant: {variant}")
    except Exception as e:
        logger.error(f"Error preparing text exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running text exercise chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


def run_lecture_chat_pipeline_worker(variant, dto):
    try:
        callback = LectureChatCallback(
            run_id=dto.settings.authentication_token,
            base_url=dto.settings.artemis_base_url,
            initial_stages=dto.initial_stages,
        )
        match variant:
            case "default" | "lecture_chat_pipeline_reference_impl":
                pipeline = LectureChatPipeline(callback=callback)
            case _:
                raise ValueError(f"Unknown variant: {variant}")
    except Exception as e:
        logger.error(f"Error preparing lecture chat pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running lecture chat pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/text-exercise-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_text_exercise_chat_pipeline(
    variant: str, dto: TextExerciseChatPipelineExecutionDTO
):
    thread = Thread(target=run_text_exercise_chat_pipeline_worker, args=(dto, variant))
    thread.start()


@router.post(
    "/lecture-chat/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_lecture_chat_pipeline(variant: str, dto: LectureChatPipelineExecutionDTO):
    thread = Thread(target=run_lecture_chat_pipeline_worker, args=(variant, dto))
    thread.start()


def run_competency_extraction_pipeline_worker(
    dto: CompetencyExtractionPipelineExecutionDTO, _variant: str
):
    try:
        callback = CompetencyExtractionCallback(
            run_id=dto.execution.settings.authentication_token,
            base_url=dto.execution.settings.artemis_base_url,
            initial_stages=dto.execution.initial_stages,
        )
        pipeline = CompetencyExtractionPipeline(callback=callback)
    except Exception as e:
        logger.error(f"Error preparing competency extraction pipeline: {e}")
        logger.error(traceback.format_exc())
        capture_exception(e)
        return

    try:
        pipeline(dto=dto)
    except Exception as e:
        logger.error(f"Error running competency extraction pipeline: {e}")
        logger.error(traceback.format_exc())
        callback.error("Fatal error.", exception=e)


@router.post(
    "/competency-extraction/{variant}/run",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(TokenValidator())],
)
def run_competency_extraction_pipeline(
    variant: str, dto: CompetencyExtractionPipelineExecutionDTO
):
    thread = Thread(
        target=run_competency_extraction_pipeline_worker, args=(dto, variant)
    )
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
        case "TEXT_EXERCISE_CHAT":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default text exercise chat variant.",
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
        case "LECTURE_CHAT":
            return [
                FeatureDTO(
                    id="default",
                    name="Default Variant",
                    description="Default lecture chat variant.",
                )
            ]
        case _:
            return Response(status_code=status.HTTP_400_BAD_REQUEST)
