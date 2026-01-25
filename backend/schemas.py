from typing import List, Optional, Any
from pydantic import BaseModel

class CreatePathRequest(BaseModel):
    goal_title: str
    goal_description: Optional[str] = None
    domain_hint: Optional[str] = None
    level: Optional[str] = None
    user_background: Optional[str] = None

class PathNodeSchema(BaseModel):
    id: int
    title: str
    description: str
    node_type: str
    estimated_minutes: Optional[int] = None
    metadata_json: Optional[dict] = None

class PathEdgeSchema(BaseModel):
    from_node_id: int
    to_node_id: int

class LearningPathResponse(BaseModel):
    id: int
    goal_title: str
    summary: Optional[str]
    nodes: List[PathNodeSchema]
    edges: List[PathEdgeSchema]

class ChallengeCreateResponse(BaseModel):
    challenge_id: int
    prompt: str

class ChallengeSubmitRequest(BaseModel):
    answer: str

class ChallengeSubmitResponse(BaseModel):
    score: float
    pass_node: bool
    feedback_summary: str
    suggestions: List[str]