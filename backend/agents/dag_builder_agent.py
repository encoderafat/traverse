# agents/dag_builder_agent.py

from typing import Dict, Any, Optional
import json

from services.llm_client import call_gemini
from services.opik_client import create_opik_tracer
from services.ab_testing import select_variant

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

Quality requirements (very important):
- The node description must be detailed and actionable, not vague.
- Each description MUST include:
  1) Why it matters in real-world practice,
  2) The 2-4 key subskills or ideas inside the node,
  3) A concrete outcome or mini-deliverable (what the learner can do after this node).
- Keep descriptions concise but information-dense (3-5 sentences).
- Use specific language and domain terms, not generic phrasing.
- Ensure coverage depth: avoid overly broad nodes like "LLM Basics" unless they are broken into specific subtopics.

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

# Bump this when the prompt changes meaningfully.
PROMPT_VERSION = "dag_builder_v1"
EXPERIMENT_NAME = "dag_prompt"
EXPERIMENT_VARIANTS = ["A", "B"]
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
    def _parse_eval(raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3 and lines[-1].strip().startswith("```"):
                cleaned = "\n".join(lines[1:-1]).strip()
        if "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
        return json.loads(cleaned)

    raw = ""
    parsed = None
    for _ in range(2):
        try:
            raw = call_gemini(
                system_instruction=DAG_EVAL_SYSTEM_PROMPT,
                user_message=eval_user_msg,
            )
            parsed = _parse_eval(raw)
            return parsed.get("overall_score", 0.0), parsed
        except Exception:
            parsed = None

    if raw:
        print("DAG_EVAL_JSON_PARSE_ERROR")
        print(raw[:2000])

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
    from opik import start_as_current_trace, start_as_current_span

    variant = select_variant(user_id, EXPERIMENT_NAME, EXPERIMENT_VARIANTS)
    prompt_by_variant = {
        "A": DAG_BUILDER_SYSTEM_PROMPT,
        "B": DAG_BUILDER_SYSTEM_PROMPT,
    }
    system_prompt = prompt_by_variant[variant]

    with start_as_current_trace(
        name="build_learning_dag",
        tags=["dag", "curriculum-structuring", PROMPT_VERSION, f"{EXPERIMENT_NAME}:{variant}"],
        metadata={
            "user_id": user_id,
            "goal_title": goal_title,
            "competencies_count": len(competencies.get("competencies", [])),
            "prompt_version": PROMPT_VERSION,
            "experiment": EXPERIMENT_NAME,
            "variant": variant,
        },
        project_name="learning-paths"
    ) as trace:
        user_msg = f"""
        User goal: {goal_title}
        User background (free text): {user_background or "N/A"}

        Competencies JSON:
        {json.dumps(competencies, indent=2)}
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

        def _parse_dag(raw_text: str) -> Dict[str, Any]:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 3 and lines[-1].strip().startswith("```"):
                    cleaned = "\n".join(lines[1:-1]).strip()
            if "{" in cleaned and "}" in cleaned:
                cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
            return json.loads(cleaned)

        try:
            parsed = _parse_dag(raw_output)
        except Exception:
            print("DAG_BUILDER_JSON_PARSE_ERROR")
            print(raw_output[:2000])
            parsed = {
                "summary": "",
                "nodes": [],
                "edges": [],
                "error": "invalid_json_from_model",
            }


        score, details = eval_dag_quality(goal_title, parsed)

        trace.input = {"goal_title": goal_title, "competencies_count": len(competencies.get("competencies", []))}
        trace.output = {
            "nodes_count": len(parsed.get("nodes", [])),
            "edges_count": len(parsed.get("edges", [])),
            "llm_invalid_json": parsed.get("error") == "invalid_json_from_model",
            "eval_overall_score": score,
            "eval_dimension_scores": details.get("dimension_scores"),
            "eval_failed": "error" in details,
        }


        return parsed


# -----------------------------------------------------------------------------
# Remedial Node Agent
# -----------------------------------------------------------------------------

REMEDIAL_NODE_SYSTEM_PROMPT = """
You are an expert curriculum designer who specializes in adaptive learning.

A user is struggling with a specific concept in their learning path. Your task is to create a SINGLE, small, remedial (prerequisite) learning node to help them understand the fundamentals.

You will be given the user's goal, the node they are struggling with (title + description), and a suggestion for the remedial topic.

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

REMEDIAL_PROMPT_VERSION = "remedial_v1"
REMEDIAL_EXPERIMENT_NAME = "remedial_prompt"
REMEDIAL_EXPERIMENT_VARIANTS = ["A", "B"]

def run_remedial_node_agent(
    user_id: str,
    goal_title: str,
    struggling_node_title: str,
    struggling_node_description: str,
    adaptation_suggestion: str,
) -> Dict[str, Any]:
    """
    Generates a single remedial node to help a struggling user.
    """
    from opik import start_as_current_trace, start_as_current_span

    variant = select_variant(user_id, REMEDIAL_EXPERIMENT_NAME, REMEDIAL_EXPERIMENT_VARIANTS)
    prompt_by_variant = {
        "A": REMEDIAL_NODE_SYSTEM_PROMPT,
        "B": REMEDIAL_NODE_SYSTEM_PROMPT,
    }
    system_prompt = prompt_by_variant[variant]

    with start_as_current_trace(
        name="generate_remedial_node",
        tags=["remedial", "adaptive-learning", REMEDIAL_PROMPT_VERSION, f"{REMEDIAL_EXPERIMENT_NAME}:{variant}"],
        metadata={
            "user_id": user_id,
            "goal_title": goal_title,
            "struggling_node_title": struggling_node_title,
            "adaptation_suggestion": adaptation_suggestion,
            "prompt_version": REMEDIAL_PROMPT_VERSION,
            "experiment": REMEDIAL_EXPERIMENT_NAME,
            "variant": variant,
        },
        project_name="learning-paths"
    ) as trace:
        user_msg = f"""
        User's Main Goal: {goal_title}
        Node They Are Struggling With: "{struggling_node_title}"
        Node Description: "{struggling_node_description}"
        Tutor's Suggestion for a Remedial Topic: "{adaptation_suggestion}"

        Based on this, generate one small, prerequisite node as described in the system prompt.
        """

        def _parse_remedial(raw_text: str) -> Dict[str, Any]:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if len(lines) >= 3 and lines[-1].strip().startswith("```"):
                    cleaned = "\n".join(lines[1:-1]).strip()
            return json.loads(cleaned)

        raw_output = ""
        parsed = None
        for attempt in range(2):
            with start_as_current_span(
                name="call_gemini",
                type="llm",
                metadata={"model": "gemini", "attempt": attempt + 1}
            ) as span:
                raw_output = call_gemini(
                    system_instruction=system_prompt,
                    user_message=user_msg,
                )
                span.input = {"user_msg": user_msg[:500]}  # Limit input size
                span.output = {"raw_output": raw_output[:500]}  # Limit output size

            try:
                parsed = _parse_remedial(raw_output)
                break
            except Exception:
                parsed = {
                    "error": "invalid_json_from_model",
                    "title": "",
                    "description": "",
                }

        if parsed is None:
            parsed = {
                "error": "invalid_json_from_model",
                "title": "",
                "description": "",
            }

        trace.input = {"goal_title": goal_title, "struggling_node_title": struggling_node_title}
        trace.output = {
            "generated_node_title": parsed.get("title"),
            "has_description": bool(parsed.get("description")),
            "llm_invalid_json": parsed.get("error") == "invalid_json_from_model",
        }

        return parsed
