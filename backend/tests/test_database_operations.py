import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, LearningPath, PathNode, PathEdge, Challenge, ChallengeAttempt, NodeProgress, NodeProgressStatus
from uuid import uuid4


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()


def test_learning_path_crud(test_db):
    """Test CRUD operations for LearningPath model."""
    from uuid import UUID
    
    # Create a user UUID
    user_id = uuid4()
    
    # Create
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    # Assert creation worked
    assert path.id is not None
    assert path.goal_title == "Test Path"
    assert path.user_id == user_id
    
    # Read
    retrieved_path = test_db.query(LearningPath).filter(LearningPath.id == path.id).first()
    assert retrieved_path is not None
    assert retrieved_path.goal_title == "Test Path"
    
    # Update
    retrieved_path.goal_title = "Updated Path"
    test_db.commit()
    
    # Verify update
    updated_path = test_db.query(LearningPath).filter(LearningPath.id == path.id).first()
    assert updated_path.goal_title == "Updated Path"
    
    # Delete
    test_db.delete(retrieved_path)
    test_db.commit()
    
    # Verify deletion
    deleted_path = test_db.query(LearningPath).filter(LearningPath.id == path.id).first()
    assert deleted_path is None


def test_path_node_crud(test_db):
    """Test CRUD operations for PathNode model."""
    from uuid import UUID
    
    # Create a user and path first
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    # Create a node
    node = PathNode(
        path_id=path.id,
        title="Test Node",
        description="Test Node Description",
        node_type="concept",
        estimated_minutes=30,
        metadata_json={"difficulty": "easy"}
    )
    test_db.add(node)
    test_db.commit()
    test_db.refresh(node)
    
    # Assert creation worked
    assert node.id is not None
    assert node.title == "Test Node"
    assert node.path_id == path.id
    
    # Read
    retrieved_node = test_db.query(PathNode).filter(PathNode.id == node.id).first()
    assert retrieved_node is not None
    assert retrieved_node.title == "Test Node"
    
    # Update
    retrieved_node.title = "Updated Node"
    test_db.commit()
    
    # Verify update
    updated_node = test_db.query(PathNode).filter(PathNode.id == node.id).first()
    assert updated_node.title == "Updated Node"
    
    # Delete
    test_db.delete(retrieved_node)
    test_db.commit()
    
    # Verify deletion
    deleted_node = test_db.query(PathNode).filter(PathNode.id == node.id).first()
    assert deleted_node is None


def test_path_edge_crud(test_db):
    """Test CRUD operations for PathEdge model."""
    from uuid import UUID
    
    # Create a user and path first
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    # Create two nodes
    node1 = PathNode(
        path_id=path.id,
        title="Node 1",
        description="First Node",
        node_type="concept",
        estimated_minutes=30
    )
    node2 = PathNode(
        path_id=path.id,
        title="Node 2",
        description="Second Node",
        node_type="concept",
        estimated_minutes=45
    )
    test_db.add(node1)
    test_db.add(node2)
    test_db.commit()
    test_db.refresh(node1)
    test_db.refresh(node2)
    
    # Create an edge
    edge = PathEdge(
        path_id=path.id,
        from_node_id=node1.id,
        to_node_id=node2.id
    )
    test_db.add(edge)
    test_db.commit()
    test_db.refresh(edge)
    
    # Assert creation worked
    assert edge.id is not None
    assert edge.from_node_id == node1.id
    assert edge.to_node_id == node2.id
    assert edge.path_id == path.id
    
    # Read
    retrieved_edge = test_db.query(PathEdge).filter(PathEdge.id == edge.id).first()
    assert retrieved_edge is not None
    assert retrieved_edge.from_node_id == node1.id
    assert retrieved_edge.to_node_id == node2.id
    
    # Delete
    test_db.delete(retrieved_edge)
    test_db.commit()
    
    # Verify deletion
    deleted_edge = test_db.query(PathEdge).filter(PathEdge.id == edge.id).first()
    assert deleted_edge is None


def test_node_progress_crud(test_db):
    """Test CRUD operations for NodeProgress model."""
    from uuid import UUID
    
    # Create a user, path, and node first
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    node = PathNode(
        path_id=path.id,
        title="Test Node",
        description="Test Node Description",
        node_type="concept",
        estimated_minutes=30
    )
    test_db.add(node)
    test_db.commit()
    test_db.refresh(node)
    
    # Create node progress
    progress = NodeProgress(
        user_id=user_id,
        node_id=node.id,
        learning_path_id=path.id,
        status=NodeProgressStatus.NOT_STARTED,
        attempts_count=0,
        last_score=None
    )
    test_db.add(progress)
    test_db.commit()
    test_db.refresh(progress)
    
    # Assert creation worked
    assert progress.id is not None
    assert progress.user_id == user_id
    assert progress.node_id == node.id
    assert progress.status == NodeProgressStatus.NOT_STARTED
    
    # Read
    retrieved_progress = test_db.query(NodeProgress).filter(NodeProgress.id == progress.id).first()
    assert retrieved_progress is not None
    assert retrieved_progress.status == NodeProgressStatus.NOT_STARTED
    
    # Update progress
    retrieved_progress.status = NodeProgressStatus.IN_PROGRESS
    retrieved_progress.attempts_count = 1
    retrieved_progress.last_score = 0.75
    test_db.commit()
    
    # Verify update
    updated_progress = test_db.query(NodeProgress).filter(NodeProgress.id == progress.id).first()
    assert updated_progress.status == NodeProgressStatus.IN_PROGRESS
    assert updated_progress.attempts_count == 1
    assert updated_progress.last_score == 0.75
    
    # Delete
    test_db.delete(retrieved_progress)
    test_db.commit()
    
    # Verify deletion
    deleted_progress = test_db.query(NodeProgress).filter(NodeProgress.id == progress.id).first()
    assert deleted_progress is None


def test_relationships_consistency(test_db):
    """Test that relationships between models work correctly."""
    from uuid import UUID

    # Create a user, path, and nodes
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)

    node1 = PathNode(
        path_id=path.id,
        title="Node 1",
        description="First Node",
        node_type="concept",
        estimated_minutes=30
    )
    node2 = PathNode(
        path_id=path.id,
        title="Node 2",
        description="Second Node",
        node_type="concept",
        estimated_minutes=45
    )
    test_db.add(node1)
    test_db.add(node2)
    test_db.commit()
    test_db.refresh(node1)
    test_db.refresh(node2)

    # Create an edge connecting the nodes
    edge = PathEdge(
        path_id=path.id,
        from_node_id=node1.id,
        to_node_id=node2.id
    )
    test_db.add(edge)
    test_db.commit()
    test_db.refresh(edge)

    # Create progress for the user on node1
    progress = NodeProgress(
        user_id=user_id,
        node_id=node1.id,
        learning_path_id=path.id,
        status=NodeProgressStatus.IN_PROGRESS
    )
    test_db.add(progress)
    test_db.commit()

    # Test relationships by querying the database again to load relationships
    # Path should have nodes
    path_with_nodes = test_db.query(LearningPath).filter(LearningPath.id == path.id).first()
    assert len(path_with_nodes.nodes) >= 2
    node_titles = [n.title for n in path_with_nodes.nodes]
    assert "Node 1" in node_titles
    assert "Node 2" in node_titles

    # Path should have edges
    path_with_edges = test_db.query(LearningPath).filter(LearningPath.id == path.id).first()
    assert len(path_with_edges.edges) >= 1

    # Nodes should belong to path
    assert node1.path_id == path.id
    assert node2.path_id == path.id

    # Check that progress exists by querying directly
    progress_check = test_db.query(NodeProgress).filter(
        NodeProgress.node_id == node1.id,
        NodeProgress.user_id == user_id
    ).first()
    assert progress_check is not None
    assert progress_check.status == NodeProgressStatus.IN_PROGRESS

    # Progress should link user to node
    assert progress_check.user_id == user_id
    assert progress_check.node_id == node1.id


def test_challenge_crud(test_db):
    """Test CRUD operations for Challenge model."""
    from uuid import UUID
    
    # Create a user, path, and node first
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    node = PathNode(
        path_id=path.id,
        title="Test Node",
        description="Test Node Description",
        node_type="concept",
        estimated_minutes=30
    )
    test_db.add(node)
    test_db.commit()
    test_db.refresh(node)

    # Create a challenge
    challenge = Challenge(
        node_id=node.id,
        prompt="What is the main concept?",
        expected_answer_outline=json.dumps(["Answer 1", "Answer 2"]),
        rubric_json={"accuracy": "High", "completeness": "Medium"}
    )
    test_db.add(challenge)
    test_db.commit()
    test_db.refresh(challenge)
    
    # Assert creation worked
    assert challenge.id is not None
    assert challenge.node_id == node.id
    assert challenge.prompt == "What is the main concept?"
    
    # Read
    retrieved_challenge = test_db.query(Challenge).filter(Challenge.id == challenge.id).first()
    assert retrieved_challenge is not None
    assert retrieved_challenge.prompt == "What is the main concept?"
    
    # Update
    retrieved_challenge.prompt = "Updated question?"
    test_db.commit()
    
    # Verify update
    updated_challenge = test_db.query(Challenge).filter(Challenge.id == challenge.id).first()
    assert updated_challenge.prompt == "Updated question?"
    
    # Delete
    test_db.delete(retrieved_challenge)
    test_db.commit()
    
    # Verify deletion
    deleted_challenge = test_db.query(Challenge).filter(Challenge.id == challenge.id).first()
    assert deleted_challenge is None


def test_challenge_attempt_crud(test_db):
    """Test CRUD operations for ChallengeAttempt model."""
    from uuid import UUID
    
    # Create a user, path, node, and challenge first
    user_id = uuid4()
    path = LearningPath(
        user_id=user_id,
        goal_title="Test Path",
        goal_description="Test Description",
        domain_hint="Testing",
        level="beginner",
        summary="A test summary"
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    
    node = PathNode(
        path_id=path.id,
        title="Test Node",
        description="Test Node Description",
        node_type="concept",
        estimated_minutes=30
    )
    test_db.add(node)
    test_db.commit()
    test_db.refresh(node)
    
    challenge = Challenge(
        node_id=node.id,
        prompt="What is the main concept?",
        expected_answer_outline=json.dumps(["Answer 1", "Answer 2"]),
        rubric_json={"accuracy": "High", "completeness": "Medium"}
    )
    test_db.add(challenge)
    test_db.commit()
    test_db.refresh(challenge)
    
    # Create a challenge attempt
    attempt = ChallengeAttempt(
        challenge_id=challenge.id,
        user_id=user_id,
        submitted_answer="My answer to the challenge",
        score=0.8,
        feedback="Good answer with minor issues"
    )
    test_db.add(attempt)
    test_db.commit()
    test_db.refresh(attempt)
    
    # Assert creation worked
    assert attempt.id is not None
    assert attempt.challenge_id == challenge.id
    assert attempt.user_id == user_id
    assert attempt.submitted_answer == "My answer to the challenge"
    assert attempt.score == 0.8
    
    # Read
    retrieved_attempt = test_db.query(ChallengeAttempt).filter(ChallengeAttempt.id == attempt.id).first()
    assert retrieved_attempt is not None
    assert retrieved_attempt.submitted_answer == "My answer to the challenge"
    
    # Update
    retrieved_attempt.score = 0.9
    retrieved_attempt.feedback = "Excellent answer!"
    test_db.commit()
    
    # Verify update
    updated_attempt = test_db.query(ChallengeAttempt).filter(ChallengeAttempt.id == attempt.id).first()
    assert updated_attempt.score == 0.9
    assert updated_attempt.feedback == "Excellent answer!"
    
    # Delete
    test_db.delete(retrieved_attempt)
    test_db.commit()
    
    # Verify deletion
    deleted_attempt = test_db.query(ChallengeAttempt).filter(ChallengeAttempt.id == attempt.id).first()
    assert deleted_attempt is None
