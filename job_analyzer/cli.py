from pathlib import Path

import typer

from job_analyzer.analyzer import analyze
from job_analyzer.llm import LLMClient

app = typer.Typer(help="Analyze a job posting (FR/EN) and match it against a CV.")


@app.command()
def main(
    posting_file: Path = typer.Argument(..., exists=True, help="Path to the job posting text file"),
    cv_file: Path = typer.Argument(..., exists=True, help="Path to the CV text file"),
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON instead of a report"),
):
    posting_text = posting_file.read_text(encoding="utf-8")
    cv_text = cv_file.read_text(encoding="utf-8")

    llm = LLMClient()
    posting, match = analyze(llm, posting_text, cv_text)

    if json_output:
        print(posting.model_dump_json(indent=4))
        print(match.model_dump_json(indent=4))
        return

    print(f"\n{posting.title}  ({posting.level}, posting in {posting.language})")
    print(f"Match score: {match.score:.0%}")
    print(f"Experience: {match.relevant_years or '?'} years (required: {posting.years_required or 'not stated'})")
    print(f"\nFound skills:   {', '.join(match.found_skills) or 'none'}")
    print(f"Missing skills: {', '.join(match.missing_skills) or 'none'}")
    print(f"\n{match.summary}\n")


if __name__ == "__main__":
    app()