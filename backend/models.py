import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, JSON, Float
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    goal_title = Column(String, nullable=False)
    goal_description = Column(Text, nullable=True)
    domain_hint = Column(String, nullable=True)
    level = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nodes = relationship("PathNode", backref="path", cascade="all, delete-orphan")
    edges = relationship("PathEdge", backref="path", cascade="all, delete-orphan")


class PathNode(Base):
    __tablename__ = "path_nodes"

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    node_type = Column(String, nullable=False, default="concept")
    estimated_minutes = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)


class PathEdge(Base):
    __tablename__ = "path_edges"

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    from_node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)


class NodeProgressStatus:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class NodeProgress(Base):
    __tablename__ = "node_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)

    status = Column(String, nullable=False, default=NodeProgressStatus.NOT_STARTED)
    last_score = Column(Float, nullable=True)
    attempts_count = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    node = relationship("PathNode")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)

    prompt = Column(Text, nullable=False)
    expected_answer_outline = Column(Text, nullable=True)
    rubric_json = Column(JSON, nullable=True)
    difficulty = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("PathNode", backref="challenges")


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"

    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    submitted_answer = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    challenge = relationship("Challenge", backref="attempts")
