"""
DeadlineOS — Digital Twin Agent Unit Tests
"""

import unittest
from unittest.mock import MagicMock

from agents.digital_twin_agent import DigitalTwinAgent


class TestDigitalTwinAgent(unittest.TestCase):
    def setUp(self):
        """Set up a mocked GeminiService and initialize DigitalTwinAgent."""
        self.mock_gemini = MagicMock()
        self.agent = DigitalTwinAgent(self.mock_gemini)

    def test_simulate_scenario_empty(self):
        """Verify baseline behavior when no tasks or scenario are provided."""
        result = self.agent.simulate_scenario([], {}, {})
        self.assertEqual(result["future_risk"], "Low")
        self.assertEqual(result["stress_score"], 0)
        self.assertEqual(result["productivity_score"], 100)
        self.assertEqual(result["predicted_deadline_failures"], 0)
        self.mock_gemini.generate_structured.assert_not_called()

    def test_simulate_scenario_structure(self):
        """Verify the agent correctly formats the prompt and returns structured data."""
        # Setup mock return value based on requirements
        mock_response = {
            "future_risk": "High",
            "stress_score": 82,
            "productivity_score": 64,
            "predicted_deadline_failures": 2,
            "predicted_conflicts": [
                {
                    "task": "Interview Preparation",
                    "reason": "Schedule overlap"
                }
            ],
            "workload_change_percentage": 35,
            "simulation_summary": "Delaying React Assignment by 2 days creates schedule conflicts.",
            "recommendation": "Do not delay the assignment.",
            "alternative_plan": [
                {"action": "Increase daily work hours by 2"}
            ]
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
        
        scenario = {
            "action": "delay_task",
            "task": "React Assignment",
            "delay_days": 2
        }
        
        availability = {
            "daily_available_hours": 4
        }

        # Execute
        result = self.agent.simulate_scenario(tasks, scenario, availability)

        # Assertions
        self.assertEqual(result["future_risk"], "High")
        self.assertEqual(result["stress_score"], 82)
        self.assertEqual(result["predicted_deadline_failures"], 2)
        self.assertEqual(len(result["predicted_conflicts"]), 1)
        self.assertEqual(result["predicted_conflicts"][0]["task"], "Interview Preparation")

        # Verify GeminiService was called with the correct parameters
        self.mock_gemini.generate_structured.assert_called_once()
        call_kwargs = self.mock_gemini.generate_structured.call_args.kwargs
        
        # Verify prompts
        self.assertIn("predictive productivity strategist", call_kwargs["system_prompt"])
        self.assertIn("React Assignment", call_kwargs["user_prompt"])
        self.assertIn("delay_task", call_kwargs["user_prompt"])
        self.assertIn("4", call_kwargs["user_prompt"]) # daily hours
        
        # Verify schema presence
        self.assertEqual(call_kwargs["schema"]["type"], "object")
        self.assertIn("future_risk", call_kwargs["schema"]["required"])
        self.assertIn("stress_score", call_kwargs["schema"]["required"])


if __name__ == "__main__":
    unittest.main()
