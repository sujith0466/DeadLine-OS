# DeadlineOS — Usage Guide

> This document is supplementary documentation only. It does not alter, extend,
> or restrict the legal permissions granted by the [MIT License](LICENSE).

---

## Table of Contents

- [Installation](#installation)
- [Project Setup](#project-setup)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Production Build](#production-build)
- [Repository Structure](#repository-structure)
- [Contribution Workflow](#contribution-workflow)
- [Best Practices](#best-practices-for-using-deadlineos)

---

## Installation

### Prerequisites

Ensure the following are installed on your machine before proceeding:

| Tool | Minimum Version | Purpose |
|---|---|---|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend toolchain |
| npm | 9+ | Package manager |
| Git | Any | Version control |

### Clone the Repository

```bash
git clone https://github.com/sujith0466/DeadLine-OS.git
cd DeadLine-OS
```

---

## Project Setup

### Backend (Python / Flask)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Frontend (React / Vite)

```bash
cd frontend

# Install Node dependencies
npm install
```

---

## Environment Variables

Copy the example environment files and populate them with your credentials.
**Never commit `.env` files to version control.**

```bash
cp backend/.env.example  backend/.env
cp frontend/.env.example frontend/.env
```

### Backend `.env`

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | Neon PostgreSQL connection string (port 6543, `?sslmode=require`) |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_JWT_SECRET` | ✅ | JWT verification secret from Supabase |
| `GEMINI_API_KEY` | ✅ | Google Gemini 2.0 Flash API key |
| `SECRET_KEY` | ✅ | Flask session secret — use a long random string |
| `FRONTEND_URL` | ✅ | Your Vercel frontend domain (for CORS) |
| `SENTRY_DSN` | ⚠️ Optional | Sentry error tracking DSN |
| `FLASK_ENV` | ⚠️ Optional | `development` or `production` |

### Frontend `.env`

| Variable | Required | Description |
|---|---|---|
| `VITE_SUPABASE_URL` | ✅ | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | ✅ | Supabase public anon key |
| `VITE_API_BASE_URL` | ✅ | Backend API base URL (e.g., `https://your-api.onrender.com`) |

### External Services Required

1. **Neon PostgreSQL** — Serverless Postgres. Create a project and copy the Transaction Pooler URL.
2. **Supabase** — Auth provider. Create a project, retrieve URL and keys, and configure Site URL / Redirect URLs.
3. **Google Gemini API** — Obtain an API key from [Google AI Studio](https://aistudio.google.com/).

---

## Running the Application

### Backend Development Server

```bash
cd backend
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
python app.py
```

The API will be available at `http://localhost:5000`.

### Frontend Development Server

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.

> **Tip:** The frontend uses Vite's HMR (Hot Module Replacement), so most changes
> are reflected instantly without a full page reload.

---

## Production Build

### Frontend

```bash
cd frontend
npm run build
# Output is generated in frontend/dist/
```

Deploy the `dist/` directory to any static host. The included `vercel.json` handles
SPA routing automatically on Vercel.

### Backend

Use Gunicorn with the Eventlet worker for production:

```bash
gunicorn 'app:create_app()' \
  --worker-class eventlet \
  -w 1 \
  --bind 0.0.0.0:$PORT \
  --timeout 120
```

**Render.com recommended settings:**
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn 'app:create_app()' --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT`

**Vercel recommended settings:**
- Framework Preset: `Vite`
- Root Directory: `frontend`
- Ensure `vercel.json` is present for SPA catch-all routing.

---

## Repository Structure

```text
DeadLine-OS/
├── backend/
│   ├── api/                # Flask Blueprint route handlers
│   ├── database/           # SQLAlchemy engine & session config
│   ├── models/             # ORM model definitions
│   ├── scripts/            # Database migrations & maintenance utilities
│   ├── services/           # Core business logic & AI execution services
│   ├── utils/              # Auth middleware, error handlers, helpers
│   ├── app.py              # Application factory entry point
│   └── requirements.txt    # Python dependencies
├── docs/
│   ├── screenshots/        # Application screenshots for README
│   └── PROJECT_DESCRIPTION.md
├── frontend/
│   ├── public/             # Static assets
│   ├── src/
│   │   ├── api/            # Axios API client configurations
│   │   ├── components/     # Reusable React UI components
│   │   ├── context/        # Global state (Auth, Theme)
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # Utility libraries (Supabase client)
│   │   └── pages/          # Route-level page views
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── CHANGELOG.md            # Release notes
├── CONTRIBUTING.md         # Contribution workflow
├── LICENSE                 # MIT License
├── README.md               # Project overview
└── USAGE.md                # This file — setup & usage guide
```

---

## Contribution Workflow

We welcome contributions of all kinds — bug fixes, features, documentation
improvements, and translations.

### Step-by-step

1. **Open an Issue first** for anything beyond a trivial fix, so the approach
   can be discussed before significant work begins.
   → [Open an Issue](https://github.com/sujith0466/DeadLine-OS/issues)

2. **Fork** the repository to your own GitHub account.

3. **Create a branch** with a descriptive name:
   ```bash
   git checkout -b feature/google-calendar-sync
   # or
   git checkout -b fix/analytics-500-error
   ```

4. **Make your changes**, following the code style of the surrounding files.

5. **Test your changes:**
   ```bash
   # Backend
   pytest tests/

   # Frontend
   npx tsc --noEmit   # Type check
   npm run lint        # Lint
   ```

6. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: add Google Calendar OAuth sync"
   git commit -m "fix: prevent analytics 500 on empty dataset"
   ```

7. **Push** your branch and open a **Pull Request** against `main`:
   ```bash
   git push origin feature/google-calendar-sync
   ```
   Include a clear description, screenshots if relevant, and steps to test.

For the full workflow and coding standards, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Best Practices for Using DeadlineOS

These are **recommendations**, not legal requirements. They reflect open-source
community norms and help maintain a healthy ecosystem around the project.

- **Preserve the copyright notice.** When distributing copies or derivatives,
  keep the original `Copyright (c) 2026 Sujith Kumar Sanisetty` notice intact.

- **Give credit when practical.** If you build a product or showcase using
  DeadlineOS, a visible attribution (e.g., "Built on DeadlineOS") is appreciated
  and encourages collaboration.

- **Document your modifications.** If you fork and modify the project
  significantly, note your changes in a `CHANGELOG.md` or `MODIFICATIONS.md`.
  This helps downstream users understand what has changed from the original.

- **Do not misrepresent your fork.** Do not publish a fork under the name
  "DeadlineOS" in a way that could cause confusion with the official project.

- **Contribute improvements back.** If you fix a bug or add a feature that could
  benefit others, consider opening a Pull Request so the improvement can be
  shared with the whole community.

---

*This document is informational only. See [`LICENSE`](LICENSE) for the full
legal text governing use of this software.*
