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
# Evaluation Prompt
# -----------------------------------------------------------------------------

DAG_EVAL_SYSTEM_PROMPT = """
You are an expert curriculum evaluator.

You are evaluating a learning DAG for a user goal.

Assess the DAG on:
1. Structural correctness (acyclic, valid prerequisites)
2. Learning progression (concepts build logically)
3. Coverage (important areas not missing or duplicated)

Score each dimension from 0-5.
Provide an overall score between 0.0 and 1.0.

Output STRICT JSON:
{
  "dimension_scores": [
    { "name": "Structure", "score": 0-5, "comment": "..." },
    { "name": "Progression", "score": 0-5, "comment": "..." },
    { "name": "Coverage", "score": 0-5, "comment": "..." }
  ],
  "overall_score": 0.0,
  "summary": "Brief evaluation summary"
}
"""

def eval_dag_quality(goal_title: str, dag_json: Dict[str, Any]):
    eval_user_msg = f"""
User goal: {goal_title}

Generated DAG JSON:
{json.dumps(dag_json, indent=2)}

Please evaluate this DAG.
"""
    try:
        raw = call_gemini(
            system_instruction=DAG_EVAL_SYSTEM_PROMPT,
            user_message=eval_user_msg,
        )
        parsed = json.loads(raw)
        return parsed.get("overall_score", 0.0), parsed
    except Exception:
        return 0.5, {"error": "dag_evaluation_failed"}


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

        score, details = eval_dag_quality(goal_title, parsed)
        if span:
            span.add_evaluation(
                name="dag_quality",
                score=score,
                details=details,
            )


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


# -----------------------------------------------------------------------------
# Remedial Node Agent
# -----------------------------------------------------------------------------

REMEDIAL_NODE_SYSTEM_PROMPT = """
You are an expert curriculum designer who specializes in adaptive learning.

A user is struggling with a specific concept in their learning path. Your task is to create a SINGLE, small, remedial (prerequisite) learning node to help them understand the fundamentals.

You will be given the user's goal, the node they are struggling with, and a suggestion for the remedial topic.

Rules:
- The node you create should be a small, foundational concept that can be learned quickly.
- The title and description should be encouraging and clear.
- Estimate a short learning time (e.g., 10-20 minutes).

Output STRICT JSON with the new node's content:
{
  "title": "...",
  "description": "...",
  "node_type": "concept",
  "estimated_minutes": 15,
  "tags": ["remedial", "adaptive"]
}
"""

def run_remedial_node_agent(
    user_id: str,
    goal_title: str,
    struggling_node_title: str,
    adaptation_suggestion: str,
) -> Dict[str, Any]:
    """
    Generates a single remedial node to help a struggling user.
    """
    user_msg = f"""
    User's Main Goal: {goal_title}
    Node They Are Struggling With: "{struggling_node_title}"
    Tutor's Suggestion for a Remedial Topic: "{adaptation_suggestion}"

    Based on this, generate one small, prerequisite node as described in the system prompt.
    """

    span = None
    if opik_tracer:
        span = opik_tracer.start_span(
            "generate_remedial_node",
            metadata={
                "user_id": user_id,
                "goal_title": goal_title,
                "struggling_node_title": struggling_node_title,
                "adaptation_suggestion": adaptation_suggestion,
            },
        )
    
    try:
        raw_output = call_gemini(
            system_instruction=REMEDIAL_NODE_SYSTEM_PROMPT,
            user_message=user_msg,
        )
        if span:
            span.add_event("remedial_model_response", {"raw_output": raw_output})
        
        parsed = json.loads(raw_output)
        return parsed

    except Exception as exc:
        if span:
            span.add_event("remedial_agent_exception", {"error": str(exc)})
        raise
    finally:
        if span:
            span.end()
