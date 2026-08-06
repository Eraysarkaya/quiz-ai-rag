# Quiz AI

Quiz AI is a full-stack science quiz generator built as a graduation project. It combines retrieval-augmented generation (RAG), a Groq-hosted language model, semantic caching, authentication, quiz history, and an evaluation pipeline for comparing generated questions.

## Highlights

- Generates multiple-choice science questions by topic and difficulty.
- Grounds generation in a FAISS vector index built from the SciQ dataset.
- Detects out-of-domain requests and reuses semantically similar cached questions.
- Supports email/password and optional Google authentication.
- Saves quiz history, progress, preferences, scores, and explanations.
- Evaluates model outputs with embedding metrics and LLM-as-judge criteria.

## Technology

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Pydantic, SQLite
- **AI/RAG:** Groq, Sentence Transformers, FAISS, SciQ
- **Evaluation:** pandas, scikit-learn, SciPy, Matplotlib, Seaborn

## Architecture

```text
Next.js client
    |
    v
FastAPI routes ──> authentication and SQLite persistence
    |
    v
OOD detector ──> semantic cache ──> FAISS retrieval ──> Groq MCQ generation
                                                     |
                                                     v
                                           validation + explanation
```

The application code lives in `backend/app` and `frontend/src`. Thesis experiments and reproducible evaluation scripts live in `tez/evaluation`.

## Local setup

### 1. Backend

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env            # Windows
# cp .env.example .env            # macOS/Linux
```

Set `GROQ_API_KEY` in `.env`. Google OAuth values are optional for local email/password authentication. Use a unique `JWT_SECRET_KEY` outside development.

Start the API from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

Health check: `http://localhost:8000/api/health`

### 2. Frontend

```bash
cd frontend
npm install
copy .env.example .env.local      # Windows
# cp .env.example .env.local      # macOS/Linux
npm run dev
```

Open `http://localhost:3000`.

## Knowledge base

Processed corpus and FAISS artifacts are included for reproducibility. To rebuild them:

```bash
python backend/scripts/load_dataset.py
python backend/scripts/chunking.py
python backend/scripts/build_index.py
```

## Evaluation

The evaluation workflow compares generated question sets using correctness, faithfulness, retrieval utility, distractor plausibility, and diversity metrics.

```bash
python tez/evaluation/scripts/run_full_experiment.py
```

Generated reports are written under `tez/evaluation/results/reports`.

## Quality checks

```bash
cd frontend
npm run lint
npm run build
```

Backend and evaluation syntax can be checked with:

```bash
python -m compileall backend/app tez/evaluation
python -m unittest discover -s backend/tests -v
```

## Screenshots

![Quiz AI home](docs/screenshots/01-home.png)

![Generated question](docs/screenshots/02-question.png)

![Quiz results](docs/screenshots/03-results.png)

## Security and data

- Never commit `.env` files or API credentials.
- Runtime SQLite databases are local and ignored by Git.
- The generated questions may contain errors and should be verified for high-stakes use.
- Revoke an API key immediately if it is pasted into an issue, commit, screenshot, or chat.

## Project status

This is a portfolio and academic project intended for local demonstration. A hosted deployment is not required to review the code or reproduce the evaluation.

## License

MIT
