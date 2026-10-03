from typing import Literal
from pydantic import BaseModel, Field

class JobPosting (BaseModel):
    title: str
    language: Literal ["en","fr"]
    level: Literal ["entry","mid","senior","unknown"]
    required_skills: list[str] = []
    bonus_skills: list[str] = []
    required_language: list[Literal ["en","fr"]] = []
    years_required: int | None = None

class MatchResult (BaseModel):
    score: float = Field(..., ge=0, le=1)
    found_skills: list[str] = []
    missing_skills: list[str] = []
    relevant_years: int | None = None
    summary: str 

class LLMMatch (BaseModel):
    found_skills: list[str] = []
    summary: str
    relevant_years: int | None = None


class AnalyzeRequest(BaseModel):
    posting: str = Field(..., min_length=20)
    cv: str = Field(..., min_length=20)


class AnalyzeResponse(BaseModel):
    posting: JobPosting
    match: MatchResult

