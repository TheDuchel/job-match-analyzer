import json

from pydantic import BaseModel, ValidationError

from job_analyzer.llm import LLMClient
from job_analyzer.schema import JobPosting, LLMMatch, MatchResult

EXTRACT_PROMPT = """You extract structured information from job postings written in French or English.

Return ONLY a JSON object, with no text before or after it, using exactly these keys:
- "title": the job title, in the original language of the posting
- "language": the language the posting is written in, "en" or "fr"
- "level": one of "entry", "mid", "senior", "unknown"
- "required_skills": list of required technical skills
- "bonus_skills": list of skills described as a plus / un atout (empty list if none)
- "required_language": spoken languages the job requires, as a list of "en" and/or "fr"
- "years_required": the number of years of experience required, as an integer (0 if none specified)

Write every skill name in English, using its most common form
(for example "infonuagique" -> "Cloud", "bases de données" -> "Databases").

<posting>
{posting}
</posting>"""

MATCH_PROMPT = """You compare a candidate's CV against the required skills of a job.

Required skills:
{required_skills}

Return ONLY a JSON object, with no text before or after it, using exactly these keys:
- "found_skills": the required skills that the CV clearly demonstrates.
  Only use skills from the list above, written exactly as they appear there.
  Count a skill as found if the CV shows it through equivalent wording or closely related experience.
- "summary": 2 sentences in English on how well the candidate fits this job.

<cv>
{cv}
</cv>"""

MAX_ATTEMPTS = 2


def extract_json(text: str) -> dict:
    """Keep only the {...} part of the model's reply."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in the model's reply: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def ask_llm(llm: LLMClient, prompt: str, model_class: type[BaseModel]) -> BaseModel:
    """Call the LLM, validate its JSON against model_class, retry with feedback if invalid."""
    last_error = None

    for _ in range(MAX_ATTEMPTS):
        full_prompt = prompt
        if last_error:
            full_prompt += (
                f"\n\nYour previous answer was invalid: {last_error}\n"
                "Return ONLY valid JSON matching the keys above."
            )

        response = llm.complete(full_prompt, max_tokens=1000)

        try:
            return model_class.model_validate(extract_json(response))
        except (ValueError, ValidationError) as error:
            last_error = str(error)[:300]

    raise RuntimeError(f"LLM returned invalid output after {MAX_ATTEMPTS} attempts: {last_error}")


def extract_posting(llm: LLMClient, posting_text: str) -> JobPosting:
    prompt = EXTRACT_PROMPT.format(posting=posting_text)
    return ask_llm(llm, prompt, JobPosting)


def compute_score(found: list[str], required: list[str]) -> float:
    """Share of required skills found in the CV, between 0 and 1."""
    if not required:
        return 0.0
    return round(len(found) / len(required), 2)

def experience_score(candidate_years: int | None, years_required: int | None) -> float:
    if years_required is None or years_required == 0:
        return 1.0                      # no requirement: no penalty
    if candidate_years is None:
        return 0.5                      # unknown: neutral rather than zero
    return min(1.0, candidate_years / years_required)


def match_cv(llm: LLMClient, posting: JobPosting, cv_text: str) -> MatchResult:
    required_list = "\n".join(f"- {skill}" for skill in posting.required_skills)
    prompt = MATCH_PROMPT.format(required_skills=required_list, cv=cv_text)
    llm_match = ask_llm(llm, prompt, LLMMatch)

    # Keep only found skills that really are in the required list (case-insensitive),
    # then derive the missing ones in Python instead of trusting the LLM.
    found_lower = {skill.lower() for skill in llm_match.found_skills}
    found = [skill for skill in posting.required_skills if skill.lower() in found_lower]
    missing = [skill for skill in posting.required_skills if skill.lower() not in found_lower]
    SKILLS_WEIGHT = 0.7
    EXPERIENCE_WEIGHT = 0.3

    skills_score = compute_score(found, posting.required_skills)
    exp_score = experience_score(llm_match.relevant_years, posting.years_required)
    score = SKILLS_WEIGHT * skills_score + EXPERIENCE_WEIGHT * exp_score

    return MatchResult(
        score=score,
        found_skills=found,
        missing_skills=missing,
        summary=llm_match.summary,
    )


def analyze(llm: LLMClient, posting_text: str, cv_text: str) -> tuple[JobPosting, MatchResult]:
    posting = extract_posting(llm, posting_text)
    match = match_cv(llm, posting, cv_text)
    return posting, match


if __name__ == "__main__":
    llm = LLMClient()

    with open("examples/posting_fr.txt", encoding="utf-8") as f:
        posting_text = f.read()
    with open("examples/cv_sample.txt", encoding="utf-8") as f:
        cv_text = f.read()

    posting, match = analyze(llm, posting_text, cv_text)
    print(posting.model_dump_json(indent=4))
    print(match.model_dump_json(indent=4))