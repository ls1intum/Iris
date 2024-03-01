from typing import Dict

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProgrammingLanguage(str, Enum):
    JAVA = "JAVA"
    PYTHON = "PYTHON"
    C = "C"
    HASKELL = "HASKELL"
    KOTLIN = "KOTLIN"
    VHDL = "VHDL"
    ASSEMBLER = "ASSEMBLER"
    SWIFT = "SWIFT"
    OCAML = "OCAML"
    EMPTY = "EMPTY"


class ProgrammingExerciseDTO(BaseModel):
    id: int
    name: str
    programming_language: ProgrammingLanguage = Field(alias="programmingLanguage")
    template_repository: Dict[str, str] = Field(alias="templateRepository")
    solution_repository: Dict[str, str] = Field(alias="solutionRepository")
    test_repository: Dict[str, str] = Field(alias="testRepository")
    problem_statement: str = Field(alias="problemStatement")
    start_date: datetime | None = Field(alias="startDate")
    end_date: datetime | None = Field(alias="endDate")
