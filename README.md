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
## 📦 Software Completion Status (Task 6 Complete)

- [x] **React + Vite + TypeScript Frontend**
- [x] **Multilingual Support**: English (`en-IN`), Hindi (`hi-IN`), Marathi (`mr-IN`)
- [x] **Web Speech STT & TTS**: Browser-native SpeechRecognition & SpeechSynthesis with voice controls
- [x] **FastAPI Backend Gateway**: Centralized `process_user_query()` single source of truth
- [x] **RAG Knowledge Pipeline**: Supabase PostgreSQL + `pgvector` IVFFlat similarity search (768-dim embeddings)
- [x] **Gemini 1.5/2.0 AI Generation**: Strictly grounded with anti-hallucination & prompt injection defense
- [x] **Verified Source Citations**: Real government URLs (`cooperation.gov.in`, `pmfby.gov.in`, `nabard.org`)
- [x] **Domain APIs & Grievance Workflow**: Document listing, Knowledge search, and Grievance preparation summary
- [x] **Hardware-Ready API Contracts**: `/api/voice/query` and `/api/vision/query` ready for tomorrow's ESP32-S3

---

## 🛠️ API Inventory

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `POST` | `/api/query` | Text query endpoint |
| `GET` | `/api/conversations/{id}/messages` | Fetch chat history turns |
| `POST` | `/api/voice/query` | Web & ESP32-S3 hardware voice contract |
| `POST` | `/api/vision/query` | Camera / OCR document contract |
| `GET` | `/api/knowledge/documents` | List registered knowledge documents |
| `GET` | `/api/knowledge/search` | Vector search knowledge chunks |
| `POST` | `/api/grievance` | Grievance draft creation & summary |
| `GET` | `/api/grievance/{id}` | Fetch grievance record details |
| `GET` | `/api/grievance/{id}/summary` | Fetch complaint summary & verification guide |

Interactive Swagger API Documentation is available at **http://localhost:8000/docs**.

---

## 🧪 Testing Commands

### Backend Verification Suite
```bash
cd backend
PYTHONPATH=. .venv/bin/python /Users/pranav/.gemini/antigravity/brain/c58c5817-7655-4820-a79e-489928cd0b8e/scratch/test_task6_verification.py
```

### Frontend Build Check
```bash
cd frontend
npm run build
```

---

## 🔌 Hardware-Ready Architecture (ESP32-S3 Ready for Tomorrow)

```
                  ┌──────────────────────┐
                  │  ESP32-S3 Hardware   │
                  │  INMP441 / Button    │
                  └──────────┬───────────┘
                             │
                      HTTPS POST /api/voice/query
                             │
                             ▼
                  ┌──────────────────────┐
                  │   FastAPI Gateway    │
                  └──────────┬───────────┘
                             │
                             ▼
                    process_user_query()
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
         RAG + Gemini                  Persistence
```

*Note: ESP32 devices communicate purely over HTTPS with FastAPI and require zero secret keys (`GEMINI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`).*

---

*Smart India Hackathon 2026 · Problem Statement SIH26088*
