"""
DeadlineOS — Vision Agent
=============================
An intelligent productivity analyst capable of converting visual 
information (screenshots, handwritten notes, timetables) into 
actionable structured tasks.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

VISION_PROMPT_TEMPLATE = """You are the Vision Agent in DeadlineOS — an intelligent productivity analyst capable of converting visual information into actionable tasks.
Analyze the provided image (which could be a screenshot, handwritten note, timetable, meeting note, or study plan).

CORE RESPONSIBILITIES:
1. Extract all identifiable tasks, assignments, and obligations.
2. Extract any visible deadlines or due dates (convert to YYYY-MM-DD if possible).
3. Extract any specific action items or sub-tasks.
4. Automatically generate priority recommendations ("High", "Medium", "Low") based on the implied urgency or context of the document.
5. Provide a brief executive summary of what was found.

Output EXACTLY according to the following JSON schema:
{schema_json}
"""

VISION_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "deadline": {"type": "string", "description": "YYYY-MM-DD or 'None'"},
                    "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "description": "Recommended priority"}
                },
                "required": ["title", "deadline", "priority"]
            }
        },
        "deadlines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "date": {"type": "string"}
                },
                "required": ["task", "date"]
            }
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "summary": {
            "type": "string"
        }
    },
    "required": ["tasks", "deadlines", "action_items", "summary"]
}

class VisionAgent:
    """Agent responsible for multimodal task extraction from images."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def extract_tasks_from_image(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Analyzes an image and extracts structured tasks, deadlines, and action items.
        
        Args:
            image_bytes: raw image content
            mime_type: e.g. "image/png" or "image/jpeg"
            
        Returns:
            dict: Structured extraction results matching VISION_SCHEMA.
        """
        # GeminiService vision endpoint takes a single combined prompt
        full_prompt = VISION_PROMPT_TEMPLATE.format(
            schema_json=json.dumps(VISION_SCHEMA, indent=2)
        )
        
        logger.info("Vision Agent analyzing %s image (%d bytes)", mime_type, len(image_bytes))
        
        try:
            result = self.gemini.generate_vision(
                image_bytes=image_bytes,
                prompt=full_prompt,
                mime_type=mime_type,
                structured=True,
                temperature=0.2  # Keep it precise for extraction
            )
            return result
        except Exception as exc:
            logger.error("Vision Agent failed to process image: %s", exc)
            raise
