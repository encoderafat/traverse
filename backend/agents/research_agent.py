# agents/research_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer

# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

RESEARCH_SYSTEM_PROMPT = """
You are an expert curriculum designer and career coach.

Given a user's goal (any domain: career, fitness, creative, etc.), you will:
1. Infer the main competencies and subskills required to achieve that goal.
2. Express them as structured JSON.
3. Avoid domain-specific jargon unless necessary; explain in plain language.

Output strictly valid JSON in this schema:
{
  "normalized_goal": "...",
  "competencies": [
    {
      "id": "c1",
      "name": "Short name of competency",
      "description": "1-3 sentence explanation",
      "type": "technical | conceptual | soft-skill | meta",
      "example_tasks": [
        "Example real-world task #1",
        "Example real-world task #2"
      ]
    }
  ]
}
"""

# -----------------------------------------------------------------------------
# Opik Tracer (module-level singleton)
# -----------------------------------------------------------------------------

opik_tracer = create_opik_tracer(
    name="research-agent",
    project_name="learning-paths",
    tags=["research", "competency-extraction"],
    metadata={
        "component": "research_agent",
    },
)

# -----------------------------------------------------------------------------
# Agent Execution
# -----------------------------------------------------------------------------

def run_research_agent(
    user_id: str,
    goal_title: str,
    goal_description: Optional[str],
    domain_hint: Optional[str],
    level: Optional[str],
) -> Dict[str, Any]:
    """
    Derives competencies for a user goal.
    Fully instrumented with Opik.
    """

    user_msg = f"""
    User goal title: {goal_title}
    Goal description: {goal_description or "N/A"}
    Domain hint: {domain_hint or "N/A"}
    Level: {level or "N/A"}

    Derive competencies as described.
    """

    # ---- Start Opik span -----------------------------------------------------
    span = None
    if opik_tracer:
        span = opik_tracer.start_span(
            name="derive_competencies",
            metadata={
                "user_id": user_id,
                "goal_title": goal_title,
                "domain_hint": domain_hint,
                "level": level,
            },
        )

    try:
        raw_output = call_gemini(
            system_instruction=RESEARCH_SYSTEM_PROMPT,
            user_message=user_msg,
        )

        if span:
            span.add_event(
                name="model_response_received",
                metadata={"raw_output_preview": raw_output[:500]},
            )

        try:
            parsed = json.loads(raw_output)
        except Exception as parse_error:
            parsed = {
                "normalized_goal": goal_title,
                "competencies": [],
                "error": "invalid_json_from_model",
            }

            if span:
                span.add_event(
                    name="json_parse_failure",
                    metadata={
                        "error": str(parse_error),
                        "raw_output_preview": raw_output[:500],
                    },
                )

        # ---- Evaluation hook (future) ---------------------------------------
        # Example:
        #
        # score, explanation = eval_research_quality(goal_title, parsed)
        # if span:
        #     span.add_evaluation(
        #         name="research_quality",
        #         score=score,
        #         details=explanation,
        #     )

        return parsed

    except Exception as exc:
        if span:
            span.add_event(
                name="research_agent_exception",
                metadata={"error": str(exc)},
            )
        raise

    finally:
        if span:
            span.end()
