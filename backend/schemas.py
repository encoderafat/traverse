from typing import List, Optional
from pydantic import BaseModel, ConfigDict



class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LearningPathBase(BaseModel):
    goal_title: str
    summary: str


class LearningPathCreate(LearningPathBase):
    pass


class CreatePathRequest(BaseModel):
    goal_title: str
    goal_description: str
    domain_hint: str
    level: str
    user_background: str


class LearningPath(LearningPathBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class NodeBase(BaseModel):
    title: str
    description: str
    node_type: str
    estimated_minutes: int | None = None
    metadata_json: dict | None = None


class NodeCreate(NodeBase):
    pass


class Node(NodeBase):
    id: int
    path_id: int

    model_config = ConfigDict(from_attributes=True)


class EdgeBase(BaseModel):
    from_node_id: int
    to_node_id: int


class EdgeCreate(EdgeBase):
    pass


class Edge(EdgeBase):
    id: int
    path_id: int

    model_config = ConfigDict(from_attributes=True)


class ChallengeBase(BaseModel):
    prompt: str


class Challenge(ChallengeBase):
    challenge_id: int

    model_config = ConfigDict(from_attributes=True)

class PathNodeSchema(BaseModel):
    id: int
    title: str
    description: str
    node_type: str
    estimated_minutes: Optional[int] = None
    metadata_json: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)

class PathEdgeSchema(BaseModel):
    from_node_id: int
    to_node_id: int

class LearningPathResponse(BaseModel):
    id: int
    goal_title: str
    summary: str
    research_context: Optional[list] = None
    nodes: List[PathNodeSchema]
    edges: List[PathEdgeSchema]


class Hint(BaseModel):
    hint: str


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
    remedial_added: bool = False
