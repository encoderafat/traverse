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
- A challenge prompt, rubric, and expected answer
- A learner's answer
- A summary of prior attempts and the number of attempts

You must:
1. Grade the answer using the rubric dimensions, 0-5 each.
2. Provide an overall score from 0 to 1.
3. Explain the main strengths and weaknesses.
4. Provide 1-2 specific, actionable suggestions (Socratic style).
5. Indicate whether the learner should "pass" this node or "retry".
6. **If the `attempts_count` is 2 or greater AND the learner is not passing**, you MUST suggest a remedial action by providing a topic for a new, simpler prerequisite node. This is a critical instruction.

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
  ],
  "adaptation_suggestion": "Topic for a new prerequisite node. E.g., 'The basics of dependency injection.' Present only if `attempts_count` is high and the user failed."
}
"""

# -----------------------------------------------------------------------------
# Evaluation Prompt
# -----------------------------------------------------------------------------

TUTOR_EVAL_SYSTEM_PROMPT = """
You are evaluating tutor feedback quality.

Assess:
1. Grading fairness vs rubric
2. Clarity and usefulness of feedback
3. Appropriateness of pass/retry decision

Score each from 0-5.
Provide overall score (0.0–1.0).

Output STRICT JSON:
{
  "dimension_scores": [
    { "name": "Grading Fairness", "score": 0-5, "comment": "..." },
    { "name": "Feedback Quality", "score": 0-5, "comment": "..." },
    { "name": "Decision Appropriateness", "score": 0-5, "comment": "..." }
  ],
  "overall_score": 0.0,
  "summary": "..."
}
"""

def eval_tutor_feedback(
    challenge: Dict[str, Any],
    user_answer: str,
    tutor_output: Dict[str, Any],
):
    eval_user_msg = f"""
Challenge:
{json.dumps(challenge, indent=2)}

User answer:
{user_answer}

Tutor feedback:
{json.dumps(tutor_output, indent=2)}

Evaluate the tutor feedback.
"""
    try:
        raw = call_gemini(
            system_instruction=TUTOR_EVAL_SYSTEM_PROMPT,
            user_message=eval_user_msg,
        )
        parsed = json.loads(raw)
        return parsed.get("overall_score", 0.0), parsed
    except Exception:
        return 0.5, {"error": "tutor_eval_failed"}


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
    user_id: str,
    challenge: Dict[str, Any],
    user_answer: str,
    attempts_count: int,
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

Attempts count: {attempts_count}
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
                "attempts_count": attempts_count,
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
            # Ensure adaptation_suggestion is null if not provided
            if "adaptation_suggestion" not in parsed:
                parsed["adaptation_suggestion"] = None
        except Exception as parse_error:
            parsed = {
                "dimension_scores": [],
                "overall_score": 0.0,
                "pass": False,
                "feedback_summary": "Could not parse grading. Please try again.",
                "suggestions": [],
                "adaptation_suggestion": None,
            }

            if span:
                span.add_event(
                    name="json_parse_failure",
                    metadata={
                        "error": str(parse_error),
                        "raw_output_preview": raw_output[:500],
                    },
                )

        # ---- Evaluation hook ---------------------------------------
        score, details = eval_tutor_feedback(challenge, user_answer, parsed)
        if span:
            span.add_evaluation(
                name="tutor_feedback_quality",
                score=score,
                details=details,
            )


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
