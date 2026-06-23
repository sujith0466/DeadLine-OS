"""
DeadlineOS — Document Intelligence Agent
========================================
Extracts tasks, deadlines, action items, and owners from uploaded meeting/project notes.
"""

from typing import Dict, Any
from services.gemini_service import GeminiService

class DocumentIntelligenceAgent:

    def __init__(self, gemini_service):
        self.gemini = gemini_service

    def parse_document(self, text: str) -> Dict[str, Any]:
        """Parses raw text into structured execution items."""
        
        prompt = f"""
        You are the Document Intelligence Agent.
        Analyze the following document/meeting notes and extract all actionable intelligence.
        
        DOCUMENT TEXT:
        {text[:15000]} # Truncated to fit standard prompt window safely.
        
        Extract:
        1. tasks (Array of Strings: Specific tasks to be done)
        2. deadlines (Array of Strings: Any mentioned dates/times)
        3. action_items (Array of Strings: High-level action items)
        4. owners (Array of Strings: People responsible for tasks)
        5. summary (String: 2-3 sentence summary of the document's purpose)
        """
        
        schema = {
            "type": "OBJECT",
            "properties": {
                "tasks": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "deadlines": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "action_items": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "owners": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "summary": {"type": "STRING"}
            },
            "required": ["tasks", "deadlines", "action_items", "owners", "summary"]
        }
        
        try:
            return self.gemini.generate_structured(prompt, text, schema)
        except Exception as e:
            import logging
            logging.error(f"DocumentIntelligenceAgent Error: {e}")
            return {
                "tasks": ["Review parsed document"],
                "deadlines": ["ASAP"],
                "action_items": ["Manual review required due to parsing error."],
                "owners": ["System"],
                "summary": "Document processing encountered an error."
            }
