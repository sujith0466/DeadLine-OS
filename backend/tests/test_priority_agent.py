"""
DeadlineOS — Priority Agent Unit Tests
"""

import unittest
from unittest.mock import MagicMock

from agents.priority_agent import PriorityAgent


class TestPriorityAgent(unittest.TestCase):
    def setUp(self):
        """Set up a mocked GeminiService and initialize PriorityAgent."""
        self.mock_gemini = MagicMock()
        self.agent = PriorityAgent(self.mock_gemini)

    def test_analyze_task_structure(self):
        """Verify the agent correctly formats the prompt and returns structured data."""
        # Setup mock return value based on requirements
        mock_response = {
            "priority_score": 92,
            "urgency": "High",
            "importance": "High",
            "estimated_hours": 4.0,
            "risk_level": "Medium",
            "reasoning": "Deadline is near and workload is significant."
        }
        self.mock_gemini.generate_structured.return_value = mock_response

        # Input data
        task_data = {
            "title": "React Assignment",
            "description": "Build a dashboard using React",
            "deadline": "2026-06-25T18:00:00",
            "estimated_hours": 4
        }

        # Execute
        result = self.agent.analyze_task(task_data, active_tasks_count=5)

        # Assertions
        self.assertEqual(result["priority_score"], 92)
        self.assertEqual(result["urgency"], "High")
        self.assertEqual(result["importance"], "High")
        self.assertEqual(result["risk_level"], "Medium")

        # Verify GeminiService was called with the correct parameters
        self.mock_gemini.generate_structured.assert_called_once()
        call_kwargs = self.mock_gemini.generate_structured.call_args.kwargs
        
        # Verify prompts
        self.assertIn("Eisenhower Matrix", call_kwargs["system_prompt"])
        self.assertIn("React Assignment", call_kwargs["user_prompt"])
        self.assertIn("5 tasks pending", call_kwargs["user_prompt"])
        
        # Verify schema presence
        self.assertEqual(call_kwargs["schema"]["type"], "object")
        self.assertIn("priority_score", call_kwargs["schema"]["required"])


if __name__ == "__main__":
    unittest.main()
