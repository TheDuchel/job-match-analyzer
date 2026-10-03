import json

import pytest

from job_analyzer.analyzer import (
    compute_score,
    experience_score,
    extract_json,
    extract_posting,
    match_cv,
)
from job_analyzer.schema import JobPosting


class FakeLLM:
    """Returns pre-written replies in order and records the prompts it received."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.prompts = []

    def complete(self, prompt: str, max_tokens: int = 1000) -> str:
        self.prompts.append(prompt)
        return self.replies.pop(0)


VALID_POSTING = {
    "title": "Développeur Python",
    "language": "fr",
    "level": "mid",
    "required_skills": ["Python", "SQL", "Docker"],
    "bonus_skills": ["Azure"],
    "required_language": ["fr", "en"],
    "years_required": 3,
}


# --- extract_json -----------------------------------------------------------

def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_code_fences_and_text():
    text = 'Here is the result:\n```json\n{"a": 1}\n```\nHope it helps!'
    assert extract_json(text) == {"a": 1}


def test_extract_json_without_json_raises():
    with pytest.raises(ValueError):
        extract_json("Sorry, I can't do that.")


# --- extract_posting ----------------------------------------------------------

def test_extract_posting_valid():
    llm = FakeLLM([json.dumps(VALID_POSTING)])
    posting = extract_posting(llm, "some posting text")
    assert posting.title == "Développeur Python"
    assert posting.required_skills == ["Python", "SQL", "Docker"]


def test_extract_posting_retries_after_invalid_output():
    bad = json.dumps({**VALID_POSTING, "level": "expert"})  # not an allowed value
    llm = FakeLLM([bad, json.dumps(VALID_POSTING)])

    posting = extract_posting(llm, "some posting text")

    assert posting.level == "mid"
    assert len(llm.prompts) == 2
    assert "previous answer was invalid" in llm.prompts[1]


def test_extract_posting_gives_up_after_max_attempts():
    llm = FakeLLM(["not json", "still not json"])
    with pytest.raises(RuntimeError):
        extract_posting(llm, "some posting text")


# --- scoring -----------------------------------------------------------------

def test_compute_score():
    assert compute_score(["Python"], ["Python", "SQL"]) == 0.5


def test_compute_score_no_required_skills():
    assert compute_score([], []) == 0.0


@pytest.mark.parametrize(
    "candidate, required, expected",
    [
        (5, 3, 1.0),      # more than required: capped at 1
        (2, 4, 0.5),      # half of what's required
        (None, 3, 0.5),   # unknown: neutral
        (2, None, 1.0),   # no requirement: no penalty
    ],
)
def test_experience_score(candidate, required, expected):
    assert experience_score(candidate, required) == expected


# --- match_cv ----------------------------------------------------------------

def test_match_cv_computes_missing_and_ignores_invented_skills():
    posting = JobPosting(**VALID_POSTING)
    llm_reply = json.dumps({
        "found_skills": ["python", "SQL", "Kubernetes"],  # lowercase + one invented skill
        "summary": "Good fit.",
        "relevant_years": 3,
    })
    llm = FakeLLM([llm_reply])

    result = match_cv(llm, posting, "some cv text")

    assert result.found_skills == ["Python", "SQL"]
    assert result.missing_skills == ["Docker"]
    assert result.score == pytest.approx(0.77, abs=0.01)