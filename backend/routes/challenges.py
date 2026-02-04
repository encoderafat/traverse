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

router = APIRouter(tags=["challenges"])

class HintRequest(BaseModel):
    hintLevel: int

@router.post("/paths/{path_id}/nodes/{node_id}/challenges", response_model=ChallengeCreateResponse)
def create_or_get_challenge(
    path_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    user_uuid = UUID(user_id)

    # 1. Check if challenge already exists for this node
    challenge = db.query(Challenge).filter(Challenge.node_id == node_id).first()
    if challenge:
        # If a previous generation produced an empty prompt, regenerate.
        if challenge.prompt and challenge.prompt.strip():
            return ChallengeCreateResponse(
                challenge_id=challenge.id,
                node_id=challenge.node_id,
                prompt=challenge.prompt,
                difficulty=challenge.difficulty,
            )
        db.delete(challenge)
        db.commit()

    # 2. Get node and path details for agent context
    node = db.query(PathNode).filter(PathNode.id == node_id, PathNode.path_id == path_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found in this path")
    
    lp = db.query(LearningPath).filter(LearningPath.id == path_id, LearningPath.user_id == user_uuid).first()
    if not lp:
        raise HTTPException(status_code=404, detail="Learning Path not found")

    # 3. Use challenge agent to generate a new challenge
    try:
        challenge_data = run_challenge_agent(
            user_id=user_id,
            path_id=path_id,
            node={
                "id": node.id,
                "title": node.title,
                "description": node.description,
                "node_type": node.node_type,
                "estimated_minutes": node.estimated_minutes,
                "metadata_json": node.metadata_json,
            },
            domain_hint=lp.domain_hint,
            research_context=lp.research_context or [],
        )
    except Exception as exc:
        # Surface the underlying error so we can debug quickly.
        raise HTTPException(
            status_code=503,
            detail=f"Challenge generation failed: {exc}",
        ) from exc

    # 4. Save the new challenge to DB
    expected_outline = challenge_data.get("expected_answer_outline")
    if isinstance(expected_outline, list):
        expected_outline = "\n".join(expected_outline)

    new_challenge = Challenge(
        node_id=node_id,
        prompt=challenge_data["prompt"],
        expected_answer_outline=expected_outline,
        rubric_json=challenge_data.get("rubric"),
        difficulty=challenge_data.get("difficulty"),
    )
    db.add(new_challenge)
    db.flush() # Flush to get the new challenge's ID
    db.commit()

    # 5. Create a NodeProgress entry for the user if it doesn't exist
    node_progress = db.query(NodeProgress).filter(
        NodeProgress.user_id == user_uuid,
        NodeProgress.node_id == node_id
    ).first()
    
    if not node_progress:
        db.add(NodeProgress(
            user_id=user_uuid,
            node_id=node_id,
            learning_path_id=path_id, # Ensure this is set
            status=NodeProgressStatus.IN_PROGRESS,
            attempts_count=0
        ))
        db.commit()


    return ChallengeCreateResponse(
        challenge_id=new_challenge.id,
        node_id=new_challenge.node_id,
        prompt=new_challenge.prompt,
        difficulty=new_challenge.difficulty,
    )

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

    remedial_added = False
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
        if (new_status == NodeProgressStatus.BLOCKED and adaptation_suggestion and not passed):
            # Guard: avoid creating multiple remedial nodes for the same struggling node
            existing_remedial = db.query(PathEdge).join(PathNode, PathEdge.from_node_id == PathNode.id).filter(
                PathEdge.path_id == path.id,
                PathEdge.to_node_id == struggling_node.id,
                PathNode.node_type == "remedial",
            ).first()

            if existing_remedial:
                db.commit()
                return ChallengeSubmitResponse(
                    score=overall_score,
                    pass_node=passed,
                    feedback_summary=tutor_result.get("feedback_summary", ""),
                    suggestions=tutor_result.get("suggestions", []),
                    remedial_added=False,
                )

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
                node_type="remedial",
                estimated_minutes=remedial_node_data.get("estimated_minutes"),
                metadata_json={"tags": remedial_node_data.get("tags", [])},
            )
            db.add(remedial_node)
            db.flush() # Flush to get the new node's ID

            # Create a progress entry for the new node
            db.add(NodeProgress(
                user_id=user_uuid,
                node_id=remedial_node.id,
                learning_path_id=path.id,
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

            remedial_added = True
    
    db.commit()

    return ChallengeSubmitResponse(
        score=overall_score,
        pass_node=passed,
        feedback_summary=tutor_result.get("feedback_summary", ""),
        suggestions=tutor_result.get("suggestions", []),
        remedial_added=remedial_added,
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
