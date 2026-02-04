from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from db import get_db
from models import LearningPath, PathNode, NodeProgress, NodeProgressStatus
from pydantic import BaseModel
from core.auth import get_current_user_id

router = APIRouter(tags=["progress"])


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


class UpdateStatusPayload(BaseModel):
    status: NodeProgressStatus


@router.put("/paths/{path_id}/progress/nodes/{node_id}", response_model=NodeProgressItem)
def update_node_status(
    path_id: int,
    node_id: int,
    payload: UpdateStatusPayload,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

    # 1. Verify path ownership
    lp = db.query(LearningPath).filter(
        LearningPath.id == path_id,
        LearningPath.user_id == user_uuid,
    ).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Path not found")

    # 2. Verify node exists in path
    node = db.query(PathNode).filter(PathNode.id == node_id, PathNode.path_id == path_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="PathNode not found in this path")

    # 3. Find or create progress record
    progress = db.query(NodeProgress).filter(
        NodeProgress.node_id == node_id,
        NodeProgress.user_id == user_uuid,
    ).first()

    if progress:
        # 4. Update existing progress
        progress.status = payload.status
    else:
        # 5. Create new progress record
        progress = NodeProgress(
            user_id=user_uuid,
            node_id=node_id,
            learning_path_id=path_id,
            status=payload.status,
            last_score=1.0 if payload.status == NodeProgressStatus.COMPLETED else None,
            attempts_count=1,
        )
        db.add(progress)

    # 6. Commit changes
    db.commit()
    db.refresh(progress)
    
    # 7. Return updated item
    return NodeProgressItem(
        node_id=progress.node_id,
        title=node.title,
        status=progress.status,
        last_score=progress.last_score,
        attempts_count=progress.attempts_count,
    )


@router.get("/paths/{path_id}/progress", response_model=PathProgressResponse)
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
            NodeProgress.user_id == user_uuid,
            NodeProgress.learning_path_id == path_id,
        ).all()
    }

    # Build a map of prerequisites
    prereqs_map = {}
    for edge in lp.edges:
        if edge.to_node_id not in prereqs_map:
            prereqs_map[edge.to_node_id] = []
        prereqs_map[edge.to_node_id].append(edge.from_node_id)

    completed_count = 0
    items = []

    for node in lp.nodes:
        progress = progresses.get(node.id)
        status = progress.status if progress else NodeProgressStatus.NOT_STARTED
        
        # Check for blocked status
        is_blocked = False
        prereqs = prereqs_map.get(node.id, [])
        for prereq_id in prereqs:
            prereq_progress = progresses.get(prereq_id)
            if not prereq_progress or prereq_progress.status != NodeProgressStatus.COMPLETED:
                is_blocked = True
                break
        
        current_status = "blocked" if is_blocked else status
        
        if current_status == NodeProgressStatus.COMPLETED:
            completed_count += 1

        items.append(NodeProgressItem(
            node_id=node.id,
            title=node.title,
            status=current_status,
            last_score=progress.last_score if progress else None,
            attempts_count=progress.attempts_count if progress else 0,
        ))

    return PathProgressResponse(
        path_id=path_id,
        completion_ratio=completed_count / len(lp.nodes) if lp.nodes else 0.0,
        nodes=items,
    )
