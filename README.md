# 🤝 SIH26088 — Multilingual Cooperative Governance & Legal Assistance Chatbot

> **Smart India Hackathon 2026**  
> An AI-powered assistant helping cooperative society members, farmers, and rural citizens access cooperative laws, government schemes, and grievance redressal — in Hindi, Marathi, and English.

---

## 📋 Project Overview

Cooperative societies serve millions of Indian farmers and rural communities, yet navigating cooperative laws, PACS operations, government schemes (PMFBY, KCC), and grievance procedures is complex and inaccessible without expert help.

This chatbot bridges that gap by providing:

- **Multilingual support**: English, Hindi, Marathi
- **Cooperative law guidance**: Maharashtra Cooperative Societies Act, model by-laws
- **Scheme information**: PMFBY, KCC, PACS, Financial Literacy
- **Grievance workflow**: File and track cooperative grievances
- **RAG-powered answers**: Grounded in authoritative knowledge documents

---

## 🏗️ Architecture

```
Browser (React + Vite)
        ↓  HTTP (REST)
FastAPI Backend
        ↓
AIProvider (abstract interface)
        ↓
GeminiProvider → Gemini API
        ↓
Supabase (PostgreSQL + pgvector for RAG)
```

**Why this architecture?**
- React never calls Gemini directly — all AI calls go through FastAPI
- `AIProvider` is a swappable abstraction — OpenAI can replace Gemini with zero frontend changes
- Supabase will handle both structured data (grievances, users) and vector search (RAG)

---

## 📁 Folder Structure

```
/
├── frontend/                  # React + Vite + TypeScript SPA
│   ├── src/
│   │   ├── api/               # API client (all fetch calls)
│   │   │   └── client.ts
│   │   ├── components/        # UI components
│   │   │   ├── ChatArea.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   └── QuickTopics.tsx
│   │   ├── types/             # TypeScript interfaces
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── .env.example
│   └── package.json
│
├── backend/                   # Python FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py  # GET /health
│   │   │       └── query.py   # POST /api/query
│   │   ├── providers/
│   │   │   ├── ai_provider.py     # Abstract base class
│   │   │   └── gemini_provider.py # Gemini implementation
│   │   ├── schemas/
│   │   │   └── query.py           # Pydantic request/response models
│   │   ├── config.py              # Settings from .env
│   │   ├── dependencies.py        # FastAPI dependency injection
│   │   └── main.py                # App entry point + CORS
│   ├── .env.example
│   └── requirements.txt
│
├── knowledge_base/            # RAG documents (populated in M2)
│   └── README.md
│
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ⚠️ Service role key — **never expose to frontend** |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `APP_ENV` | `development` or `production` |
| `LOG_LEVEL` | `INFO`, `DEBUG`, etc. |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | FastAPI backend URL (default: `http://localhost:8000`) |

> **Security**: Only `VITE_*` variables are exposed to the browser. Never put `GEMINI_API_KEY` or Supabase service-role keys in `.env.local`.

---

## 🚀 Frontend Setup

**Requirements**: Node.js 18+

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local if your backend runs on a different port
npm run dev
```

Runs at: **http://localhost:5173**

---

## 🚀 Backend Setup

**Requirements**: Python 3.11+

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in real values in .env
uvicorn app.main:app --reload --port 8000
```

Runs at: **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

---

## 🧪 Testing the API

### Health check

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### Query endpoint

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"message": "What is PMFBY?", "language": "en"}'
```

Expected response:
```json
{
  "answer": "Hello! I am the Cooperative AI Assistant...",
  "language": "en",
  "intent": "GENERAL_COOPERATIVE",
  "source": null,
  "next_action": null
}
```

---

## 📦 Current MVP Scope (Milestone 1)

- [x] React + Vite + TypeScript frontend
- [x] Multilingual UI (English, Hindi, Marathi)
- [x] Chat interface with quick topic buttons
- [x] Mobile-responsive design
- [x] FastAPI backend with CORS configured
- [x] `GET /health` endpoint
- [x] `POST /api/query` with Pydantic validation
- [x] `AIProvider` abstraction layer
- [x] `GeminiProvider` stub (returns placeholder responses)
- [x] Supabase config ready in settings
- [x] `.env.example` for both frontend and backend

---

## 🗺️ Future Modules

| Milestone | Module |
|---|---|
| M2 | Gemini API integration + intent classification |
| M3 | RAG pipeline with Supabase pgvector |
| M4 | Web voice (Speech-to-Text / Text-to-Speech) |
| M5 | Grievance workflow (file, track, escalate) |
| M6 | Supabase database schema (users, grievances, sessions) |
| M7 | Authentication |
| M8 | ESP32 / INMP441 hardware integration |
| M9 | OV2640 camera + OCR |
| M10 | Hardware dashboard + telemetry |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| AI | Google Gemini API |
| Database | Supabase (PostgreSQL + pgvector) |
| Deployment | Vercel (frontend), Render (backend), Supabase (DB) |

---

*Smart India Hackathon 2026 · Problem Statement SIH26088*
