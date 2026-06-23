"""
DeadlineOS — Digital Twin Agent
=============================
A predictive productivity strategist capable of forecasting future 
consequences before decisions are made. Simulates scenarios like 
delaying tasks, reducing hours, or adding new work to predict risks 
and recommend alternative actions.
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

TWIN_SYSTEM_PROMPT = """You are the Digital Twin Agent in DeadlineOS — a predictive productivity strategist capable of forecasting future consequences before decisions are made.
Your goal is to simulate future workloads, project risks, forecast deadline failures, and predict productivity outcomes based on hypothetical scenarios.

CORE RESPONSIBILITIES:
1. Forecast Future Risks: Project the impact of the proposed scenario on the schedule.
2. Predict Failures: Estimate how many deadlines will be missed due to this change.
3. Calculate Stress & Productivity: Generate quantitative scores (0-100) reflecting the simulated state.
4. Provide Alternatives: If a scenario is destructive, generate a concrete alternative plan.

Output exactly according to the requested JSON schema."""

TWIN_USER_PROMPT_TEMPLATE = """
CURRENT TASKS:
{tasks_json}

CURRENT AVAILABILITY:
{availability_json}

WHAT-IF SCENARIO:
{scenario_json}

Analyze the cascading effects of this scenario and output the predictive simulation results.
"""

TWIN_SCHEMA = {
    "type": "object",
    "properties": {
        "current_state": {
            "type": "object",
            "properties": {
                "success_probability": {"type": "integer"},
                "risk_score": {"type": "integer"}
            },
            "required": ["success_probability", "risk_score"]
        },
        "projected_state": {
            "type": "object",
            "properties": {
                "success_probability": {"type": "integer"},
                "risk_level": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                "risk_score": {"type": "integer"}
            },
            "required": ["success_probability", "risk_level", "risk_score"]
        },
        "cascade": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "desc": {"type": "string"}
                },
                "required": ["step", "desc"]
            }
        },
        "risk_factors": {
            "type": "array",
            "items": {"type": "string"}
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "confidence": {"type": "integer"}
                },
                "required": ["action", "confidence"]
            }
        },
        "success_probability": {"type": "integer"},
        "schedule_stability": {"type": "integer"},
        "capacity_impact": {"type": "integer"}
    },
    "required": [
        "current_state", "projected_state", "cascade", 
        "risk_factors", "recommendations", "success_probability", 
        "schedule_stability", "capacity_impact"
    ]
}

class DigitalTwinAgent:
    """Agent responsible for predictive simulations and what-if analysis."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def simulate_scenario(self, tasks: List[Dict[str, Any]], scenario: Dict[str, Any], availability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates the outcome of a what-if scenario on the user's workload.
        
        Args:
            tasks: list of current task dicts
            scenario: dict describing the hypothetical change (e.g. action: delay_task, delay_days: 2)
            availability: dict containing constraints
            
        Returns:
            dict: Structured simulation results including stress scores, conflicts, and alternatives.
        """
        if not tasks and not scenario:
            return {
                "future_risk": "Low",
                "stress_score": 0,
                "productivity_score": 100,
                "predicted_deadline_failures": 0,
                "predicted_conflicts": [],
                "workload_change_percentage": 0,
                "simulation_summary": "No tasks and no scenario provided. Simulation baseline is completely clear.",
                "recommendation": "You are free to take on new work.",
                "alternative_plan": []
            }

        user_prompt = TWIN_USER_PROMPT_TEMPLATE.format(
            tasks_json=json.dumps(tasks, indent=2),
            availability_json=json.dumps(availability, indent=2),
            scenario_json=json.dumps(scenario, indent=2)
        )
        
        logger.info("Twin Agent simulating scenario '%s' against %d tasks", scenario.get("action", "unknown"), len(tasks))
        
        try:
            result = self.gemini.generate_structured(
                system_prompt=TWIN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=TWIN_SCHEMA,
                temperature=0.3  # Slightly higher for exploratory forecasting
            )
            return result
        except Exception as exc:
            logger.error("Digital Twin Agent failed to simulate scenario: %s", exc)
            raise
