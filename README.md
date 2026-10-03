# Job Match Analyzer

Analyze a job posting in **French or English** and match it against a CV using an LLM.
Built for the bilingual Quebec job market.

Given a posting and a CV, it extracts the job's requirements (title, level, required and bonus
skills, languages, years of experience) and scores how well the CV matches, with the skills
found, the skills missing, and a short summary.

![API documentation](docs/api-screenshot.png)

## Example

```
$ python -m job_analyzer.cli examples/posting_fr.txt examples/cv_sample.txt

[paste your real CLI output here]
```

## Features

- Structured extraction from French and English postings, with skills normalized to English
- Match score combining skill coverage (70%) and experience (30%)
- Command-line interface with a human-readable report or raw JSON (`--json`)
- REST API built with FastAPI, with interactive docs at `/docs`
- Test suite that runs without calling the LLM

## How it works

1. **Extract:** the LLM turns the raw posting into JSON, validated against a Pydantic model.
2. **Match:** the LLM identifies which required skills the CV demonstrates and estimates relevant years of experience.
3. **Score:** Python computes the final score from those results.

## Design decisions

- **The LLM judges, Python calculates.** LLMs are good at understanding that "built REST
  services with FastAPI" covers "Python", but inconsistent with numbers. The score is computed
  deterministically in code.
- **Validate everything the LLM returns.** Every response is validated with Pydantic. If it's
  invalid, the request is retried once with the validation error included in the prompt.
- **Don't trust the LLM's lists blindly.** Found skills are filtered against the posting's
  required skills (so invented skills can't inflate the score), and missing skills are derived in code.
- **Bilingual by normalization.** Skills are normalized to English during extraction, so a
  French posting ("infonuagique") can be compared with an English CV ("Cloud").
- **LLM isolated behind one class.** All API calls go through `LLMClient`, injected as a
  dependency. Tests replace it with a fake, and switching providers means changing one file.
- **Robust response handling.** The client collects text blocks from the response rather than
  assuming a fixed position, so it handles responses that include reasoning blocks.

## Getting started

Requirements: Python 3.11+ and an Anthropic API key.

```bash
git clone https://github.com/[your-username]/job-match-analyzer.git
cd job-match-analyzer
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API key.

**CLI**
```bash
python -m job_analyzer.cli examples/posting_fr.txt examples/cv_sample.txt
python -m job_analyzer.cli examples/posting_fr.txt examples/cv_sample.txt --json
```

**API**
```bash
uvicorn job_analyzer.api:app --reload
```
Then open http://127.0.0.1:8000/docs

**Tests**
```bash
python -m pytest -v
```

## Project structure

```
job_analyzer/
├── schema.py     # Pydantic models: what we extract and return
├── llm.py        # LLM client (the only file that calls the API)
├── analyzer.py   # Extraction, matching, scoring, retry logic
├── cli.py        # Command-line interface (Typer)
└── api.py        # REST API (FastAPI)
tests/            # Unit and API tests with a fake LLM
examples/         # Sample postings (FR/EN) and a sample CV
```

## Possible improvements

- Weight bonus skills in the score
- Accept PDF CVs
- Evaluate extraction accuracy on a larger set of real postings
- Add a simple web front end