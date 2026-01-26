# agents/dag_builder_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer

# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

DAG_BUILDER_SYSTEM_PROMPT = """
You are an expert at structuring learning sequences into a directed acyclic graph (DAG).

Input: a list of competencies for a given goal + user background.

Task:
1. Group and order these competencies into 15-40 "nodes".
2. Each node should be a meaningful unit of learning (concept, skill, or project).
3. Define prerequisite relationships between nodes (DAG, no cycles).
4. Estimate time per node in minutes for a motivated learner.
5. Tag node type: 'concept', 'skill', 'project', or 'meta'.

Output STRICT JSON:
{
  "summary": "Short 2-3 sentence summary of the path",
  "nodes": [
    {
      "id": "n1",
      "title": "...",
      "description": "...",
      "node_type": "concept | skill | project | meta",
      "estimated_minutes": 30,
      "tags": ["tag1", "tag2"]
    }
  ],
  "edges": [
    { "from": "n1", "to": "n2" }
  ]
}

Rules:
- No edge cycles.
- 'from' must be a prerequisite of 'to'.
- Keep beginners in mind; build up complexity gradually.
"""

# -----------------------------------------------------------------------------
# Opik Tracer (module-level singleton)
# -----------------------------------------------------------------------------

opik_tracer = create_opik_tracer(
    name="dag-builder-agent",
    project_name="learning-paths",
    tags=["dag", "curriculum-structuring"],
    metadata={
        "component": "dag_builder_agent",
    },
)

# -----------------------------------------------------------------------------
# Agent Execution
# -----------------------------------------------------------------------------

def run_dag_builder_agent(
    user_id: str,
    goal_title: str,
    competencies: Dict[str, Any],
    user_background: Optional[str],
) -> Dict[str, Any]:
    """
    Builds a learning DAG from extracted competencies.
    Fully instrumented with core Opik tracing.
    """

    user_msg = f"""
    User goal: {goal_title}
    User background (free text): {user_background or "N/A"}

    Competencies JSON:
    {json.dumps(competencies, indent=2)}
    """

    # ---- Start Opik span -----------------------------------------------------
    span = None
    if opik_tracer:
        span = opik_tracer.start_span(
            name="build_learning_dag",
            metadata={
                "user_id": user_id,
                "goal_title": goal_title,
                "competencies_count": len(competencies.get("competencies", [])),
            },
        )

    try:
        raw_output = call_gemini(
            system_instruction=DAG_BUILDER_SYSTEM_PROMPT,
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
                "summary": "",
                "nodes": [],
                "edges": [],
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
        # score, explanation = eval_dag_quality(goal_title, parsed)
        # if span:
        #     span.add_evaluation(
        #         name="dag_quality",
        #         score=score,
        #         details=explanation,
        #     )

        return parsed

    except Exception as exc:
        if span:
            span.add_event(
                name="dag_builder_exception",
                metadata={"error": str(exc)},
            )
        raise

    finally:
        if span:
            span.end()
