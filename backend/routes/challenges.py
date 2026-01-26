from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models import (
    PathNode, LearningPath, Challenge, ChallengeAttempt,
    NodeProgress, NodeProgressStatus
)
from schemas import (
    ChallengeCreateResponse,
    ChallengeSubmitRequest,
    ChallengeSubmitResponse,
)
from agents.challenge_agent import run_challenge_agent
from agents.tutor_agent import run_tutor_agent
from core.auth import get_current_user_id

router = APIRouter(prefix="/api", tags=["challenges"])


@router.post("/paths/{path_id}/nodes/{node_id}/challenges", response_model=ChallengeCreateResponse)
def create_or_get_challenge(
    path_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

    path = db.query(LearningPath).filter(
        LearningPath.id == path_id,
        LearningPath.user_id == user_uuid,
    ).first()
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")

    node = db.query(PathNode).filter(
        PathNode.id == node_id,
        PathNode.path_id == path_id,
    ).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if node.challenges:
        ch = node.challenges[0]
    else:
        chall = run_challenge_agent(
            user_id=user_id,
            path_id=path_id,
            node={
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "node_type": node.node_type,
            },
            domain_hint=path.domain_hint,
        )

        ch = Challenge(
            node_id=node.id,
            prompt=chall["prompt"],
            expected_answer_outline="\n".join(chall.get("expected_answer_outline", [])),
            rubric_json=chall.get("rubric"),
            difficulty=chall.get("difficulty"),
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)

    np = db.query(NodeProgress).filter(
        NodeProgress.user_id == user_uuid,
        NodeProgress.node_id == node.id,
    ).first()
    if np:
        np.status = NodeProgressStatus.IN_PROGRESS
        db.commit()

    return ChallengeCreateResponse(challenge_id=ch.id, prompt=ch.prompt)


@router.post("/challenges/{challenge_id}/submit", response_model=ChallengeSubmitResponse)
def submit_challenge(
    challenge_id: int,
    payload: ChallengeSubmitRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    tutor_result = run_tutor_agent(
        user_id=user_id,
        challenge={
            "id": ch.id,
            "prompt": ch.prompt,
            "expected_answer_outline": (ch.expected_answer_outline or "").split("\n"),
            "rubric": ch.rubric_json or {},
        },
        user_answer=payload.answer,
    )

    overall_score = float(tutor_result.get("overall_score", 0.0))
    passed = bool(tutor_result.get("pass", False))

    db.add(ChallengeAttempt(
        challenge_id=ch.id,
        user_id=user_uuid,
        submitted_answer=payload.answer,
        score=overall_score,
        feedback=tutor_result.get("feedback_summary"),
    ))

    np = db.query(NodeProgress).filter(
        NodeProgress.user_id == user_uuid,
        NodeProgress.node_id == ch.node_id,
    ).first()
    if np:
        np.attempts_count += 1
        np.last_score = overall_score
        np.status = (
            NodeProgressStatus.COMPLETED if passed
            else NodeProgressStatus.BLOCKED if np.attempts_count >= 3
            else NodeProgressStatus.IN_PROGRESS
        )

    db.commit()

    return ChallengeSubmitResponse(
        score=overall_score,
        pass_node=passed,
        feedback_summary=tutor_result.get("feedback_summary", ""),
        suggestions=tutor_result.get("suggestions", []),
    )
