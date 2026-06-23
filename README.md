# DeadlineOS

**AI-Powered Executive Operating System for Students, Professionals, and Teams.**

## Overview
DeadlineOS is an advanced, fully integrated executive intelligence platform. Designed to go far beyond traditional task management, it seamlessly integrates a powerful AI Command Center with a real-time Digital Twin to simulate, orchestrate, and optimize your schedule.

**Core Capabilities:**
* **AI Command Center:** Centralized hub for issuing natural language commands.
* **Digital Twin:** Simulates your future capacity and models risk scenarios before they happen.
* **Planner:** Intelligently schedules tasks, maximizing productivity and preventing burnout.
* **Rescue Engine:** Detects and mitigates scheduling conflicts in real-time.
* **Intervention Engine:** Proactively catches missed deadlines and auto-generates rescue strategies.
* **Calendar Intelligence:** Visual execution layer with deep insights into workload density.
* **Document Intelligence:** Extracts actionable tasks directly from unstructured PDFs, Syllabi, and Requirements.
* **Vision Intelligence:** Understands images, screenshots, and visual assignments.
* **Voice Copilot:** Complete voice-driven interaction for hands-free operation.
* **Analytics Observatory:** Executive dashboard detailing AI confidence, productivity velocity, and system health.

## Core Architecture
**Frontend:**
* React
* TypeScript
* Vite
* Tailwind CSS
* Framer Motion

**Backend:**
* Flask
* SQLAlchemy
* PostgreSQL (Neon)

**AI Layer:**
* Gemini (Google AI)
* Planning Agent
* Rescue Agent
* Vision Agent
* Voice Agent
* Digital Twin Agent
* Intervention Engine

## Features

## Executive Dashboard

![Dashboard](docs/screenshots/dashboard.png)

## AI Command Center

![Command Center](docs/screenshots/command-center.png)

## AI Planner

![Planner](docs/screenshots/planner.png)

## Rescue Operations Center

![Rescue](docs/screenshots/rescue.png)

## Goals & Habits Intelligence

![Goals](docs/screenshots/goals.png)

## Digital Twin Laboratory

![Digital Twin](docs/screenshots/digital-twin.png)

## Executive Calendar Intelligence

![Calendar](docs/screenshots/calendar.png)

## Active Interventions

![Interventions](docs/screenshots/interventions.png)

## Executive Intelligence Observatory

![Analytics](docs/screenshots/analytics.png)

## Document Intelligence

![Documents](docs/screenshots/documents.png)

## Vision Intelligence

![Vision](docs/screenshots/vision.png)

## Voice Copilot

![Voice](docs/screenshots/voice.png)

## System Flow

**Document:**
Document Upload → Task Extraction → Planner → Calendar → Digital Twin → Intervention Engine → Analytics

**Vision:**
Vision Upload → OCR Processing → Task Creation → Planning Engine

**Voice:**
Voice Input → Intent Detection → Agent Routing → Execution

## Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Environment Variables
Create a `.env` file in the `backend/` directory:
```env
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=your_postgresql_key
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Database Migration
```bash
cd backend
flask db upgrade
```

### 5. Run Locally
Start the backend API (Port 5000):
```bash
cd backend
flask run --port=5000
```
Start the frontend dev server (Port 5173):
```bash
cd frontend
npm run dev
```

## Deployment
* **Frontend:** Vercel (Production configuration)
* **Backend:** Render (Platform-as-a-Service)
* **Database:** Neon Serverless PostgreSQL

## Security
* **Upload Validation:** Strict MIME type checking and file bounds for Documents, Images, and Audio.
* **Timeout Guards:** Hard multi-threaded timeouts on all LLM calls prevent hanging WSGI workers.
* **SQLAlchemy Protection:** Mitigates SQL injection through ORM parameterized queries.
* **Error Boundaries:** Frontend gracefully catches React faults without breaking the UI application.
* **Graceful Degradation:** The UI dynamically falls back to safe states if the AI provider experiences outages.

## Performance
* **N+1 Elimination:** Recursive loop queries replaced with pre-fetched sets and bulk transactions.
* **Pagination:** Strict page bounds configured on historical intelligence and task endpoints.
* **Query Governance:** Metric aggregation safely offloaded from Python directly to Neon PostgreSQL.
* **React Memoization:** Advanced charts, physics visualizers, and dashboards stabilized via memo and useCallback.
* **AI Timeout Controls:** Complete execution isolation for long-running generative models.

## Project Status
**Production Ready**
Phase 17D Launch Certified
