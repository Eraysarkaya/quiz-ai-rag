# CLAUDE.md

> Project context file for Claude Code - Quiz AI

## Project Overview

**Quiz AI** is a full-stack academic project for AI-powered multiple-choice question (MCQ) generation using RAG (Retrieval-Augmented Generation) and LLM architecture. Built as a thesis/research project for generating high-quality science quiz questions.

### Core Stack
- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **AI/ML**: Groq LLaMA 3.3-70B, FAISS, SentenceTransformers (all-mpnet-base-v2)
- **Auth**: Google OAuth, JWT (python-jose)
- **Dataset**: SciQ (HuggingFace datasets)

---

## Architecture

```
quiz-ai/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Pydantic settings
│   │   ├── middleware.py      # Rate limiting, security headers
│   │   ├── auth/              # Google OAuth
│   │   ├── core/              # Core business logic
│   │   │   ├── config.py      # Centralized config (models, paths, thresholds)
│   │   │   ├── pipeline.py    # End-to-end quiz generation
│   │   │   ├── mcq_generator.py  # LLM-based MCQ generation
│   │   │   ├── rag_retriever.py  # FAISS + SentenceTransformer
│   │   │   ├── embedding_service.py  # Singleton embedding
│   │   │   ├── semantic_cache.py     # Semantic caching
│   │   │   └── ood_detector.py       # Out-of-domain detection
│   │   ├── models/            # Pydantic models
│   │   ├── routes/            # API endpoints
│   │   └── services/          # Business logic layer
│   ├── data/
│   │   ├── processed/         # Corpus and chunks (JSONL)
│   │   └── vectorstore/       # FAISS index and metadata
│   └── scripts/               # Setup scripts
│       ├── load_dataset.py    # Load SciQ from HuggingFace
│       ├── chunking.py        # Semantic text chunking
│       └── build_index.py     # Build FAISS vector index
│
├── frontend/                   # Next.js 16 Frontend
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/        # React components
│   │   ├── lib/               # Client utilities, contexts
│   │   └── types/             # TypeScript definitions
│   └── package.json
│
└── tez/                        # Thesis/Evaluation
    ├── evaluation/            # Evaluation framework
    │   ├── src/               # Core evaluation modules
    │   │   ├── config.py      # Model and metric configuration
    │   │   ├── metrics.py     # LLM-as-Judge metrics
    │   │   ├── judge.py       # GPT-OSS 120B judge
    │   │   └── groq_api.py    # Groq API wrapper
    │   ├── scripts/           # Evaluation scripts
    │   │   ├── generate_questions.py
    │   │   └── run_evaluation.py
    │   ├── data/              # Topics and SciQ data
    │   ├── generated/         # Generated questions
    │   └── results/           # Evaluation results
    └── results/               # Benchmark results
```

---

## Key Files

### Backend Core
| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app with CORS, middleware, routers |
| `backend/app/core/config.py` | All tunable parameters (model, paths, thresholds) |
| `backend/app/core/pipeline.py` | End-to-end quiz generation (RAG + MCQ) |
| `backend/app/core/mcq_generator.py` | LLM prompts with Bloom's taxonomy |
| `backend/app/core/rag_retriever.py` | FAISS vector search with cosine similarity |
| `backend/app/core/embedding_service.py` | Singleton SentenceTransformer |

### Frontend Core
| File | Purpose |
|------|---------|
| `frontend/src/app/page.tsx` | Main quiz UI |
| `frontend/src/lib/api.ts` | API client with auth |
| `frontend/src/lib/AuthContext.tsx` | Auth state management |
| `frontend/src/components/TopicInput.tsx` | Topic input form |

### Evaluation Core (Thesis)
| File | Purpose |
|------|---------|
| `tez/evaluation/src/config.py` | 4 LLaMA models + GPT-OSS judge config |
| `tez/evaluation/src/metrics.py` | LLM-as-Judge metrics (4 metrics) |
| `tez/evaluation/src/judge.py` | Independent GPT-OSS 120B judge |
| `tez/evaluation/src/groq_api.py` | Groq API for MCQ generation |
| `tez/evaluation/scripts/run_evaluation.py` | Main evaluation runner |

---

## Configuration

### Environment Variables (.env)
```
GROQ_API_KEY=gsk_xxx           # Required - from console.groq.com
GOOGLE_CLIENT_ID=xxx           # Required - OAuth
GOOGLE_CLIENT_SECRET=xxx       # Required - OAuth
```

### Key Settings (backend/app/core/config.py)
| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_MODEL` | llama-3.3-70b-versatile | Groq model |
| `EMBEDDING_MODEL` | all-mpnet-base-v2 | SentenceTransformer |
| `EMBEDDING_DIM` | 768 | Embedding dimension |
| `CHUNK_SIZE` | 512 | Tokens per chunk |
| `DEFAULT_TOP_K` | 5 | Chunks to retrieve |
| `SIMILARITY_THRESHOLD` | 0.40 | Min similarity score |
| `MCQ_TEMPERATURE` | 0.3 | LLM temperature |

---

## Development Commands

### Backend
```bash
# From project root
python -m uvicorn backend.app.main:app --reload --port 8000

# First-time setup
python -m backend.scripts.load_dataset
python -m backend.scripts.chunking
python -m backend.scripts.build_index
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Evaluation (Thesis)
```bash
cd tez/evaluation

# Generate questions for all 4 LLaMA models
python scripts/generate_questions.py --condition all --samples 100

# Run evaluation with GPT-OSS 120B judge
python scripts/run_evaluation.py --condition all

# Test single model
python scripts/generate_questions.py --condition llama-3.3-70b-versatile --samples 10
python scripts/run_evaluation.py --condition llama-3.3-70b-versatile --samples 3
```

### Access URLs
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

---

## MCQ Generation Features

- **Difficulty levels**: easy, medium, hard
- **Bloom's taxonomy**: remember, understand, apply, analyze
- **Automatic explanations**: Why the answer is correct
- **Distractor generation**: Plausible wrong answers

---

## Evaluation System (Thesis)

### Model Comparison Experiment
- **4 LLaMA Models**: 3.3-70B, 3.1-8B, LLaMA 4 Maverick, LLaMA 4 Scout
- **Independent Judge**: GPT-OSS 120B (different model family)
- **Blind Judging**: Model names hidden from judge prompts

### Metrics (4 Total)
| Metric | Description | Threshold |
|--------|-------------|-----------|
| `question_quality` | Clarity, answerability | >=0.75 |
| `answer_correctness` | Factual accuracy | >=0.75 |
| `distractor_quality` | Plausibility of wrong options | >=0.70 |
| `answer_relevancy` | Pertinence to question | >=0.75 |

---

## Coding Conventions

### Backend (Python)
- FastAPI with Pydantic v2 models
- Singleton pattern for model caching (embedding_service.py)
- Type hints throughout
- Docstrings for complex functions

### Frontend (TypeScript/React)
- Next.js App Router (not Pages Router)
- React 19 with useOptimistic, useActionState
- Tailwind CSS 4 (no CSS modules)
- Context API for global state (AuthContext, QuizHistoryContext)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/google` | Google OAuth login |
| GET | `/api/auth/me` | Current user |
| POST | `/api/quiz/generate` | Generate MCQs |
| GET | `/api/user/preferences` | User preferences |
| PUT | `/api/user/preferences` | Update preferences |

---

## Notes

- Project uses **Turkish** for some documentation (tez/, kurulum.txt)
- This is an **academic thesis project** - methods are documented for research
- Semantic caching implemented to reduce API costs
- Out-of-domain detection for invalid science queries
- Rate limiting middleware included
- Blind judging eliminates self-evaluation bias

---

## Common Tasks

### Add new LLM model
1. Add model config to `tez/evaluation/src/config.py` (GENERATOR_MODELS dict)
2. Add to `ALL_MODELS` list
3. Run evaluation with `python scripts/generate_questions.py --condition <model-id>`

### Modify chunking strategy
1. Edit `backend/scripts/chunking.py`
2. Re-run: `python -m backend.scripts.chunking`
3. Rebuild index: `python -m backend.scripts.build_index`

### Modify evaluation metrics
1. Edit `tez/evaluation/src/metrics.py`
2. Update `METRICS` dict in `tez/evaluation/src/config.py`
3. Re-run evaluation
