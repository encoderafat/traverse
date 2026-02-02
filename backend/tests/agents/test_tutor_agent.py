import pytest
from unittest.mock import patch, MagicMock
from backend.agents.tutor_agent import run_tutor_agent, run_hint_agent, eval_tutor_feedback


class TestTutorAgent:
    """Unit tests for the tutor agent."""

    @patch('backend.agents.tutor_agent.opik_tracer')
    @patch('backend.agents.tutor_agent.call_gemini')
    def test_run_tutor_agent_success(self, mock_call_gemini, mock_opik_tracer):
        """Test successful execution of the tutor agent."""
        # Mock the LLM response with valid JSON
        mock_call_gemini.return_value = '''
        {
          "dimension_scores": [
            { "name": "Relevance", "score": 4, "comment": "Good relevance" }
          ],
          "overall_score": 0.8,
          "pass": true,
          "feedback_summary": "Good answer with minor issues",
          "suggestions": [
            "Consider adding more examples",
            "Elaborate on the main point"
          ],
          "adaptation_suggestion": null
        }
        '''

        challenge = {
            "id": 1,
            "prompt": "Explain variables in Python",
            "expected_answer_outline": ["Variables store data", "Dynamic typing"],
            "rubric": {
                "dimensions": [
                    {"name": "Relevance", "description": "How relevant is the answer"}
                ],
                "scoring_scale": "0-5"
            }
        }

        result = run_tutor_agent(
            user_id="test-user-id",
            challenge=challenge,
            user_answer="Variables in Python store data values and have dynamic typing",
            attempts_count=1
        )

        # Assertions
        assert "overall_score" in result
        assert "pass" in result
        assert "feedback_summary" in result
        assert "suggestions" in result
        assert result["overall_score"] == 0.8
        assert result["pass"] is True
        
        # Verify that the mock was called
        mock_call_gemini.assert_called()

    @patch('backend.agents.tutor_agent.opik_tracer')
    @patch('backend.agents.tutor_agent.call_gemini')
    def test_run_tutor_agent_json_parsing_error(self, mock_call_gemini, mock_opik_tracer):
        """Test tutor agent when LLM returns invalid JSON."""
        # Mock invalid JSON response
        mock_call_gemini.return_value = "Invalid JSON response from LLM"

        challenge = {
            "id": 1,
            "prompt": "Explain variables in Python",
            "expected_answer_outline": ["Variables store data", "Dynamic typing"],
            "rubric": {
                "dimensions": [
                    {"name": "Relevance", "description": "How relevant is the answer"}
                ],
                "scoring_scale": "0-5"
            }
        }

        result = run_tutor_agent(
            user_id="test-user-id",
            challenge=challenge,
            user_answer="Variables in Python store data values and have dynamic typing",
            attempts_count=1
        )

        # Should handle JSON parsing errors gracefully
        assert "overall_score" in result
        assert "pass" in result
        assert result["pass"] is False
        assert "Could not parse grading" in result["feedback_summary"]

    @patch('backend.agents.tutor_agent.opik_tracer')
    @patch('backend.agents.tutor_agent.call_gemini')
    def test_run_tutor_agent_high_attempts_blocked(self, mock_call_gemini, mock_opik_tracer):
        """Test tutor agent behavior with high attempts count (should suggest adaptation)."""
        # Mock the LLM response with adaptation suggestion
        mock_call_gemini.return_value = '''
        {
          "dimension_scores": [
            { "name": "Relevance", "score": 2, "comment": "Low relevance" }
          ],
          "overall_score": 0.4,
          "pass": false,
          "feedback_summary": "Needs improvement",
          "suggestions": [
            "Review the basics"
          ],
          "adaptation_suggestion": "The basics of variable assignment in Python"
        }
        '''

        challenge = {
            "id": 1,
            "prompt": "Explain variables in Python",
            "expected_answer_outline": ["Variables store data", "Dynamic typing"],
            "rubric": {
                "dimensions": [
                    {"name": "Relevance", "description": "How relevant is the answer"}
                ],
                "scoring_scale": "0-5"
            }
        }

        result = run_tutor_agent(
            user_id="test-user-id",
            challenge=challenge,
            user_answer="Wrong answer",
            attempts_count=3  # High attempts count
        )

        # Should include adaptation suggestion for high attempts
        assert "adaptation_suggestion" in result
        assert result["adaptation_suggestion"] is not None

    def test_eval_tutor_feedback(self):
        """Test the tutor feedback evaluation function."""
        challenge = {
            "id": 1,
            "prompt": "Explain variables in Python",
            "expected_answer_outline": ["Variables store data", "Dynamic typing"],
            "rubric": {
                "dimensions": [
                    {"name": "Relevance", "description": "How relevant is the answer"}
                ],
                "scoring_scale": "0-5"
            }
        }
        
        user_answer = "Variables in Python store data values"
        
        tutor_output = {
            "dimension_scores": [
                {"name": "Relevance", "score": 4, "comment": "Good relevance"}
            ],
            "overall_score": 0.8,
            "pass": True,
            "feedback_summary": "Good answer",
            "suggestions": ["Consider adding more examples"]
        }

        score, details = eval_tutor_feedback(challenge, user_answer, tutor_output)

        # Should return a numeric score and details
        assert isinstance(score, (int, float))
        assert isinstance(details, dict)
        assert 0.0 <= score <= 1.0

    @patch('backend.agents.tutor_agent.opik_tracer')
    @patch('backend.agents.tutor_agent.call_gemini')
    def test_run_hint_agent(self, mock_call_gemini, mock_opik_tracer):
        """Test the hint agent function."""
        # Mock the LLM response for hint
        mock_call_gemini.return_value = "Consider thinking about what variables represent in programming"

        hint_text = run_hint_agent(
            challenge_prompt="Explain variables in Python",
            hint_level=1,
            user_id="test-user-id"
        )

        # Should return a hint string
        assert isinstance(hint_text, str)
        assert len(hint_text) > 0
        
        # Verify that the mock was called
        mock_call_gemini.assert_called()

    @patch('backend.agents.tutor_agent.opik_tracer')
    @patch('backend.agents.tutor_agent.call_gemini')
    def test_run_tutor_agent_with_prior_attempts(self, mock_call_gemini, mock_opik_tracer):
        """Test tutor agent with prior attempts summary."""
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "dimension_scores": [
            { "name": "Relevance", "score": 3, "comment": "Moderate relevance" }
          ],
          "overall_score": 0.6,
          "pass": false,
          "feedback_summary": "Some improvement needed",
          "suggestions": [
            "Focus on the key concepts"
          ],
          "adaptation_suggestion": null
        }
        '''

        challenge = {
            "id": 1,
            "prompt": "Explain variables in Python",
            "expected_answer_outline": ["Variables store data", "Dynamic typing"],
            "rubric": {
                "dimensions": [
                    {"name": "Relevance", "description": "How relevant is the answer"}
                ],
                "scoring_scale": "0-5"
            }
        }

        result = run_tutor_agent(
            user_id="test-user-id",
            challenge=challenge,
            user_answer="Partially correct answer",
            attempts_count=2,
            prior_attempts_summary="Previous attempts showed confusion about dynamic typing"
        )

        # Should work with prior attempts summary
        assert "overall_score" in result
        assert result["overall_score"] == 0.6