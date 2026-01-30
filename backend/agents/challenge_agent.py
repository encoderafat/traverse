# agents/challenge_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer

# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

CHALLENGE_SYSTEM_PROMPT = """
You are an expert instructional designer who creates realistic, scenario-based challenges.

Given a learning node (a competency) and, most importantly, external research content (articles, blog posts, etc.), create ONE "proof of competency" challenge.

The challenge MUST:
- Be directly inspired by or based on the provided research content.
- Reflect a real-world task in this domain.
- Be solvable via a text answer (explanation, plan, critique, or small design).
- Include an expected answer outline and a rubric with generic dimensions.

If no research content is provided, do your best to create a realistic challenge based on the node's description alone.

Output STRICT JSON:
{
  "challenge_type": "artefact_creation | critique | scenario_decision | comprehension_test",
  "prompt": "Full instruction to learner.",
  "expected_answer_outline": [
    "Point 1...",
    "Point 2..."
  ],
  "rubric": {
    "dimensions": [
      { "name": "Relevance", "description": "..." },
      { "name": "Correctness", "description": "..." },
      { "name": "Clarity", "description": "..." }
    ],
    "scoring_scale": "0-5"
  },
  "difficulty": "easy | medium | hard"
}
"""

# -----------------------------------------------------------------------------
# Opik Tracer
# -----------------------------------------------------------------------------

opik_tracer = create_opik_tracer(
    name="challenge-agent",
    project_name="learning-paths",
    tags=["challenge", "assessment"],
    metadata={"component": "challenge_agent"},
)

# -----------------------------------------------------------------------------
# Agent Execution
# -----------------------------------------------------------------------------

def run_challenge_agent(
    user_id: str,
    path_id: int,
    node: Dict[str, Any],
    domain_hint: Optional[str],
    research_context: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Generates a single challenge for a learning node.
    Fully instrumented with core Opik tracing.
    """

    user_msg = f"""
Domain hint: {domain_hint or "N/A"}

Node to build challenge for:
{json.dumps(node, indent=2)}

---
Research Content to base the challenge on:
"""
    if research_context:
        for item in research_context:
            # Truncate content to avoid excessive prompt length.
            # This is a simple strategy; more advanced would be summarization or embedding-based search.
            content_preview = (item.get('content', '') or '')[:3000]
            user_msg += f"\nURL: {item.get('url', 'N/A')}\nContent Preview:\n{content_preview}\n---"
    else:
        user_msg += "\nNo external research content provided."


    user_msg += """
---
Create ONE challenge as described in the system prompt, based primarily on the provided research content.
"""

    span = None
    if opik_tracer:
        span = opik_tracer.start_span(
            name="generate_challenge",
            metadata={
                "user_id": user_id,
                "path_id": path_id,
                "node_id": node.get("id"),
                "node_title": node.get("title"),
                "domain_hint": domain_hint,
                "has_research_context": bool(research_context),
            },
        )

    try:
        raw_output = call_gemini(
            system_instruction=CHALLENGE_SYSTEM_PROMPT,
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
                "error": "invalid_json_from_model",
                "challenge_type": None,
                "prompt": "",
                "expected_answer_outline": [],
                "rubric": {},
                "difficulty": None,
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
        # score, details = eval_challenge_realism(node, parsed)
        # if span:
        #     span.add_evaluation(
        #         name="challenge_realism",
        #         score=score,
        #         details=details,
        #     )

        return parsed

    except Exception as exc:
        if span:
            span.add_event(
                name="challenge_agent_exception",
                metadata={"error": str(exc)},
            )
        raise

    finally:
        if span:
            span.end()
