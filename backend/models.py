from datetime import datetime
from typing import Optional, Dict, Any

try:
    from sqlalchemy import (
        Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Float
    )
    from sqlalchemy.orm import declarative_base, relationship
except ImportError:
    # Fallback for older SQLAlchemy versions
    from sqlalchemy import (
        Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
    )
    from sqlalchemy.orm import declarative_base, relationship
    Enum = None

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_title = Column(String, nullable=False)          # "Become a junior UX designer"
    goal_description = Column(Text, nullable=True)
    domain_hint = Column(String, nullable=True)          # "software", "fitness", "marketing", ...
    level = Column(String, nullable=True)                # "beginner", "intermediate", ...
    summary = Column(Text, nullable=True)                # short summary for UI
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="learning_paths")
    nodes = relationship("PathNode", backref="path", cascade="all, delete-orphan")
    edges = relationship("PathEdge", backref="path", cascade="all, delete-orphan")


class PathNode(Base):
    __tablename__ = "path_nodes"
    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    node_type = Column(String, nullable=False, default="concept")  # 'concept', 'skill', 'project', 'meta'
    estimated_minutes = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # tags, difficulty, domain_keywords, etc.


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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)
    status = Column(String, nullable=False, default=NodeProgressStatus.NOT_STARTED)
    last_score = Column(Float, nullable=True)  # 0..1 or 0..100 normalized
    attempts_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    node = relationship("PathNode")


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("path_nodes.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    expected_answer_outline = Column(Text, nullable=True)
    rubric_json = Column(JSON, nullable=True)
    difficulty = Column(String, nullable=True)  # 'easy', 'medium', 'hard'
    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("PathNode", backref="challenges")


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"
    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_answer = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    challenge = relationship("Challenge", backref="attempts")
    user = relationship("User")