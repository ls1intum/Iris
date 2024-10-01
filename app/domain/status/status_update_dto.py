from typing import List

from pydantic import BaseModel

from ..data.token_usage_dto import TokenUsageDTO
from ...domain.status.stage_dto import StageDTO


class StatusUpdateDTO(BaseModel):
    stages: List[StageDTO]
    tokens: List[TokenUsageDTO] = []
