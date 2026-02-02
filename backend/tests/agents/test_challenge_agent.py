import pytest
from unittest.mock import patch, MagicMock
from backend.agents.challenge_agent import run_challenge_agent, eval_challenge_quality


class TestChallengeAgent:
    """Unit tests for the challenge agent."""

    @patch('backend.agents.challenge_agent.opik_tracer')
    @patch('backend.agents.challenge_agent.call_gemini')
    def test_run_challenge_agent_success(self, mock_call_gemini, mock_opik_tracer):
        """Test successful execution of the challenge agent."""
        # Mock the LLM response with valid JSON
        mock_call_gemini.return_value = '''
        {
          "challenge_type": "comprehension_test",
          "prompt": "Explain the concept of variables in Python",
          "expected_answer_outline": [
            "Variables store data values",
            "Python has dynamic typing",
            "Variable names follow specific rules"
          ],
          "rubric": {
            "dimensions": [
              { "name": "Relevance", "description": "How relevant is the answer" },
              { "name": "Correctness", "description": "How correct is the answer" }
            ],
            "scoring_scale": "0-5"
          },
          "difficulty": "medium"
        }
        '''

        node = {
            "id": "n1",
            "title": "Variables in Python",
            "description": "Understanding variables in Python",
            "node_type": "concept"
        }

        research_context = [
            {
                "url": "https://example.com/article",
                "content": "Python variables are used to store data values..."
            }
        ]

        result = run_challenge_agent(
            user_id="test-user-id",
            path_id=1,
            node=node,
            domain_hint="programming",
            research_context=research_context
        )

        # Assertions
        assert "challenge_type" in result
        assert "prompt" in result
        assert "expected_answer_outline" in result
        assert "rubric" in result
        assert "difficulty" in result
        assert result["challenge_type"] == "comprehension_test"
        
        # Verify that the mock was called
        mock_call_gemini.assert_called()

    @patch('backend.agents.challenge_agent.opik_tracer')
    @patch('backend.agents.challenge_agent.call_gemini')
    def test_run_challenge_agent_without_research_context(self, mock_call_gemini, mock_opik_tracer):
        """Test challenge agent without research context."""
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "challenge_type": "comprehension_test",
          "prompt": "Explain the concept of variables in Python",
          "expected_answer_outline": [
            "Variables store data values",
            "Python has dynamic typing"
          ],
          "rubric": {
            "dimensions": [
              { "name": "Relevance", "description": "How relevant is the answer" }
            ],
            "scoring_scale": "0-5"
          },
          "difficulty": "easy"
        }
        '''

        node = {
            "id": "n1",
            "title": "Variables in Python",
            "description": "Understanding variables in Python",
            "node_type": "concept"
        }

        result = run_challenge_agent(
            user_id="test-user-id",
            path_id=1,
            node=node,
            domain_hint="programming",
            research_context=None
        )

        # Should work even without research context
        assert "challenge_type" in result
        assert "prompt" in result

    @patch('backend.agents.challenge_agent.opik_tracer')
    @patch('backend.agents.challenge_agent.call_gemini')
    def test_run_challenge_agent_json_parsing_error(self, mock_call_gemini, mock_opik_tracer):
        """Test challenge agent when LLM returns invalid JSON."""
        # Mock invalid JSON response
        mock_call_gemini.return_value = "Invalid JSON response from LLM"

        node = {
            "id": "n1",
            "title": "Variables in Python",
            "description": "Understanding variables in Python",
            "node_type": "concept"
        }

        result = run_challenge_agent(
            user_id="test-user-id",
            path_id=1,
            node=node,
            domain_hint="programming",
            research_context=[]
        )

        # Should handle JSON parsing errors gracefully
        assert "error" in result
        assert result["error"] == "invalid_json_from_model"

    def test_eval_challenge_quality(self):
        """Test the challenge quality evaluation function."""
        node = {
            "id": "n1",
            "title": "Variables in Python",
            "description": "Understanding variables in Python",
            "node_type": "concept"
        }
        
        challenge_json = {
            "challenge_type": "comprehension_test",
            "prompt": "Explain the concept of variables in Python",
            "expected_answer_outline": [
                "Variables store data values",
                "Python has dynamic typing"
            ],
            "rubric": {
                "dimensions": [
                    { "name": "Relevance", "description": "How relevant is the answer" }
                ],
                "scoring_scale": "0-5"
            },
            "difficulty": "easy"
        }

        score, details = eval_challenge_quality(node, challenge_json)

        # Should return a numeric score and details
        assert isinstance(score, (int, float))
        assert isinstance(details, dict)
        assert 0.0 <= score <= 1.0

    @patch('backend.agents.challenge_agent.opik_tracer')
    @patch('backend.agents.challenge_agent.call_gemini')
    def test_run_challenge_agent_with_minimal_node_info(self, mock_call_gemini, mock_opik_tracer):
        """Test challenge agent with minimal node information."""
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "challenge_type": "comprehension_test",
          "prompt": "Explain the concept of variables in Python",
          "expected_answer_outline": [],
          "rubric": {},
          "difficulty": null
        }
        '''

        # Minimal node info
        node = {
            "id": "n1",
            "title": "Variables"
        }

        result = run_challenge_agent(
            user_id="test-user-id",
            path_id=1,
            node=node,
            domain_hint=None,  # No domain hint
            research_context=None
        )

        # Should handle minimal information
        assert "challenge_type" in result