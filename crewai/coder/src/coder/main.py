#!/usr/bin/env python
import json
import os
import sys

from coder.crew import CVGeneratorCrew


DEFAULT_CHANGES = "No changes requested"
DEFAULT_TEMPLATE_REQUIREMENTS = (
    "Match this exact one-page resume template as closely as possible: "
    "full name in large bold uppercase centered at the top; one centered contact line beneath "
    "with email, phone, LinkedIn, GitHub, and location separated by vertical bars; no role/title "
    "line under the name; section headings in uppercase and left aligned; section order exactly as "
    "PROFILE, TECHNICAL SKILLS, SOFT SKILLS, PROFESSIONAL EXPERIENCE, PERSONAL PROJECTS, EDUCATION; "
    "PROFILE is a dense paragraph, TECHNICAL SKILLS uses grouped label-style lines such as "
    "'Languages & Frameworks:', 'Databases:', 'Core CS Concepts:', and 'Tools & Platforms:'; "
    "SOFT SKILLS appears as a compact single-line bullet-style list; PROFESSIONAL EXPERIENCE shows "
    "job title and company on one line with dates on the next line; PERSONAL PROJECTS lists project "
    "name plus stack on the heading line followed by compact bullet points; EDUCATION is at the end "
    "with degree first, university on the next line, and dates aligned simply on the following line "
    "or same block; keep the resume compact, professional, single-column, and close to one page; "
    "do not add sidebars, icons, colored blocks, decorative graphics, extra sections, or a new layout."
)

def build_inputs(
    cv_path: str | None = None,
    changes: str | None = None,
    template_requirements: str | None = None,
) -> dict:
    cv_value = (cv_path or os.getenv("CODER_CV_PATH", "knowledge/NasirShahzad_CV_Updated.pdf")).strip()
    if not cv_value:
        raise Exception(
            "Missing CV path. Set CODER_CV_PATH in .env or pass the path as the first argument."
        )

    changes_value = (changes or os.getenv("CODER_CHANGES", DEFAULT_CHANGES)).strip()
    if not changes_value:
        changes_value = DEFAULT_CHANGES

    template_value = (
        template_requirements
        or os.getenv("CODER_TEMPLATE_REQUIREMENTS", DEFAULT_TEMPLATE_REQUIREMENTS)
    ).strip()
    if not template_value:
        template_value = DEFAULT_TEMPLATE_REQUIREMENTS

    return {
        "cv_path": cv_value,
        "changes": changes_value,
        "template_requirements": template_value,
    }


def run() -> None:
    """Run the CV generator crew via `crewai run`."""
    try:
        CVGeneratorCrew().crew().kickoff(inputs=build_inputs())
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train() -> None:
    """Train the crew for a given number of iterations."""
    if len(sys.argv) < 3:
        raise Exception("Usage: train <n_iterations> <filename> [cv_path] [changes]")

    cv_path = sys.argv[3] if len(sys.argv) > 3 else None
    changes = sys.argv[4] if len(sys.argv) > 4 else None
    template_requirements = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        CVGeneratorCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=build_inputs(
                cv_path=cv_path,
                changes=changes,
                template_requirements=template_requirements,
            ),
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay() -> None:
    """Replay the crew execution from a specific task."""
    try:
        CVGeneratorCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test() -> None:
    """Test the crew execution and return the results."""
    if len(sys.argv) < 3:
        raise Exception("Usage: test <n_iterations> <eval_llm> [cv_path] [changes]")

    cv_path = sys.argv[3] if len(sys.argv) > 3 else None
    changes = sys.argv[4] if len(sys.argv) > 4 else None
    template_requirements = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        CVGeneratorCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=build_inputs(
                cv_path=cv_path,
                changes=changes,
                template_requirements=template_requirements,
            ),
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger() -> None:
    """Run the crew with a trigger payload."""
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    try:
        result = CVGeneratorCrew().crew().kickoff(
            inputs=build_inputs(
                cv_path=trigger_payload.get("cv_path"),
                changes=trigger_payload.get("changes"),
                template_requirements=trigger_payload.get("template_requirements"),
            )
        )
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


if __name__ == "__main__":
    run()
