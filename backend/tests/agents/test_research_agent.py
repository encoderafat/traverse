import pytest
from unittest.mock import patch, MagicMock
from agents.research_agent import run_research_agent, eval_research_quality


class TestResearchAgent:
    """Unit tests for the research agent."""

    @patch('agents.research_agent.opik_tracer')
    @patch('agents.research_agent.call_gemini')
    @patch('agents.research_agent.google_web_search')
    @patch('agents.research_agent.web_fetch')
    def test_run_research_agent_success(self, mock_web_fetch, mock_google_web_search, mock_call_gemini, mock_opik_tracer):
        """Test successful execution of the research agent."""
        # Mock the web search results
        mock_google_web_search.return_value = {
            "results": [
                {"link": "https://example.com/article1", "title": "Article 1"},
                {"link": "https://example.com/article2", "title": "Article 2"}
            ]
        }
        
        # Mock the web fetch results
        mock_web_fetch.return_value = "Sample content from the webpage"
        
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "normalized_goal": "Learn Python Programming",
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
        '''

        result = run_research_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            goal_description="Learn Python programming from scratch",
            domain_hint="programming",
            level="beginner"
        )

        # Assertions
        assert "competencies" in result
        assert "research_context" in result
        assert isinstance(result["competencies"], dict)
        assert len(result["competencies"]["competencies"]) > 0
        
        # Verify that the mocks were called
        mock_google_web_search.assert_called()
        mock_web_fetch.assert_called()
        mock_call_gemini.assert_called()

    @patch('agents.research_agent.opik_tracer')
    @patch('agents.research_agent.call_gemini')
    @patch('agents.research_agent.google_web_search')
    def test_run_research_agent_no_content_found(self, mock_google_web_search, mock_call_gemini, mock_opik_tracer):
        """Test research agent when no content is found."""
        # Mock empty search results
        mock_google_web_search.return_value = {"results": []}
        
        # Mock the LLM response
        mock_call_gemini.return_value = '''
        {
          "normalized_goal": "Learn Python Programming",
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
        '''

        result = run_research_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            goal_description="Learn Python programming from scratch",
            domain_hint="programming",
            level="beginner"
        )

        # Should still work even without external content
        assert "competencies" in result
        assert "research_context" in result

    @patch('agents.research_agent.opik_tracer')
    @patch('agents.research_agent.call_gemini')
    def test_run_research_agent_json_parsing_error(self, mock_call_gemini, mock_opik_tracer):
        """Test research agent when LLM returns invalid JSON."""
        # Mock invalid JSON response
        mock_call_gemini.return_value = "Invalid JSON response from LLM"

        result = run_research_agent(
            user_id="test-user-id",
            goal_title="Learn Python",
            goal_description="Learn Python programming from scratch",
            domain_hint="programming",
            level="beginner"
        )

        # Should handle JSON parsing errors gracefully
        assert "competencies" in result
        assert "research_context" in result
        assert result["competencies"]["error"] == "invalid_json_from_model"

    def test_eval_research_quality(self):
        """Test the research quality evaluation function."""
        goal_title = "Learn Python"
        competencies_json = {
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

        score, details = eval_research_quality(goal_title, competencies_json)

        # Should return a numeric score and details
        assert isinstance(score, (int, float))
        assert isinstance(details, dict)
        assert 0.0 <= score <= 1.0