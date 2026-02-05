import uuid
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db import get_db
from core.auth import get_current_user_id
from models import (
    Base,
    User,
    LearningPath,
    PathNode,
    PathEdge,
    NodeProgress,
    NodeProgressStatus,
    Challenge,
)


def _make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def _make_client(db_session, user_id: str) -> TestClient:
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    def _get_current_user_id_override():
        return user_id

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user_id] = _get_current_user_id_override
    return TestClient(app)


def _seed_path_with_challenge(db_session, user_id: uuid.UUID):
    user = User(id=user_id, email="test@example.com")
    db_session.add(user)
    db_session.flush()

    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test",
        domain_hint="testing",
        level="beginner",
        summary="summary",
    )
    db_session.add(path)
    db_session.flush()

    node_a = PathNode(
        path_id=path.id,
        title="Node A",
        description="A",
        node_type="concept",
        estimated_minutes=10,
    )
    node_b = PathNode(
        path_id=path.id,
        title="Node B",
        description="B",
        node_type="concept",
        estimated_minutes=10,
    )
    db_session.add(node_a)
    db_session.add(node_b)
    db_session.flush()

    edge = PathEdge(path_id=path.id, from_node_id=node_a.id, to_node_id=node_b.id)
    db_session.add(edge)

    challenge = Challenge(node_id=node_b.id, prompt="Q?")
    db_session.add(challenge)

    progress = NodeProgress(
        user_id=user_id,
        node_id=node_b.id,
        learning_path_id=path.id,
        status=NodeProgressStatus.IN_PROGRESS,
        attempts_count=2,
    )
    db_session.add(progress)
    db_session.commit()

    return path, node_a, node_b, challenge, progress


def _mock_tutor_result():
    return {
        "overall_score": 0.2,
        "pass": False,
        "feedback_summary": "Needs work",
        "suggestions": [],
        "adaptation_suggestion": "Basics of X",
    }


def _mock_remedial_node():
    return {
        "title": "Remedial Basics",
        "description": "Short remedial description.",
        "node_type": "concept",
        "estimated_minutes": 15,
        "tags": ["remedial"],
    }


def test_remedial_node_creation_and_rewire(monkeypatch):
    db_session = _make_session()
    user_id = uuid.uuid4()
    path, node_a, node_b, challenge, progress = _seed_path_with_challenge(db_session, user_id)

    from routes import challenges as challenges_module

    monkeypatch.setattr(challenges_module, "run_tutor_agent", lambda **_: _mock_tutor_result())
    monkeypatch.setattr(challenges_module, "run_remedial_node_agent", lambda **_: _mock_remedial_node())

    client = _make_client(db_session, str(user_id))
    res = client.post(f"/api/challenges/{challenge.id}/submit", json={"answer": "test"})
    assert res.status_code == 200
    assert res.json()["remedial_added"] is True

    remedials = db_session.query(PathNode).filter(PathNode.path_id == path.id, PathNode.node_type == "remedial").all()
    assert len(remedials) == 1
    remedial_node = remedials[0]

    edges = db_session.query(PathEdge).filter(PathEdge.path_id == path.id).all()
    edge_pairs = {(e.from_node_id, e.to_node_id) for e in edges}
    assert (node_a.id, remedial_node.id) in edge_pairs
    assert (remedial_node.id, node_b.id) in edge_pairs
    assert (node_a.id, node_b.id) not in edge_pairs

    remedial_progress = db_session.query(NodeProgress).filter(
        NodeProgress.user_id == user_id,
        NodeProgress.node_id == remedial_node.id,
    ).first()
    assert remedial_progress is not None
    assert remedial_progress.status == NodeProgressStatus.NOT_STARTED

    refreshed_progress = db_session.query(NodeProgress).filter(NodeProgress.id == progress.id).first()
    assert refreshed_progress.status == NodeProgressStatus.NOT_STARTED
    assert refreshed_progress.attempts_count == 0


def test_remedial_duplicate_guard(monkeypatch):
    db_session = _make_session()
    user_id = uuid.uuid4()
    path, node_a, node_b, challenge, progress = _seed_path_with_challenge(db_session, user_id)

    remedial = PathNode(
        path_id=path.id,
        title="Existing Remedial",
        description="Existing",
        node_type="remedial",
        estimated_minutes=10,
    )
    db_session.add(remedial)
    db_session.flush()
    db_session.add(PathEdge(path_id=path.id, from_node_id=remedial.id, to_node_id=node_b.id))
    db_session.commit()

    from routes import challenges as challenges_module

    monkeypatch.setattr(challenges_module, "run_tutor_agent", lambda **_: _mock_tutor_result())
    monkeypatch.setattr(challenges_module, "run_remedial_node_agent", lambda **_: _mock_remedial_node())

    client = _make_client(db_session, str(user_id))
    res = client.post(f"/api/challenges/{challenge.id}/submit", json={"answer": "test"})
    assert res.status_code == 200
    assert res.json()["remedial_added"] is False

    remedials = db_session.query(PathNode).filter(PathNode.path_id == path.id, PathNode.node_type == "remedial").all()
    assert len(remedials) == 1


def test_remedial_cap(monkeypatch):
    db_session = _make_session()
    user_id = uuid.uuid4()
    path, node_a, node_b, challenge, progress = _seed_path_with_challenge(db_session, user_id)

    for i in range(3):
        db_session.add(PathNode(
            path_id=path.id,
            title=f"Remedial {i}",
            description="Existing",
            node_type="remedial",
            estimated_minutes=10,
        ))
    db_session.commit()

    from routes import challenges as challenges_module

    monkeypatch.setattr(challenges_module, "run_tutor_agent", lambda **_: _mock_tutor_result())
    monkeypatch.setattr(challenges_module, "run_remedial_node_agent", lambda **_: _mock_remedial_node())

    client = _make_client(db_session, str(user_id))
    res = client.post(f"/api/challenges/{challenge.id}/submit", json={"answer": "test"})
    assert res.status_code == 200
    assert res.json()["remedial_added"] is False

    remedials = db_session.query(PathNode).filter(PathNode.path_id == path.id, PathNode.node_type == "remedial").all()
    assert len(remedials) == 3


def test_remedial_validation_rollback(monkeypatch):
    db_session = _make_session()
    user_id = uuid.uuid4()
    path, node_a, node_b, challenge, progress = _seed_path_with_challenge(db_session, user_id)

    from routes import challenges as challenges_module

    monkeypatch.setattr(challenges_module, "run_tutor_agent", lambda **_: _mock_tutor_result())
    monkeypatch.setattr(challenges_module, "run_remedial_node_agent", lambda **_: _mock_remedial_node())
    monkeypatch.setattr(challenges_module, "_validate_dag", lambda *_: ["cycle"])

    client = _make_client(db_session, str(user_id))
    res = client.post(f"/api/challenges/{challenge.id}/submit", json={"answer": "test"})
    assert res.status_code == 200
    assert res.json()["remedial_added"] is False

    remedials = db_session.query(PathNode).filter(PathNode.path_id == path.id, PathNode.node_type == "remedial").all()
    assert len(remedials) == 0

    refreshed_progress = db_session.query(NodeProgress).filter(NodeProgress.id == progress.id).first()
    assert refreshed_progress.status == NodeProgressStatus.BLOCKED
    assert refreshed_progress.attempts_count == 3


def test_remedial_retry_on_malformed(monkeypatch):
    db_session = _make_session()
    user_id = uuid.uuid4()
    path, node_a, node_b, challenge, progress = _seed_path_with_challenge(db_session, user_id)

    from routes import challenges as challenges_module

    monkeypatch.setattr(challenges_module, "run_tutor_agent", lambda **_: _mock_tutor_result())
    calls = {"count": 0}

    def _remedial_side_effect(**_):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"title": "", "description": ""}
        return _mock_remedial_node()

    monkeypatch.setattr(challenges_module, "run_remedial_node_agent", _remedial_side_effect)

    client = _make_client(db_session, str(user_id))
    res = client.post(f"/api/challenges/{challenge.id}/submit", json={"answer": "test"})
    assert res.status_code == 200
    assert res.json()["remedial_added"] is True
    assert calls["count"] == 2
