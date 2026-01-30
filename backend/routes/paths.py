from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List


from models import LearningPath, PathNode, PathEdge, NodeProgress, NodeProgressStatus
from schemas import (
    CreatePathRequest, LearningPathResponse, PathNodeSchema, PathEdgeSchema
)
from db import get_db
from agents.research_agent import run_research_agent
from agents.dag_builder_agent import run_dag_builder_agent
from core.auth import get_current_user_id, get_optional_user, require_role, enforce_ownership, get_current_user

router = APIRouter(prefix="/api/paths", tags=["paths"])


@router.post("", response_model=LearningPathResponse)
def create_path(
    payload: CreatePathRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),  # Supabase UUID
):
    user_uuid = UUID(user_id)

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


@router.get("/{path_id}", response_model=LearningPathResponse)
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

@router.delete("/{path_id}")
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

@router.get("", response_model=List[LearningPathResponse])
def list_paths(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

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