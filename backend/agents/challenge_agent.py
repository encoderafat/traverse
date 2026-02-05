# agents/challenge_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer
from services.ab_testing import select_variant

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

# Bump this when the prompt changes meaningfully.
PROMPT_VERSION = "challenge_v1"
EXPERIMENT_NAME = "challenge_prompt"
EXPERIMENT_VARIANTS = ["A", "B"]
# -----------------------------------------------------------------------------
# Evaluation Prompt
# -----------------------------------------------------------------------------

CHALLENGE_EVAL_SYSTEM_PROMPT = """
You are evaluating a competency challenge.

Assess:
1. Alignment with the learning node
2. Real-world realism
3. Appropriateness of difficulty

Score each from 0-5.
Provide an overall score (0.0–1.0).

Output STRICT JSON:
{
  "dimension_scores": [
    { "name": "Alignment", "score": 0-5, "comment": "..." },
    { "name": "Realism", "score": 0-5, "comment": "..." },
    { "name": "Difficulty", "score": 0-5, "comment": "..." }
  ],
  "overall_score": 0.0,
  "summary": "..."
}
"""

def eval_challenge_quality(node: Dict[str, Any], challenge_json: Dict[str, Any]):
    eval_user_msg = f"""
Learning node:
{json.dumps(node, indent=2)}

Generated challenge:
{json.dumps(challenge_json, indent=2)}

Evaluate this challenge.
"""
    try:
        raw = call_gemini(
            system_instruction=CHALLENGE_EVAL_SYSTEM_PROMPT,
            user_message=eval_user_msg,
        )
        parsed = json.loads(raw)
        return parsed.get("overall_score", 0.0), parsed
    except Exception:
        return 0.5, {"error": "challenge_eval_failed"}


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
    from opik import start_as_current_trace, start_as_current_span

    variant = select_variant(user_id, EXPERIMENT_NAME, EXPERIMENT_VARIANTS)
    prompt_by_variant = {
        "A": CHALLENGE_SYSTEM_PROMPT,
        "B": CHALLENGE_SYSTEM_PROMPT,
    }
    system_prompt = prompt_by_variant[variant]

    with start_as_current_trace(
        name="generate_challenge",
        tags=["challenge", "assessment", PROMPT_VERSION, f"{EXPERIMENT_NAME}:{variant}"],
        metadata={
            "user_id": user_id,
            "path_id": path_id,
            "node_id": node.get("id"),
            "node_title": node.get("title"),
            "domain_hint": domain_hint,
            "has_research_context": bool(research_context),
            "prompt_version": PROMPT_VERSION,
            "experiment": EXPERIMENT_NAME,
            "variant": variant,
        },
        project_name="learning-paths"
    ) as trace:
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
            user_msg += "\nNo external research content found."


        user_msg += """
---
Create ONE challenge as described in the system prompt, based on the provided research content.
"""

        with start_as_current_span(
            name="call_gemini",
            type="llm",
            metadata={"model": "gemini"}
        ) as span:
            raw_output = call_gemini(
                system_instruction=system_prompt,
                user_message=user_msg,
            )
            span.input = {"user_msg": user_msg[:500]}  # Limit input size
            span.output = {"raw_output": raw_output[:500]}  # Limit output size

        try:
            parsed = json.loads(raw_output)
        except Exception:
            parsed = {
                "error": "invalid_json_from_model",
                "challenge_type": None,
                "prompt": "",
                "expected_answer_outline": [],
                "rubric": {},
                "difficulty": None,
            }

        # ---- Evaluation hook ---------------------------------------
        score, details = eval_challenge_quality(node, parsed)

        trace.input = {"node_title": node.get("title"), "domain_hint": domain_hint}
        trace.output = {
            "challenge_type": parsed.get("challenge_type"),
            "prompt_length": len(parsed.get("prompt", "")),
            "llm_invalid_json": parsed.get("error") == "invalid_json_from_model",
            "eval_overall_score": score,
            "eval_dimension_scores": details.get("dimension_scores"),
            "eval_failed": "error" in details,
        }


        return parsed
