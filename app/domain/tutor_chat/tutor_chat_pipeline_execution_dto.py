from typing import List

from pydantic import Field

from ...domain import PipelineExecutionDTO
from ...domain.data.course_dto import CourseDTO
from ...domain.data.message_dto import MessageDTO
from ...domain.data.programming_exercise_dto import ProgrammingExerciseDTO
from ...domain.data.user_dto import UserDTO
from ...domain.data.submission_dto import SubmissionDTO


class TutorChatPipelineExecutionDTO(PipelineExecutionDTO):
    submission: SubmissionDTO | None = None
    exercise: ProgrammingExerciseDTO
    course: CourseDTO
    chat_history: List[MessageDTO] = Field(alias="chatHistory", default=[])
    user: UserDTO | None = None
