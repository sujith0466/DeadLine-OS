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

## System Modules

### Executive Dashboard
[![Executive Dashboard](docs/screenshots/dashboard.png)](docs/screenshots/dashboard.png)

<table width="100%">
  <tr>
    <td width="50%" align="center">
      <b>AI Command Center</b><br><br>
      <a href="docs/screenshots/command-center.png"><img src="docs/screenshots/command-center.png" alt="Command Center"/></a>
    </td>
    <td width="50%" align="center">
      <b>AI Planner</b><br><br>
      <a href="docs/screenshots/planner.png"><img src="docs/screenshots/planner.png" alt="Planner"/></a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>Rescue Operations Center</b><br><br>
      <a href="docs/screenshots/rescue.png"><img src="docs/screenshots/rescue.png" alt="Rescue Center"/></a>
    </td>
    <td width="50%" align="center">
      <b>Active Interventions</b><br><br>
      <a href="docs/screenshots/interventions.png"><img src="docs/screenshots/interventions.png" alt="Active Interventions"/></a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>Digital Twin Laboratory</b><br><br>
      <a href="docs/screenshots/digital-twin.png"><img src="docs/screenshots/digital-twin.png" alt="Digital Twin"/></a>
    </td>
    <td width="50%" align="center">
      <b>Goals & Habits Intelligence</b><br><br>
      <a href="docs/screenshots/goals.png"><img src="docs/screenshots/goals.png" alt="Goals"/></a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>Executive Calendar Intelligence</b><br><br>
      <a href="docs/screenshots/calendar.png"><img src="docs/screenshots/calendar.png" alt="Calendar"/></a>
    </td>
    <td width="50%" align="center">
      <b>Executive Intelligence Observatory</b><br><br>
      <a href="docs/screenshots/analytics.png"><img src="docs/screenshots/analytics.png" alt="Analytics"/></a>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>Document Intelligence</b><br><br>
      <a href="docs/screenshots/documents.png"><img src="docs/screenshots/documents.png" alt="Documents"/></a>
    </td>
    <td width="50%" align="center">
      <b>Vision Intelligence</b><br><br>
      <a href="docs/screenshots/vision.png"><img src="docs/screenshots/vision.png" alt="Vision"/></a>
    </td>
  </tr>
  <tr>
    <td width="100%" colspan="2" align="center">
      <b>Voice Copilot</b><br><br>
      <a href="docs/screenshots/voice.png"><img src="docs/screenshots/voice.png" alt="Voice" width="50%"/></a>
    </td>
  </tr>
</table>
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
