# DeadlineOS Deployment Guide

This guide outlines the production deployment strategy for DeadlineOS.

## 1. Prerequisites
- **Render Account** (Backend API hosting)
- **Vercel Account** (Frontend hosting)
- **Neon** (PostgreSQL Serverless Database)
- **Supabase** (Authentication)
- **Google Cloud** (Gemini API Key)

## 2. Environment Variables Configuration
Ensure all environment variables mapped in `.env.example` are securely added to Vercel (Frontend) and Render (Backend). Do NOT commit `.env` files.

### 2.1 Backend (Render)
Go to the Render dashboard -> Environment:
- `DATABASE_URL`: Your Neon Transaction Pooler URI (ending in `?sslmode=require`).
- `FLASK_SECRET_KEY`: High entropy string.
- `SUPABASE_URL` / `SUPABASE_JWT_SECRET` / `SUPABASE_SERVICE_ROLE_KEY`: Copied from your Supabase Project settings.
- `GEMINI_API_KEY`: Google Studio API Key.
- `CORS_ORIGINS`: `https://your-frontend-domain.vercel.app`
- `SENTRY_DSN`: Your backend Sentry tracking DSN.

### 2.2 Frontend (Vercel)
Go to Vercel Project Settings -> Environment Variables:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL`: `https://your-backend.onrender.com/api`
- `VITE_SENTRY_DSN`: Your frontend Sentry tracking DSN.

## 3. Database Initialization
1. Ensure the Neon database is provisioned.
2. The initial deployment of the backend must run migrations. On Render, set the **Build Command** to:
   ```bash
   pip install -r requirements.txt && flask db upgrade
   ```
   *Note: If you do not use Flask-Migrate, run the initialization python scripts located in `scripts/migrations/` manually.*

## 4. Render Deployment (Backend)
- **Environment:** Docker or Python 3.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --worker-class eventlet -w 1 app:app` (Eventlet handles SocketIO effectively).

## 5. Vercel Deployment (Frontend)
Vercel automatically detects Vite.
- **Framework Preset:** Vite
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

## 6. Verifying Deployment
1. Navigate to the Vercel URL.
2. Check the browser console to ensure zero CORS errors.
3. Attempt a test registration (this validates Supabase, Vercel, and Render).
4. Create a task (this validates Neon and Gemini).
