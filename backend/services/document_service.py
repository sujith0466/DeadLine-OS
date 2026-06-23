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

class DocumentService:

    @classmethod
    def process_file(cls, file: FileStorage) -> Dict[str, Any]:
        """Extracts text from the file and generates intelligence."""
        
        filename = file.filename.lower()
        text = ""

        try:
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

            # Run Document Intelligence Agent
            from flask import current_app
            gemini = current_app.extensions.get("gemini_service")
            intelligence = DocumentIntelligenceAgent(gemini).parse_document(text)
            
            # Optional: Auto-create tasks in DB
            # For hackathon demo, we will actually insert these so they show up in Calendar & CommandCenter
            from datetime import datetime, timedelta
            inserted_tasks = []
            for task_data in intelligence.get("tasks", []):
                title = task_data.get("title") if isinstance(task_data, dict) else str(task_data)
                
                deadline_val = task_data.get("deadline") if isinstance(task_data, dict) else None
                if deadline_val:
                    try:
                        deadline = datetime.fromisoformat(deadline_val.replace("Z", "+00:00"))
                    except:
                        deadline = datetime.utcnow() + timedelta(days=1)
                else:
                    deadline = datetime.utcnow() + timedelta(days=1)
                    
                t = Task(title=title, deadline=deadline, status="Pending", estimated_hours=1)
                inserted_tasks.append(t)
            
            if inserted_tasks:
                db.session.add_all(inserted_tasks)
            
            db.session.commit()
            
            # Form final result
            return {
                "filename": filename,
                "summary": intelligence.get("summary", ""),
                "tasks": intelligence.get("tasks", []),
                "deadlines": intelligence.get("deadlines", []),
                "action_items": intelligence.get("action_items", []),
                "owners": intelligence.get("owners", []),
                "tasks_created": len(inserted_tasks)
            }

        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}
