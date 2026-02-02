import pytest
from unittest.mock import patch, MagicMock
from backend.agents.dag_builder_agent import run_dag_builder_agent, eval_dag_quality


class TestDagBuilderAgent:
    """Unit tests for the DAG builder agent."""

    @patch('backend.agents.dag_builder_agent.opik_tracer')
    @patch('backend.agents.dag_builder_agent.call_gemini')
    def test_run_dag_builder_agent_success(self, mock_call_gemini, mock_opik_tracer):
        """Test successful execution of the DAG builder agent."""
        # Mock the LLM response with valid JSON
        mock_call_gemini.return_value = '''
        {
          "summary": "A comprehensive learning path for Python",
          "nodes": [
            {
              "id": "n1",
              "title": "Basic Concepts",
              "description": "Learn basic Python concepts",
              "node_type": "concept",
              "estimated_minutes": 30,
              "tags": ["basics", "fundamentals"]
            }
          ],
          "edges": [
            { "from": "n1", "to": "n2" }
          ]
        }
        '''

        competencies = {
            "normalized_goal": "Learn Python",
            "competencies": [
                {
                    "id": "c1",
                    "name": "Basic Syntax",
                    "description": "Understanding Python syntax",
                    "type": "technical",
                    "example_tasks": ["Write a simple program", "Use variables"]
                }
            ]
        }

        result = run_dag_builder_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            competencies=competencies,
            user_background="Programming beginner"
        )

        # Assertions
        assert "summary" in result
        assert "nodes" in result
        assert "edges" in result
        assert result["summary"] == "A comprehensive learning path for Python"
        assert len(result["nodes"]) > 0
        
        # Verify that the mock was called
        mock_call_gemini.assert_called()

    @patch('backend.agents.dag_builder_agent.opik_tracer')
    @patch('backend.agents.dag_builder_agent.call_gemini')
    def test_run_dag_builder_agent_json_parsing_error(self, mock_call_gemini, mock_opik_tracer):
        """Test DAG builder agent when LLM returns invalid JSON."""
        # Mock invalid JSON response
        mock_call_gemini.return_value = "Invalid JSON response from LLM"

        competencies = {
            "normalized_goal": "Learn Python",
            "competencies": [
                {
                    "id": "c1",
                    "name": "Basic Syntax",
                    "description": "Understanding Python syntax",
                    "type": "technical",
                    "example_tasks": ["Write a simple program", "Use variables"]
                }
            ]
        }

        result = run_dag_builder_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            competencies=competencies,
            user_background="Programming beginner"
        )

        # Should handle JSON parsing errors gracefully
        assert "summary" in result
        assert "nodes" in result
        assert "edges" in result
        assert result["nodes"] == []
        assert result["edges"] == []

    def test_eval_dag_quality(self):
        """Test the DAG quality evaluation function."""
        goal_title = "Learn Python"
        dag_json = {
            "summary": "A comprehensive learning path for Python",
            "nodes": [
                {
                    "id": "n1",
                    "title": "Basic Concepts",
                    "description": "Learn basic Python concepts",
                    "node_type": "concept",
                    "estimated_minutes": 30,
                    "tags": ["basics", "fundamentals"]
                }
            ],
            "edges": [
                { "from": "n1", "to": "n2" }
            ]
        }

        score, details = eval_dag_quality(goal_title, dag_json)

        # Should return a numeric score and details
        assert isinstance(score, (int, float))
        assert isinstance(details, dict)
        assert 0.0 <= score <= 1.0

    @patch('backend.agents.dag_builder_agent.opik_tracer')
    @patch('backend.agents.dag_builder_agent.call_gemini')
    def test_run_dag_builder_agent_with_empty_competencies(self, mock_call_gemini, mock_opik_tracer):
        """Test DAG builder agent with empty competencies."""
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "summary": "An empty learning path",
          "nodes": [],
          "edges": []
        }
        '''

        competencies = {
            "normalized_goal": "Learn Python",
            "competencies": []
        }

        result = run_dag_builder_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            competencies=competencies,
            user_background="Programming beginner"
        )

        # Should handle empty competencies
        assert "summary" in result
        assert "nodes" in result
        assert "edges" in result