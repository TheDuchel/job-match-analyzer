from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from job_analyzer.analyzer import analyze
from job_analyzer.llm import LLMClient
from job_analyzer.schema import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="Job Match Analyzer",
    description="Analyze a job posting (FR/EN) and match it against a CV.",
    version="0.1.0",
)


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(request: AnalyzeRequest, llm: LLMClient = Depends(get_llm)):
    try:
        posting, match = analyze(llm, request.posting, request.cv)
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))
    return AnalyzeResponse(posting=posting, match=match)