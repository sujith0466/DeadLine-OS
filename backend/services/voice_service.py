"""
DeadlineOS — Voice Service
==========================
Receives transcripts, parses intent via VoiceCopilotAgent, and routes 
execution to the appropriate backend agents/services.
"""

from typing import Dict, Any
from agents.voice_copilot_agent import VoiceCopilotAgent
from agents.rescue_agent import RescueAgent
from agents.digital_twin_agent import DigitalTwinAgent
from agents.priority_agent import PriorityAgent
from services.goal_service import GoalService
from services.telemetry_service import TelemetryService
import time

class VoiceService:

    @classmethod
    def process_voice_command(cls, transcript: str, gemini_service) -> Dict[str, Any]:
        """Parses the transcript, executes the required action, and returns results."""
        t0 = time.time()
        
        # 1. NLU Parsing
        agent = VoiceCopilotAgent(gemini_service)
        nlu_result = agent.parse_transcript(transcript)
        intent = nlu_result.get("intent")
        entities = nlu_result.get("entities", {})
        
        execution_data = {}
        
        # 2. Intent Routing & Execution
        if intent == "task_creation":
            from models.task import Task
            from database.db import db
            from datetime import datetime, timezone, timedelta
            from services.orchestrator import OrchestratorService

            task_title = entities.get("target_name", "New Task")
            target_date = entities.get("target_date")
            confidence = nlu_result.get("confidence", 92)

            try:
                deadline = datetime.fromisoformat(target_date) if target_date else datetime.now(timezone.utc) + timedelta(days=1)
            except:
                deadline = datetime.now(timezone.utc) + timedelta(days=1)

            # Duplicate check
            existing_task = Task.query.filter_by(title=task_title).first()
            if existing_task:
                execution_data = {"status": "Task already exists", "task_id": existing_task.id, "title": existing_task.title}
                OrchestratorService.add_event("Voice Copilot", "Prevented duplicate task creation", "warning", {"title": task_title})
            else:
                t = Task(title=task_title, deadline=deadline, status="pending", source="voice", ai_confidence=confidence)
                db.session.add(t)
                db.session.commit()
                execution_data = {"status": "Task created", "task_id": t.id, "title": t.title}
                OrchestratorService.add_event("Voice Copilot", "Created Task via Voice", "success", execution_data)
            
        elif intent == "rescue":
            from agents.rescue_agent import RescueAgent
            from models.task import Task
            from services.orchestrator import OrchestratorService

            tasks = [t.to_dict() for t in Task.get_all_pending()]
            execution_data = RescueAgent(gemini_service).detect_risk(tasks, {"daily_available_hours": 4})
            OrchestratorService.add_event("Voice Copilot", "Triggered Rescue Mode", "warning", {"risk_detected": execution_data.get("risk_detected")})
            
        elif intent == "digital_twin":
            from services.orchestrator import OrchestratorService
            from models.task import Task
            tasks = [t.to_dict() for t in Task.get_all_pending()]
            execution_data = DigitalTwinAgent(gemini_service).simulate_scenario(tasks, {"action": "shift", "shift": "Voice Command"}, {"daily_available_hours": 8})
            OrchestratorService.add_event("Voice Copilot", "Triggered Digital Twin", "success", {"scenario": "Voice Simulation"})
            
        elif intent == "goal_creation":
            from services.orchestrator import OrchestratorService
            goal_title = entities.get("target_name", "New Goal")
            execution_data = GoalService.create_goal(goal_title, "Created via voice.", "General", entities.get("target_date"))
            OrchestratorService.add_event("Voice Copilot", "Created Goal via Voice", "success", {"goal_id": execution_data.get("goal", {}).get("id")})
            
        elif intent == "planning":
            from agents.planning_agent import PlanningAgent
            from models.task import Task
            from services.orchestrator import OrchestratorService

            tasks = [t.to_dict() for t in Task.get_all_pending()]
            execution_data = PlanningAgent(gemini_service).generate_schedule(tasks, {"daily_available_hours": 8})
            OrchestratorService.add_event("Voice Copilot", "Generated Schedule via Voice", "success", {"tasks_planned": len(tasks)})
            
        else:
            from services.orchestrator import OrchestratorService
            # For query intents (analytics, calendar, habit), we just return a success state
            execution_data = {"status": "Query processed", "intent": intent}
            OrchestratorService.add_event("Voice Copilot", "Processed Voice Query", "success", {"intent": intent})

        try:
            confidence = nlu_result.get("confidence", 90)
            TelemetryService.log_execution("Voice Copilot", "Intent Processing", "success", t0, confidence)
        except Exception as t_err:
            import logging
            logging.getLogger(__name__).error(f"Telemetry logging failed for Voice Copilot: {t_err}")

        return {
            "transcript": transcript,
            "nlu": nlu_result,
            "execution": execution_data
        }
