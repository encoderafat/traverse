from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class LearningPathBase(BaseModel):
    goal_title: str
    summary: str


class LearningPathCreate(LearningPathBase):
    pass


class LearningPath(LearningPathBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


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

    class Config:
        orm_mode = True


class EdgeBase(BaseModel):
    from_node_id: int
    to_node_id: int


class EdgeCreate(EdgeBase):
    pass


class Edge(EdgeBase):
    id: int
    path_id: int

    class Config:
        orm_mode = True


class ChallengeBase(BaseModel):
    prompt: str


class Challenge(ChallengeBase):
    challenge_id: int

    class Config:
        orm_mode = True

class Hint(BaseModel):
    hint: str
