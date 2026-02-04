"""
End-to-End tests that hit real APIs for internal testing.
These tests should only be run manually with real API credentials.
"""

import pytest
import os
from fastapi.testclient import TestClient
from main import app


# Skip these tests unless explicitly enabled
@pytest.mark.skipif(
    os.getenv("RUN_E2E_TESTS") != "true", 
    reason="End-to-end tests require real API access and RUN_E2E_TESTS=true"
)
class TestRealApiE2E:
    """End-to-end tests that hit real APIs for internal testing."""
    
    def test_full_learning_path_generation_with_real_gemini(self):
        """Test the complete flow with real Gemini API calls."""
        client = TestClient(app)
        
        # This will hit the real Gemini API to generate competencies and learning path
        response = client.post("/api/paths/", json={
            "goal_title": "Learn Python Basics",
            "goal_description": "Learn Python programming fundamentals",
            "domain_hint": "programming",
            "level": "beginner",
            "user_background": "No programming experience"
        })
        
        # Should succeed with real API calls
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
        assert data["goal_title"] == "Learn Python Basics"
        
        print(f"Generated path with {len(data['nodes'])} nodes and {len(data['edges'])} edges")
        
        # Verify the path can be retrieved
        path_id = data["id"]
        get_response = client.get(f"/api/paths/{path_id}")
        assert get_response.status_code == 200
        retrieved_path = get_response.json()
        assert retrieved_path["id"] == path_id
        assert len(retrieved_path["nodes"]) == len(data["nodes"])
        
    def test_learning_path_with_different_goals(self):
        """Test different learning goals with real API calls."""
        client = TestClient(app)
        
        test_cases = [
            {
                "goal_title": "JavaScript Fundamentals",
                "domain_hint": "web-development",
                "level": "beginner"
            },
            {
                "goal_title": "Machine Learning Basics",
                "domain_hint": "data-science",
                "level": "intermediate"
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                response = client.post("/api/paths/", json={
                    "goal_title": test_case["goal_title"],
                    "goal_description": f"Learn {test_case['goal_title'].lower()}",
                    "domain_hint": test_case["domain_hint"],
                    "level": test_case["level"],
                    "user_background": "Some technical background"
                })
                
                assert response.status_code == 200
                data = response.json()
                
                assert "id" in data
                assert len(data["nodes"]) > 0
                assert len(data["edges"]) >= 0  # May have no edges for single-node paths
                
                print(f"Successfully generated path for '{test_case['goal_title']}' with {len(data['nodes'])} nodes")
    
    def test_path_list_and_retrieval(self):
        """Test creating multiple paths and retrieving them."""
        client = TestClient(app)
        
        # Create first path
        response1 = client.post("/api/paths/", json={
            "goal_title": "Python E2E Test 1",
            "goal_description": "First end-to-end test path",
            "domain_hint": "testing",
            "level": "beginner",
            "user_background": "Internal testing"
        })
        assert response1.status_code == 200
        path1 = response1.json()
        
        # Create second path
        response2 = client.post("/api/paths/", json={
            "goal_title": "Python E2E Test 2",
            "goal_description": "Second end-to-end test path",
            "domain_hint": "testing",
            "level": "intermediate",
            "user_background": "Internal testing"
        })
        assert response2.status_code == 200
        path2 = response2.json()
        
        # Verify both paths were created with different content
        assert path1["id"] != path2["id"]
        assert path1["goal_title"] != path2["goal_title"]
        
        # Retrieve individual paths
        get_response1 = client.get(f"/api/paths/{path1['id']}")
        assert get_response1.status_code == 200
        retrieved_path1 = get_response1.json()
        assert retrieved_path1["id"] == path1["id"]
        
        get_response2 = client.get(f"/api/paths/{path2['id']}")
        assert get_response2.status_code == 200
        retrieved_path2 = get_response2.json()
        assert retrieved_path2["id"] == path2["id"]
        
        print(f"Created and verified two different learning paths: {path1['id']} and {path2['id']}")


# Example of how to run these tests:
"""
To run these end-to-end tests with real APIs:

1. Set up your environment with real API keys:
export GOOGLE_API_KEY=your_actual_api_key
export GEMINI_MODEL=gemini-pro
export DATABASE_URL=your_db_url
export RUN_E2E_TESTS=true

2. Run the tests:
python -m pytest tests/e2e/ -v

3. Or run specific tests:
python -m pytest tests/e2e/ -k "real_gemini" -v
"""


if __name__ == "__main__":
    # This allows running the tests directly if needed
    pytest.main([__file__, "-v"])