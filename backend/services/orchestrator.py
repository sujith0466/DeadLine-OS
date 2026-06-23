"""
DeadlineOS — Agent Orchestration Service
========================================
Manages the execution flow of the multi-agent system.
Responsible for chaining agent inputs/outputs and maintaining the event bus.
"""

import logging
import datetime
from typing import Dict, Any, List

from agents.vision_agent import VisionAgent
from agents.priority_agent import PriorityAgent
from agents.planning_agent import PlanningAgent
from agents.rescue_agent import RescueAgent
from agents.digital_twin_agent import DigitalTwinAgent
from agents.accountability_agent import AccountabilityAgent
from agents.coach_agent import CoachAgent
from agents.reflection_agent import ReflectionAgent
from api.agents import _set_agent_state  # Direct state update for simplicity

logger = logging.getLogger(__name__)

class OrchestratorService:
    """Coordinates multi-agent workflows and maintains the global activity feed."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
        self.vision = VisionAgent(gemini_service)
        self.priority = PriorityAgent(gemini_service)
        self.planning = PlanningAgent(gemini_service)
        self.rescue = RescueAgent(gemini_service)
        self.twin = DigitalTwinAgent(gemini_service)
        self.accountability = AccountabilityAgent(gemini_service)
        self.coach = CoachAgent(gemini_service)
        self.reflection = ReflectionAgent(gemini_service)

    @classmethod
    def add_event(cls, agent: str, action: str, status: str, payload: Any = None):
        """Append an event to the global event bus."""
        from models.telemetry import OrchestratorEvent
        from database.db import db
        
        event = OrchestratorEvent(
            agent=agent,
            action=action,
            status=status,
            payload=payload
        )
        try:
            db.session.add(event)
            db.session.commit()
            
            # Prune old events to prevent bloat
            count = OrchestratorEvent.query.count()
            if count > 500:
                oldest = OrchestratorEvent.query.order_by(OrchestratorEvent.timestamp.asc()).first()
                db.session.delete(oldest)
                db.session.commit()
        except Exception as e:
            logger.error("Failed to save OrchestratorEvent: %s", e)

    @classmethod
    def get_feed(cls) -> List[Dict[str, Any]]:
        """Return the event feed, newest first."""
        from models.telemetry import OrchestratorEvent
        events = OrchestratorEvent.query.order_by(OrchestratorEvent.timestamp.desc()).limit(100).all()
        return [e.to_dict() for e in events]

    def run_pipeline(self, image_bytes: bytes, mime_type: str, availability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the full pipeline:
        Vision -> Priority -> Planning -> Accountability -> Coach -> Rescue -> Twin -> Reflection
        """
        trace = []
        
        def _log(agent, action, status, data=None):
            self.add_event(agent, action, status, data)
            trace.append({"agent": agent, "action": action, "status": status, "data": data})

        from services.telemetry_service import TelemetryService
        import time

        logger.info("Starting Orchestrator Pipeline...")
        
        # 1. Vision Agent
        _set_agent_state("vision", "running")
        _log("Vision Agent", "Extracting tasks from image", "running")
        t0 = time.time()
        vision_result = self.vision.extract_tasks_from_image(image_bytes, mime_type)
        extracted_tasks = vision_result.get("tasks", [])
        _log("Vision Agent", f"Extracted {len(extracted_tasks)} tasks", "success", vision_result)
        TelemetryService.log_execution("Vision Agent", "Image Extraction", "success", t0, 95, {"task_count": len(extracted_tasks)})
        _set_agent_state("vision", "idle")

        if not extracted_tasks:
            return {"status": "error", "message": "No tasks found in image.", "trace": trace}

        # 2. Priority Agent
        _set_agent_state("priority", "running")
        _log("Priority Agent", "Calculating priority scores", "running")
        t0 = time.time()
        prioritized_tasks = []
        for task in extracted_tasks:
            # Add defaults for missing fields to avoid API errors
            req = {
                "title": task.get("title", "Unknown"),
                "deadline": task.get("deadline", ""),
                "description": task.get("description", ""),
                "estimated_hours": 2
            }
            score_res = self.priority.analyze_priority(req)
            task["priority_score"] = score_res.get("priority_score", 50)
            task["estimated_hours"] = score_res.get("estimated_hours", 2)
            prioritized_tasks.append(task)
        
        _log("Priority Agent", "Assigned priority scores", "success", prioritized_tasks)
        TelemetryService.log_execution("Priority Agent", "Priority Scoring", "success", t0, 90, {"task_count": len(prioritized_tasks)})
        _set_agent_state("priority", "idle")

        # 3. Planning Agent
        _set_agent_state("planning", "running")
        _log("Planning Agent", "Synthesizing schedule", "running")
        t0 = time.time()
        plan_result = self.planning.generate_schedule(prioritized_tasks, availability)
        _log("Planning Agent", "Generated execution schedule", "success", plan_result)
        TelemetryService.log_execution("Planning Agent", "Schedule Synthesis", "success", t0, 85)
        _set_agent_state("planning", "idle")

        # 4. Accountability Agent
        _set_agent_state("accountability", "running")
        _log("Accountability Agent", "Analyzing execution behavior", "running")
        t0 = time.time()
        # In a real scenario, completed/overdue tasks would be pulled from the DB here.
        accountability_result = self.accountability.generate_metrics(prioritized_tasks, [], [])
        _log("Accountability Agent", "Calculated productivity metrics", "success", accountability_result)
        TelemetryService.log_execution("Accountability Agent", "Behavior Analysis", "success", t0, 80)
        _set_agent_state("accountability", "idle")

        # 5. Coach Agent
        _set_agent_state("coach", "running")
        _log("Coach Agent", "Drafting coaching insights", "running")
        t0 = time.time()
        coach_result = self.coach.generate_coaching(prioritized_tasks, accountability_result)
        _log("Coach Agent", "Generated personalized coaching plan", "success", coach_result)
        TelemetryService.log_execution("Coach Agent", "Coaching Insights", "success", t0, 88)
        _set_agent_state("coach", "idle")

        # 6. Rescue Agent
        _set_agent_state("rescue", "running")
        _log("Rescue Agent", "Analyzing schedule for critical risks", "running")
        t0 = time.time()
        rescue_result = self.rescue.detect_risk(prioritized_tasks, availability)
        
        if rescue_result.get("risk_detected"):
             _log("Rescue Agent", "Detected high risk - generated recovery plan", "warning", rescue_result)
        else:
             _log("Rescue Agent", "Schedule is safe. No intervention needed.", "success", rescue_result)
             
        TelemetryService.log_execution("Rescue Agent", "Risk Detection", "success", t0, 92, {"risk_detected": rescue_result.get("risk_detected")})
        _set_agent_state("rescue", "idle")

        # 7. Digital Twin
        _set_agent_state("twin", "running")
        _log("Digital Twin", "Simulating worst-case scenario (Delay critical task)", "running")
        t0 = time.time()
        
        critical_task = max(prioritized_tasks, key=lambda x: x.get("priority_score", 0))
        scenario = {
            "action": "delay_task",
            "task": critical_task["title"],
            "delay_days": 1
        }
        twin_result = self.twin.simulate_scenario(prioritized_tasks, scenario, availability)
        _log("Digital Twin", "Forecasted simulation outcomes", "success", twin_result)
        TelemetryService.log_execution("Digital Twin Agent", "Simulation", "success", t0, 90)
        _set_agent_state("twin", "idle")

        # 8. Reflection Agent
        _set_agent_state("reflection", "running")
        _log("Reflection Agent", "Synthesizing daily reflection", "running")
        t0 = time.time()
        reflection_result = self.reflection.generate_reflection(prioritized_tasks, twin_result)
        _log("Reflection Agent", "Generated daily reflection report", "success", reflection_result)
        TelemetryService.log_execution("Reflection Agent", "Daily Reflection", "success", t0, 85)
        _set_agent_state("reflection", "idle")

        # Final Assembly
        final_briefing = {
            "status": "success",
            "pipeline_summary": "Full Intelligence Briefing complete.",
            "data": {
                "vision": vision_result,
                "tasks": prioritized_tasks,
                "schedule": plan_result,
                "accountability": accountability_result,
                "coach": coach_result,
                "rescue": rescue_result,
                "twin": twin_result,
                "reflection": reflection_result
            },
            "trace": trace
        }

        return final_briefing
