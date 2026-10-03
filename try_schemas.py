from job_analyzer.schema import JobPosting
from job_analyzer.schema import MatchResult

firstObject = JobPosting(
    title="Software Engineer",
    language="en",
    level="mid",
    required_skills=["Python", "Django", "REST"],
    bonus_skills=["Docker", "Kubernetes"],
    required_language=["en"]
)

secondObject = MatchResult(
    score=0.85,
    found_skills=["Python", "Django"],
    missing_skills=["REST"],
    summary="The candidate has a strong background in Python and Django, but lacks experience with REST."
)