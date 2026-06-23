"""
DeadlineOS — Rescue Agent Unit Tests
"""

import unittest
from unittest.mock import MagicMock

from agents.rescue_agent import RescueAgent


class TestRescueAgent(unittest.TestCase):
    def setUp(self):
        """Set up a mocked GeminiService and initialize RescueAgent."""
        self.mock_gemini = MagicMock()
        self.agent = RescueAgent(self.mock_gemini)

    def test_generate_recovery_plan_empty_tasks(self):
        """Verify behavior when no tasks are provided."""
        result = self.agent.generate_recovery_plan([], {})
        self.assertFalse(result["risk_detected"])
        self.assertEqual(result["success_probability"], 100)
        self.mock_gemini.generate_structured.assert_not_called()

    def test_generate_recovery_plan_structure(self):
        """Verify the agent correctly formats the prompt and returns structured data."""
        # Setup mock return value based on requirements
        mock_response = {
            "risk_detected": True,
            "risk_level": "High",
            "success_probability": 42,
            "recovery_plan": [
                {"action": "Increase study time by 2 hours"},
                {"action": "Postpone low-priority tasks"}
            ],
            "recommended_schedule_adjustments": [
                {
                    "task": "React Assignment",
                    "new_time_block": "18:00-21:00"
                }
            ],
            "reasoning": "Current pace is insufficient to meet the deadline."
        }
        self.mock_gemini.generate_structured.return_value = mock_response

        # Input data
        tasks = [
            {
                "title": "React Assignment",
                "deadline": "2026-06-25T18:00:00",
                "estimated_hours": 8,
                "completed_hours": 2,
                "priority_score": 92
            }
        ]
        
        availability = {
            "daily_available_hours": 3
        }

        # Execute
        result = self.agent.generate_recovery_plan(tasks, availability)

        # Assertions
        self.assertTrue(result["risk_detected"])
        self.assertEqual(result["risk_level"], "High")
        self.assertEqual(result["success_probability"], 42)
        self.assertEqual(len(result["recovery_plan"]), 2)
        self.assertEqual(result["recommended_schedule_adjustments"][0]["task"], "React Assignment")

        # Verify GeminiService was called with the correct parameters
        self.mock_gemini.generate_structured.assert_called_once()
        call_kwargs = self.mock_gemini.generate_structured.call_args.kwargs
        
        # Verify prompts
        self.assertIn("emergency productivity strategist", call_kwargs["system_prompt"])
        self.assertIn("React Assignment", call_kwargs["user_prompt"])
        self.assertIn("daily_available_hours", call_kwargs["user_prompt"])
        
        # Verify schema presence
        self.assertEqual(call_kwargs["schema"]["type"], "object")
        self.assertIn("recovery_plan", call_kwargs["schema"]["required"])


if __name__ == "__main__":
    unittest.main()
