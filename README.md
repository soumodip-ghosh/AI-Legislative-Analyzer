# LexClear — AI Legislative Analyzer

A citizen dashboard that turns dense Indian parliamentary bills and acts into plain-English summaries. Built with FastAPI + Next.js, using token compression and RAG to keep inference costs low.

---

## Architecture Overview

```
User uploads PDF/DOCX
        ↓
[Backend FastAPI]
  1. File validation (type, size)
  2. Cache check (SHA-256 hash)
  3. Domain classification (keyword-based, no LLM)
  4. Text extraction (PyMuPDF / python-docx)
  5. Token compression (strip filler, extract facts)
  6. RAG pipeline (FAISS + semantic chunking)
  7. Single LLM call → structured JSON
  8. Cache result
        ↓
[Frontend Next.js]
  Dashboard with animated cards
```

---

## Project Structure

```
legislative-analyzer/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, middleware wiring
│   ├── requirements.txt
│   ├── render.yaml                # Render deployment config
│   ├── .env.example
│   ├── routes/
│   │   └── analyze.py             # POST /api/analyze endpoint
│   ├── services/
│   │   ├── parser.py              # PDF + DOCX text extraction
│   │   ├── classifier.py          # Keyword-based domain filter
│   │   ├── compressor.py          # Token compression pipeline
│   │   └── rag.py                 # LangChain + FAISS RAG
│   ├── middleware/
│   │   └── rate_limit.py          # Per-IP rate limiter
│   └── utils/
│       └── cache.py               # SHA-256 hash-based result cache
│
└── frontend/
    ├── pages/
    │   ├── _app.tsx
    │   ├── _document.tsx
    │   └── index.tsx              # Main dashboard page
    ├── components/
    │   ├── UploadZone.tsx         # Drag & drop upload
    │   ├── ProcessingSteps.tsx    # Animated step tracker
    │   ├── SummaryCard.tsx        # Summary + simplified explanation
    │   ├── KeyChangesCard.tsx     # Key legislative changes
    │   ├── AffectedEntitiesCard.tsx
    │   ├── FinancialImpactCard.tsx
    │   ├── TimelineCard.tsx
    │   └── TokenStats.tsx         # Token compression metrics
    ├── styles/
    │   └── globals.css
    ├── package.json
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── vercel.json
    └── .env.local.example
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start dev server
uvicorn main:app --reload --port 8000
```

API will be live at: http://localhost:8000
Interactive docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000/api  (already set)

# Start dev server
npm run dev
```

App will be live at: http://localhost:3000

---

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ |
| `ALLOWED_ORIGINS` | Comma-separated frontend URLs | ✅ |

### Frontend (.env.local)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | ✅ |

---

## Deployment

### Backend → Render

1. Push backend folder to a GitHub repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Render auto-detects `render.yaml` — review and confirm settings
5. Under **Environment**, add:
   - `OPENAI_API_KEY` = your key
   - `ALLOWED_ORIGINS` = `https://your-app.vercel.app`
6. Deploy. Note your service URL (e.g. `https://legislative-analyzer-api.onrender.com`)

### Frontend → Vercel

1. Push frontend folder to GitHub (can be same repo)
2. Go to [vercel.com](https://vercel.com) → New Project → Import repo
3. Set root directory to `frontend/`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-api.onrender.com/api`
5. Deploy

---

## API Reference

### `POST /api/analyze`

Upload a legal document for analysis.

**Request:** `multipart/form-data`
- `file`: PDF or DOCX file (max 5MB)

**Response:**
```json
{
  "summary": "Plain-English summary of the document",
  "key_changes": [
    { "title": "...", "description": "...", "impact_level": "high|medium|low" }
  ],
  "affected_entities": [
    { "entity": "Citizens", "how": "Must register by..." }
  ],
  "financial_impact": {
    "description": "...",
    "figures": ["₹10,000 fine", "5% tax"],
    "who_pays": "...",
    "who_benefits": "..."
  },
  "timeline": [
    { "date": "1 April 2025", "event": "Act comes into force" }
  ],
  "simplified_explanation": "In simple terms...",
  "penalties_and_compliance": "Non-compliance results in...",
  "document_type": "Act|Bill|Amendment|Policy|Notification",
  "tokens_saved": 8421,
  "original_tokens": 12300,
  "compressed_tokens": 3879,
  "is_legal": true,
  "from_cache": false
}
```

**Error responses:**
- `400` — Invalid file type or size
- `413` — Document too large (>50k tokens after parsing)
- `422` — Could not parse document
- `429` — Rate limit exceeded (10 req/min per IP)
- `504` — Analysis timed out

### `GET /health`

Health check. Returns `{ "status": "ok", "version": "1.0.0" }`.

---

## How Token Compression Works

Before any LLM call, the document goes through:

1. **Filler stripping** — removes boilerplate phrases like "notwithstanding anything contained", standard preamble language, signature blocks
2. **Fact extraction** — captures dates, monetary figures, penalty clauses, and section headers
3. **Semantic chunking** — splits on section/article boundaries (not fixed character counts)
4. **Chunk scoring** — ranks chunks by density of meaningful content
5. **Budget-aware selection** — picks the highest-value chunks that fit the token budget

Typical reduction: **60–75%** on standard parliamentary bills.

---

## Domain Classification

The system rejects non-legal documents *before* hitting the LLM — free and fast.

Uses:
- Keyword density scoring (legal terminology)
- Structural pattern matching (section numbers, gazette references, enactment language)
- Hard-reject keywords for obvious non-legal content (recipes, fiction, etc.)

---

## Security

- **Rate limiting**: 10 requests/minute per IP (in-memory; swap for Redis in production)
- **File validation**: Extension + size checks before any processing
- **Token guard**: Hard limit of 50,000 tokens — rejects oversized docs
- **Caching**: SHA-256 document hash — identical files skip re-inference
- **CORS**: Configured to allowed origins only
- **No hardcoded secrets**: All keys via environment variables

---

## Caveats

- In-memory cache resets on server restart. For production, wire `utils/cache.py` to Redis.
- Rate limiter is per-process. Behind multiple workers, use a shared store.
- LLM output is AI-generated — always verify against official gazette before legal action.
- Scanned PDFs (image-only) will fail — OCR not included in this version.
