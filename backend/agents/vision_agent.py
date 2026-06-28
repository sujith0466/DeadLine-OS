"""
DeadlineOS — Vision Agent
=============================
An intelligent productivity analyst capable of converting visual 
information (screenshots, handwritten notes, timetables) into 
actionable structured tasks.
"""

import json
import logging
import io
import re
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

try:
    import dateparser
except ImportError:
    dateparser = None

try:
    import easyocr
    OCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
except ImportError:
    OCR_READER = None

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

    def preprocess_image(self, image_bytes: bytes) -> bytes:
        """Resizes and normalizes image for OCR and Gemini."""
        try:
            # Load with PIL (supports HEIC via pillow_heif)
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize if too large
            max_size = 1600
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
            # Convert PIL to OpenCV format (numpy array)
            cv_img = np.array(img)
            cv_img = cv_img[:, :, ::-1].copy() # RGB to BGR
            
            # 1. Grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # 2. Auto Deskew
            coords = np.column_stack(np.where(gray > 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                if abs(angle) > 0.5:
                    (h, w) = gray.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            # 3. Contrast Enhancement & 4. Noise Reduction
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 5. Adaptive Thresholding
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Convert back to bytes for EasyOCR
            success, encoded_img = cv2.imencode('.png', thresh)
            if success:
                return encoded_img.tobytes()
                
            # Fallback to pure PIL
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()
        except Exception as e:
            logger.warning("Image preprocessing failed, using original: %s", e)
            return image_bytes

    def extract_tasks_via_ocr(self, image_bytes: bytes) -> tuple[Dict[str, Any], float]:
        """Runs local OCR and regex extraction if text is highly structured."""
        if not OCR_READER:
            return {}, 0.0
            
        try:
            results = OCR_READER.readtext(image_bytes)
            if not results:
                return {}, 0.0
                
            # Calculate average confidence
            confs = [res[2] for res in results]
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            
            # Combine text
            text_lines = [res[1] for res in results]
            full_text = "\n".join(text_lines)
            
            return {
                "raw_text": full_text,
                "parsed_preview": self.parse_raw_text(full_text)
            }, avg_conf
            
        except Exception as e:
            logger.error("OCR extraction failed: %s", e)
            return {"raw_text": "", "parsed_preview": {"tasks": [], "deadlines": [], "action_items": []}}, 0.0

    def parse_raw_text(self, full_text: str) -> Dict[str, Any]:
        """Parses structured tasks and deadlines from raw text."""
        tasks = []
        deadlines = []
        action_items = []
        
        lines = full_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue
                
            task_text = re.sub(r"^([-*•]|\d+\.|\[[ xX]\])\s*", "", line).strip()
            
            if task_text.lower() not in ["meeting agenda", "doctor's note", "messy whiteboard"]:
                # Try Dateparser first
                parsed_date = None
                if dateparser:
                    parsed_date_obj = dateparser.parse(task_text, settings={'STRICT_PARSING': False})
                    if parsed_date_obj:
                        parsed_date = parsed_date_obj.strftime("%Y-%m-%d")
                
                # Regex Fallback
                if not parsed_date:
                    date_match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}|\d{4}-\d{2}-\d{2}", task_text, re.IGNORECASE)
                    if date_match:
                        parsed_date = date_match.group(0)
                        
                deadline_val = parsed_date if parsed_date else "None"
                
                if deadline_val != "None":
                    deadlines.append({"task": task_text, "date": deadline_val})
                    
                tasks.append({
                    "title": task_text[:100],
                    "deadline": deadline_val,
                    "priority": "Medium"
                })
                action_items.append(task_text)
                
        return {
            "tasks": tasks,
            "deadlines": deadlines,
            "events": [],
            "action_items": action_items,
            "priorities": [t["priority"] for t in tasks]
        }

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
