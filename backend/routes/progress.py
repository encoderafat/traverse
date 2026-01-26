from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from db import get_db
from models import LearningPath, NodeProgress, NodeProgressStatus
from pydantic import BaseModel
from core.auth import get_current_user_id

router = APIRouter(prefix="/api/paths", tags=["progress"])


class NodeProgressItem(BaseModel):
    node_id: int
    title: str
    status: str
    last_score: float | None
    attempts_count: int


class PathProgressResponse(BaseModel):
    path_id: int
    completion_ratio: float
    nodes: List[NodeProgressItem]


@router.get("/{path_id}/progress", response_model=PathProgressResponse)
def get_path_progress(
    path_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

    lp = db.query(LearningPath).filter(
        LearningPath.id == path_id,
        LearningPath.user_id == user_uuid,
    ).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Path not found")

    progresses = {
        p.node_id: p
        for p in db.query(NodeProgress).filter(
            NodeProgress.user_id == user_uuid
        ).all()
    }

    completed = 0
    items = []

    for node in lp.nodes:
        p = progresses.get(node.id)
        if p and p.status == NodeProgressStatus.COMPLETED:
            completed += 1

        items.append(NodeProgressItem(
            node_id=node.id,
            title=node.title,
            status=p.status if p else NodeProgressStatus.NOT_STARTED,
            last_score=p.last_score if p else None,
            attempts_count=p.attempts_count if p else 0,
        ))

    return PathProgressResponse(
        path_id=path_id,
        completion_ratio=completed / len(lp.nodes) if lp.nodes else 0.0,
        nodes=items,
    )
