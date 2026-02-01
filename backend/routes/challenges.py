from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel

from db import get_db
from models import (
    PathNode, LearningPath, Challenge, ChallengeAttempt, PathEdge,
    NodeProgress, NodeProgressStatus
)
from schemas import (
    ChallengeCreateResponse,
    ChallengeSubmitRequest,
    ChallengeSubmitResponse,
    Hint as HintSchema
)
from agents.challenge_agent import run_challenge_agent
from agents.tutor_agent import run_tutor_agent, run_hint_agent
from agents.dag_builder_agent import run_remedial_node_agent
from core.auth import get_current_user_id

router = APIRouter()

class HintRequest(BaseModel):
    hintLevel: int

# ... (create_or_get_challenge is assumed to be here)

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
    
    struggling_node = db.query(PathNode).filter(PathNode.id == ch.node_id).first()
    if not struggling_node:
        raise HTTPException(status_code=404, detail="Associated node not found")

    path = db.query(LearningPath).filter(LearningPath.id == struggling_node.path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="Associated path not found")

    np = db.query(NodeProgress).filter(
        NodeProgress.user_id == user_uuid,
        NodeProgress.node_id == ch.node_id,
    ).first()
    # Default to 0 if no progress record exists yet
    current_attempts = np.attempts_count if np else 0

    tutor_result = run_tutor_agent(
        user_id=user_id,
        challenge={
            "id": ch.id,
            "prompt": ch.prompt,
            "expected_answer_outline": (ch.expected_answer_outline or "").split("\n"),
            "rubric": ch.rubric_json or {},
        },
        user_answer=payload.answer,
        attempts_count=current_attempts,
    )

    overall_score = float(tutor_result.get("overall_score", 0.0))
    passed = bool(tutor_result.get("pass", False))
    adaptation_suggestion = tutor_result.get("adaptation_suggestion")

    db.add(ChallengeAttempt(
        challenge_id=ch.id,
        user_id=user_uuid,
        submitted_answer=payload.answer,
        score=overall_score,
        feedback=tutor_result.get("feedback_summary"),
    ))

    if np:
        np.attempts_count += 1
        np.last_score = overall_score
        new_status = (
            NodeProgressStatus.COMPLETED if passed
            else NodeProgressStatus.BLOCKED if np.attempts_count >= 3
            else NodeProgressStatus.IN_PROGRESS
        )
        np.status = new_status

        # ---- ADAPTIVE INTERVENTION LOGIC ----
        if new_status == NodeProgressStatus.BLOCKED and adaptation_suggestion:
            # 1. Generate the remedial node
            remedial_node_data = run_remedial_node_agent(
                user_id=user_id,
                goal_title=path.goal_title,
                struggling_node_title=struggling_node.title,
                adaptation_suggestion=adaptation_suggestion,
            )

            # 2. Create the new node in the DB
            remedial_node = PathNode(
                path_id=path.id,
                title=remedial_node_data["title"],
                description=remedial_node_data["description"],
                node_type=remedial_node_data.get("node_type", "concept"),
                estimated_minutes=remedial_node_data.get("estimated_minutes"),
                metadata_json={"tags": remedial_node_data.get("tags", [])},
            )
            db.add(remedial_node)
            db.flush() # Flush to get the new node's ID

            # Create a progress entry for the new node
            db.add(NodeProgress(
                user_id=user_uuid,
                node_id=remedial_node.id,
                status=NodeProgressStatus.NOT_STARTED,
            ))

            # 3. Perform Graph Surgery
            # Find incoming edges to the struggling node and reroute them
            incoming_edges = db.query(PathEdge).filter(
                PathEdge.path_id == path.id,
                PathEdge.to_node_id == struggling_node.id
            ).all()

            if not incoming_edges:
                # If the struggling node was a root, the new node becomes a root
                pass
            else:
                for edge in incoming_edges:
                    edge.to_node_id = remedial_node.id

            # Create a new edge from the remedial node to the struggling node
            db.add(PathEdge(
                path_id=path.id,
                from_node_id=remedial_node.id,
                to_node_id=struggling_node.id
            ))

            # 4. Reset the struggling node's progress
            np.status = NodeProgressStatus.NOT_STARTED
            np.attempts_count = 0
            np.last_score = None
    
    db.commit()

    return ChallengeSubmitResponse(
        score=overall_score,
        pass_node=passed,
        feedback_summary=tutor_result.get("feedback_summary", ""),
        suggestions=tutor_result.get("suggestions", []),
    )


@router.post("/challenges/{challenge_id}/hint", response_model=HintSchema)
def get_challenge_hint(
    challenge_id: int,
    payload: HintRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Call the Tutor Agent to generate a hint
    hint_text = run_hint_agent(
        challenge_prompt=ch.prompt,
        hint_level=payload.hintLevel,
        user_id=user_id,
    )

    return HintSchema(hint=hint_text)
