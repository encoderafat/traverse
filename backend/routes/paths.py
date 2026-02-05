from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import json


from models import LearningPath, PathNode, PathEdge, NodeProgress, NodeProgressStatus, User
from schemas import (
    CreatePathRequest, LearningPathResponse, PathNodeSchema, PathEdgeSchema
)
from db import get_db
from agents.research_agent import run_research_agent
from agents.dag_builder_agent import run_dag_builder_agent
from core.auth import get_optional_user, require_role, enforce_ownership, get_current_user, get_or_create_user_from_token

router = APIRouter(tags=["paths"])

def _validate_dag(dag: dict) -> list[str]:
    """
    Validate structure and acyclicity of a DAG produced by the agent.
    Returns a list of error messages; empty list means valid.
    """
    errors: list[str] = []
    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])

    if not isinstance(nodes, list) or not nodes:
        errors.append("DAG must include a non-empty 'nodes' list.")
        return errors

    node_ids = []
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            errors.append("All nodes must have an 'id'.")
            continue
        node_ids.append(node_id)

    if len(set(node_ids)) != len(node_ids):
        errors.append("Node ids must be unique.")

    if not isinstance(edges, list):
        errors.append("DAG 'edges' must be a list.")
        return errors

    node_id_set = set(node_ids)
    edge_set = set()
    in_degree: dict[str, int] = {nid: 0 for nid in node_id_set}
    adjacency: dict[str, list[str]] = {nid: [] for nid in node_id_set}

    for edge in edges:
        src = edge.get("from")
        dst = edge.get("to")
        if not src or not dst:
            errors.append("Each edge must include 'from' and 'to'.")
            continue
        if src == dst:
            errors.append(f"Self-edge detected at '{src}'.")
            continue
        if src not in node_id_set or dst not in node_id_set:
            errors.append(f"Edge references unknown node: {src} -> {dst}.")
            continue
        key = (src, dst)
        if key in edge_set:
            errors.append(f"Duplicate edge detected: {src} -> {dst}.")
            continue
        edge_set.add(key)
        adjacency[src].append(dst)
        in_degree[dst] += 1

    if errors:
        return errors

    # Kahn's algorithm for cycle detection
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    visited = 0
    while queue:
        current = queue.pop()
        visited += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(node_id_set):
        errors.append("DAG contains a cycle.")

    return errors

def _ensure_sink_connectivity(dag: dict) -> dict:
    """
    Ensure leaf nodes flow forward using list order without creating cycles.
    This is a light post-processing step to reduce orphaned leaf nodes.
    """
    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])
    if not isinstance(nodes, list) or not nodes:
        return dag
    if not isinstance(edges, list):
        dag["edges"] = []
        edges = dag["edges"]

    node_ids = [n.get("id") for n in nodes if n.get("id")]
    out_degree = {nid: 0 for nid in node_ids}
    existing_edges = set()
    adjacency = {nid: [] for nid in node_ids}
    for e in edges:
        src = e.get("from")
        dst = e.get("to")
        if src in out_degree:
            out_degree[src] += 1
        if src and dst:
            existing_edges.add((src, dst))
            if src in adjacency:
                adjacency[src].append(dst)

    # Helper to avoid introducing cycles
    def _has_path(start: str, target: str) -> bool:
        if start == target:
            return True
        seen = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current == target:
                return True
            if current in seen:
                continue
            seen.add(current)
            for nxt in adjacency.get(current, []):
                if nxt not in seen:
                    stack.append(nxt)
        return False

    id_to_index = {nid: idx for idx, nid in enumerate(node_ids)}

    for nid, degree in out_degree.items():
        if degree == 0 and (nid, sink_id) not in existing_edges:
            idx = id_to_index.get(nid)
            if idx is None:
                continue
            # Prefer the next node in list order.
            next_id = None
            if idx + 1 < len(node_ids):
                next_id = node_ids[idx + 1]
            # If no next node, fall back to last node in list.
            if not next_id and node_ids:
                next_id = node_ids[-1]
            if not next_id or next_id == nid:
                continue
            # Avoid cycles: don't add if next can already reach nid.
            if _has_path(next_id, nid):
                continue
            edges.append({"from": nid, "to": next_id})
            existing_edges.add((nid, next_id))
            adjacency[nid].append(next_id)

    return dag



@router.post("/paths", response_model=LearningPathResponse)
def create_path(
    payload: CreatePathRequest,
    db: Session = Depends(get_db),
    current_user_db: User = Depends(get_or_create_user_from_token),
):
    user_id = str(current_user_db.id)
    user_uuid = current_user_db.id


    research_result = run_research_agent(
        user_id=user_id,
        goal_title=payload.goal_title,
        goal_description=payload.goal_description,
        domain_hint=payload.domain_hint,
        level=payload.level,
    )
    
    research_competencies = research_result["competencies"]
    research_context = research_result["research_context"]

    dag = run_dag_builder_agent(
        user_id=user_id,
        goal_title=payload.goal_title,
        competencies=research_competencies,
        user_background=payload.user_background,
    )
    dag = _ensure_sink_connectivity(dag)

    validation_errors = _validate_dag(dag)
    if validation_errors:
        # Retry once to reduce user-facing failures from occasional LLM hiccups.
            dag = run_dag_builder_agent(
                user_id=user_id,
                goal_title=payload.goal_title,
                competencies=research_competencies,
                user_background=payload.user_background,
            )
            dag = _ensure_sink_connectivity(dag)
            validation_errors = _validate_dag(dag)

    if validation_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "We couldn't generate a valid learning graph. Please try again.",
                "errors": validation_errors,
            },
        )

    lp = LearningPath(
        user_id=user_uuid,
        goal_title=payload.goal_title,
        goal_description=payload.goal_description,
        domain_hint=payload.domain_hint,
        level=payload.level,
        summary=dag.get("summary", ""),
        research_context=research_context,
    )
    db.add(lp)
    db.flush()

    node_id_map = {}

    for node in dag.get("nodes", []):
        n = PathNode(
            path_id=lp.id,
            title=node["title"],
            description=node["description"],
            node_type=node.get("node_type", "concept"),
            estimated_minutes=node.get("estimated_minutes"),
            metadata_json={"tags": node.get("tags", [])},
        )
        db.add(n)
        db.flush()
        node_id_map[node["id"]] = n.id

        db.add(NodeProgress(
            user_id=user_uuid,
            node_id=n.id,
            status=NodeProgressStatus.NOT_STARTED,
            learning_path_id=lp.id, # Ensure learning_path_id is set
        ))

    for edge in dag.get("edges", []):
        if edge["from"] in node_id_map and edge["to"] in node_id_map:
            db.add(PathEdge(
                path_id=lp.id,
                from_node_id=node_id_map[edge["from"]],
                to_node_id=node_id_map[edge["to"]],
            ))

    db.commit()
    db.refresh(lp)

    return LearningPathResponse(
        id=lp.id,
        goal_title=lp.goal_title,
        summary=lp.summary,
        research_context=lp.research_context,
        nodes=[PathNodeSchema.from_orm(n) for n in lp.nodes],
        edges=[PathEdgeSchema(from_node_id=e.from_node_id, to_node_id=e.to_node_id) for e in lp.edges],
    )


@router.post("/paths/stream")
def create_path_stream(
    payload: CreatePathRequest,
    db: Session = Depends(get_db),
    current_user_db: User = Depends(get_or_create_user_from_token),
):
    user_id = str(current_user_db.id)
    user_uuid = current_user_db.id

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    def event_stream():
        try:
            yield sse("progress", {"step": "research", "percent": 20, "message": "Researching expertise..."})
            research_result = run_research_agent(
                user_id=user_id,
                goal_title=payload.goal_title,
                goal_description=payload.goal_description,
                domain_hint=payload.domain_hint,
                level=payload.level,
            )

            research_competencies = research_result["competencies"]
            research_context = research_result["research_context"]

            yield sse("progress", {"step": "dag", "percent": 60, "message": "Building learning graph..."})
            dag = run_dag_builder_agent(
                user_id=user_id,
                goal_title=payload.goal_title,
                competencies=research_competencies,
                user_background=payload.user_background,
            )
            dag = _ensure_sink_connectivity(dag)

            validation_errors = _validate_dag(dag)
            if validation_errors:
                yield sse("error", {
                    "message": "We couldn't generate a valid learning graph. Please try again.",
                    "errors": validation_errors,
                })
                return

            yield sse("progress", {"step": "save", "percent": 90, "message": "Saving your path..."})
            lp = LearningPath(
                user_id=user_uuid,
                goal_title=payload.goal_title,
                goal_description=payload.goal_description,
                domain_hint=payload.domain_hint,
                level=payload.level,
                summary=dag.get("summary", ""),
                research_context=research_context,
            )
            db.add(lp)
            db.flush()

            node_id_map = {}
            for node in dag.get("nodes", []):
                n = PathNode(
                    path_id=lp.id,
                    title=node["title"],
                    description=node["description"],
                    node_type=node.get("node_type", "concept"),
                    estimated_minutes=node.get("estimated_minutes"),
                    metadata_json={"tags": node.get("tags", [])},
                )
                db.add(n)
                db.flush()
                node_id_map[node["id"]] = n.id

                db.add(NodeProgress(
                    user_id=user_uuid,
                    node_id=n.id,
                    status=NodeProgressStatus.NOT_STARTED,
                    learning_path_id=lp.id,
                ))

            for edge in dag.get("edges", []):
                if edge["from"] in node_id_map and edge["to"] in node_id_map:
                    db.add(PathEdge(
                        path_id=lp.id,
                        from_node_id=node_id_map[edge["from"]],
                        to_node_id=node_id_map[edge["to"]],
                    ))

            db.commit()
            db.refresh(lp)

            yield sse("done", {"path_id": lp.id})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/paths", response_model=List[LearningPathResponse])
def list_paths(
    db: Session = Depends(get_db),
    current_user_db: User = Depends(get_or_create_user_from_token),
):
    user_uuid = current_user_db.id

    paths = (
        db.query(LearningPath)
        .filter(LearningPath.user_id == user_uuid)
        .order_by(LearningPath.created_at.desc())
        .all()
    )

    return [
        LearningPathResponse(
            id=lp.id,
            goal_title=lp.goal_title,
            summary=lp.summary,
            research_context=lp.research_context,
            nodes=[
                PathNodeSchema.from_orm(n) for n in lp.nodes
            ],
            edges=[
                PathEdgeSchema(
                    from_node_id=e.from_node_id,
                    to_node_id=e.to_node_id,
                )
                for e in lp.edges
            ],
        )
        for lp in paths
    ]


@router.get("/paths/{path_id}", response_model=LearningPathResponse)
def get_path(
    path_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_optional_user),  # anonymous allowed
):
    lp = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Path not found")

    # If logged in, enforce ownership
    if user:
        enforce_ownership(
            resource_user_id=lp.user_id,
            current_user=user,
        )

    return LearningPathResponse(
        id=lp.id,
        goal_title=lp.goal_title,
        summary=lp.summary,
        research_context=lp.research_context,
        nodes=[PathNodeSchema.from_orm(n) for n in lp.nodes],
        edges=[PathEdgeSchema(from_node_id=e.from_node_id, to_node_id=e.to_node_id) for e in lp.edges],
    )


@router.delete("/paths/{path_id}")
def delete_path(
    path_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    lp = db.query(LearningPath).filter(LearningPath.id == path_id).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Path not found")

    enforce_ownership(
        resource_user_id=lp.user_id,
        current_user=user,
    )

    db.delete(lp)
    db.commit()

    return {"deleted": path_id}
