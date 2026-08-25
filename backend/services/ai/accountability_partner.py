"""
DeadlineOS — AI Accountability Partner
======================================
Provides grounded, execution-focused conversational support.
Recommends concrete next actions based strictly on actual tasks and schedules.
"""

import logging
from typing import Dict, Any, List, Optional
from services.ai.provider import AIProvider, get_default_ai_provider
from services.ai.context_builder import AIContextBuilder
from services.ai.safety import AISafety

logger = logging.getLogger(__name__)

ACCOUNTABILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "suggested_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "label": {"type": "string"},
                    "payload": {"type": "object"}
                },
                "required": ["action_type", "label"]
            }
        },
        "grounding_context": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "integer"}
    },
    "required": ["reply", "suggested_actions", "grounding_context", "confidence"]
}


class AccountabilityPartnerService:
    @classmethod
    def chat(
        cls,
        user_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Processes conversational interaction grounded in user's DeadlineOS execution state.
        """
        ai_provider = provider or get_default_ai_provider()
        context = AIContextBuilder.build_unified_inference_context(user_id)
        clean_input = AISafety.sanitize_user_input(user_message)

        def deterministic_fallback() -> Dict[str, Any]:
            tasks = context.get("tasks", [])
            slots = context.get("schedule", [])
            recovery = context.get("recovery", {})

            actions = []
            grounding = []

            if recovery.get("is_vacation_mode"):
                reply = "You are currently in Vacation Mode. All scheduled deadlines and reminders are paused."
                grounding.append("Vacation Mode is currently active.")
                return {
                    "reply": reply,
                    "suggested_actions": actions,
                    "grounding_context": grounding,
                    "confidence": 95
                }

            if slots:
                next_slot = slots[0]
                reply = f"Your next scheduled focus block is '{next_slot.get('task_title')}'."
                grounding.append(f"Upcoming slot: {next_slot.get('task_title')}")
                actions.append({
                    "action_type": "START_RUNTIME",
                    "label": f"Start '{next_slot.get('task_title')}'",
                    "payload": {"slot_id": next_slot.get("id"), "entity_id": next_slot.get("entity_id")}
                })
            elif tasks:
                next_task = tasks[0]
                reply = f"You have {len(tasks)} pending task(s). Top priority is '{next_task.get('title')}'."
                grounding.append(f"Top task: {next_task.get('title')}")
                actions.append({
                    "action_type": "VIEW_TASK",
                    "label": f"Open '{next_task.get('title')}'",
                    "payload": {"task_id": next_task.get("id")}
                })
            else:
                reply = "All scheduled tasks and daily focus blocks are complete! You are clear for the day."
                grounding.append("Zero pending tasks or upcoming schedule slots.")

            return {
                "reply": reply,
                "suggested_actions": actions,
                "grounding_context": grounding,
                "confidence": 90
            }

        system_prompt = (
            "You are the DeadlineOS AI Accountability Partner. Provide direct, encouraging, "
            "and execution-grounded answers to help the user stay on track with their real tasks. "
            "Do not make up fake deadlines or phantom tasks. Output strictly conforming to JSON schema."
        )

        user_prompt = (
            f"USER QUERY: {clean_input}\n"
            f"USER EXECUTION CONTEXT:\n{context}"
        )

        return ai_provider.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ACCOUNTABILITY_SCHEMA,
            fallback_fn=deterministic_fallback
        )
