# agents/tutor_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer

# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

TUTOR_SYSTEM_PROMPT = """
You are a supportive, rigorous tutor for any skill/domain.

Given:
- A challenge prompt
- An expected answer outline
- A rubric
- A learner's answer
- (Optionally) prior attempts summary

You must:
1. Grade the answer using the rubric dimensions, 0-5 each.
2. Provide an overall score from 0 to 1.
3. Explain the main strengths and weaknesses.
4. Provide 1-2 specific, actionable suggestions (Socratic style).
5. Indicate whether the learner should "pass" this node or "retry".

Output STRICT JSON:
{
  "dimension_scores": [
    { "name": "Relevance", "score": 0-5, "comment": "..." }
  ],
  "overall_score": 0.0,
  "pass": true,
  "feedback_summary": "...",
  "suggestions": [
    "Suggestion 1...",
    "Suggestion 2..."
  ]
}
"""

# -----------------------------------------------------------------------------
# Opik Tracer
# -----------------------------------------------------------------------------

opik_tracer = create_opik_tracer(
    name="tutor-agent",
    project_name="learning-paths",
    tags=["tutoring", "evaluation"],
    metadata={"component": "tutor_agent"},
)

# -----------------------------------------------------------------------------
# Agent Execution
# -----------------------------------------------------------------------------

def run_tutor_agent(
    user_id: int,
    challenge: Dict[str, Any],
    user_answer: str,
    prior_attempts_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Grades a learner's answer and provides feedback.
    Fully instrumented with core Opik tracing.
    """

    user_msg = f"""
Challenge prompt:
{challenge.get("prompt")}

Expected answer outline:
{challenge.get("expected_answer_outline", [])}

Rubric:
{challenge.get("rubric", {})}

User answer:
{user_answer}

Prior attempts summary (optional):
{prior_attempts_summary or "N/A"}
"""

    span = None
    if opik_tracer:
        span = opik_tracer.start_span(
            name="tutor_feedback",
            metadata={
                "user_id": user_id,
                "challenge_id": challenge.get("id"),
                "challenge_type": challenge.get("challenge_type"),
            },
        )

    try:
        raw_output = call_gemini(
            system_instruction=TUTOR_SYSTEM_PROMPT,
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
                "dimension_scores": [],
                "overall_score": 0.0,
                "pass": False,
                "feedback_summary": "Could not parse grading. Please try again.",
                "suggestions": [],
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
        # score, details = eval_feedback_helpfulness(challenge, user_answer, parsed)
        # if span:
        #     span.add_evaluation(
        #         name="feedback_helpfulness",
        #         score=score,
        #         details=details,
        #     )

        return parsed

    except Exception as exc:
        if span:
            span.add_event(
                name="tutor_agent_exception",
                metadata={"error": str(exc)},
            )
        raise

    finally:
        if span:
            span.end()
