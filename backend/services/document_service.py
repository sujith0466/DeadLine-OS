"""
DeadlineOS — Document Service
=============================
Handles raw file parsing (PDF, DOCX, TXT, MD) and routes text to the DocumentIntelligenceAgent.
Integrates with the Orchestration pipeline (adds Tasks).
"""

import os
from typing import Dict, Any, List
from werkzeug.datastructures import FileStorage
import pypdf
import docx
from agents.document_intelligence_agent import DocumentIntelligenceAgent
from models.task import Task
from database.db import db
from services.telemetry_service import TelemetryService
import time

class DocumentService:

    @classmethod
    def process_file(cls, file: FileStorage, user_id: str = None) -> Dict[str, Any]:
        """Extracts text from the file and generates intelligence."""
        from flask import g
        uid = user_id or getattr(g, "user_id", None)
        
        filename = file.filename.lower()
        text = ""

        try:
            t0 = time.time()
            if filename.endswith(".pdf"):
                reader = pypdf.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            elif filename.endswith(".docx"):
                doc = docx.Document(file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
            elif filename.endswith(".txt") or filename.endswith(".md"):
                text = file.read().decode('utf-8')
                
            else:
                return {"error": "Unsupported file format. Use PDF, DOCX, TXT, or MD."}
                
            if not text.strip():
                return {"error": "Could not extract text from document."}

            # Run via Local Intelligence Engine
            from services.local_intelligence.execution_engine import ExecutionEngine
            from flask import current_app
            gemini = current_app.extensions.get("gemini_service")
            
            execution = ExecutionEngine.execute(
                source="document",
                transcript=text[:2000], # Pass the first 2000 chars to avoid token explosion in IntentEngine fallback, normally we'd chunk this for a real system
                gemini_service=gemini,
                user_id=uid
            )
            
            try:
                confidence = execution.get("confidence", 85)
                TelemetryService.log_execution("Document Intelligence", "Extraction", "success", t0, confidence)
            except Exception as t_err:
                import logging
                logging.getLogger(__name__).error(f"Telemetry logging failed for Document Intelligence: {t_err}")
            
            # Form final result consistent with Vision & execution schema expectations
            return {
                "filename": filename,
                "summary": execution.get("message", ""),
                "tasks": execution.get("entities", {}).get("tasks", []),
                "action_items": execution.get("entities", {}).get("action_items", []),
                "deadlines": execution.get("entities", {}).get("deadlines", []),
                "owners": execution.get("entities", {}).get("people", []),
                "inserted_task_ids": execution.get("data", {}).get("inserted_ids", []),
                "tasks_created": len(execution.get("data", {}).get("inserted_ids", [])),
                "structured_result": execution
            }

        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}
