# AI Recruiter — Intelligent Candidate Ranking System

> Replace keyword-filter recruiting with genuine semantic understanding of roles and people.

Built for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  PRE-COMPUTATION (offline)           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Load 100K │→│ Build Texts  │→│   Embed via   │  │
│  │ Candidates│  │  per Cand.   │  │ MiniLM-L6-v2 │  │
│  └──────────┘  └──────────────┘  └──────┬───────┘  │
│                                         │           │
│                          ┌──────────────▼────────┐  │
│                          │ Save: embeddings.npy  │  │
│                          │        jd_embedding   │  │
│                          │        candidate_ids  │  │
│                          └───────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│            RANKING (≤5 min, CPU, no network)        │
│                                                     │
│  ┌────────────┐  Load pre-computed artifacts        │
│  │ Semantic   │  Cosine similarity → all scores     │
│  │ Retrieval  │                                     │
│  └─────┬──────┘                                     │
│        │  ┌─────────────┐                           │
│        ├──│ Career Fit  │  Title + trajectory +     │
│        │  │   Scorer    │  production AI evidence   │
│        │  └─────────────┘                           │
│        │  ┌─────────────┐                           │
│        ├──│ Skill Match │  Required + nice-to-have  │
│        │  │   Scorer    │  + assessment validation  │
│        │  └─────────────┘                           │
│        │  ┌─────────────┐                           │
│        ├──│ Behavioral  │  Response rate, recency,  │
│        │  │   Scorer    │  GitHub, notice period    │
│        │  └─────────────┘                           │
│        │  ┌─────────────┐                           │
│        └──│  Honeypot   │  Impossible profile       │
│           │  Detector   │  detection → hard filter  │
│           └─────────────┘                           │
│                 │                                   │
│        ┌───────▼────────┐                           │
│        │  Hybrid Blend  │  Weighted combination     │
│        │  + Experience  │  of all signals           │
│        │  + Education   │                           │
│        └───────┬────────┘                           │
│                │                                    │
│        ┌───────▼────────┐                           │
│        │   Explainer    │  Template-based reasoning │
│        │   (no LLM)    │  per candidate            │
│        └───────┬────────┘                           │
│                │                                    │
│        ┌───────▼────────┐                           │
│        │  Output CSV    │  Top 100 ranked           │
│        └────────────────┘                           │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Pre-compute embeddings (one-time)
```bash
# Full 100K candidates (~10-15 min on CPU)
python precompute.py

# Or test with a subset first
python precompute.py --limit 1000
```

### 3. Run ranking
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### 4. Validate submission
```bash
python validate_submission.py submission.csv
```

## 📊 Scoring System

The ranking uses a **6-signal hybrid blend**:

| Signal | Weight | What it measures |
|:---|:---:|:---|
| **Career Fit** | 32% | Title relevance, production AI experience, product vs consulting, trajectory |
| **Semantic Similarity** | 18% | Embedding cosine similarity between JD and candidate text |
| **Skill Match** | 18% | Required + nice-to-have skill cluster matching with proficiency weighting |
| **Behavioral** | 17% | Response rate, recency, GitHub, notice period, location alignment |
| **Experience Fit** | 12% | Years of experience alignment with JD's 5-9 year range |
| **Education** | 3% | Field relevance, degree level, institution tier |

### Why Career Fit is weighted highest

The JD is explicit: candidates with AI keywords in their skills list but non-engineering titles (Marketing Manager, Accountant) are traps. Career fit looks at **actual career history** rather than just skill lists to catch this.

### Honeypot Detection

~80 candidates have subtly impossible profiles (expert in 10 skills with 0 months of use, etc.). These are hard-filtered to score 0 to ensure <10% honeypot rate in top 100.

## 🏛️ Architecture Decisions

### Why sentence-transformers instead of OpenAI embeddings?
The ranking step cannot make API calls. `all-MiniLM-L6-v2` (384-dim) runs locally on CPU and is fast enough for 100K candidates (~3 min to embed, <100ms to retrieve).

### Why numpy cosine similarity instead of FAISS?
At 100K × 384 dims (~150MB), numpy matrix multiplication is fast enough (<100ms). FAISS adds complexity without meaningful speed gain at this scale.

### Why template-based reasoning instead of LLM?
No network allowed during ranking. Templates reference specific candidate data (company, title, YoE, skills) to produce varied, honest reasoning that passes Stage 4 manual review.

### Why weighted-average JD embedding?
The JD has different importance levels: "must have embeddings experience" matters more than "nice to have open-source contributions". Weighted embedding captures this priority structure.

## 🛑 Why "CPU only, no API calls"?

This project is meant to simulate a real production recruiting system, not a leaderboard-chasing benchmark. A real company ranking 200K candidates can't afford to make an LLM API call per candidate — that's too slow and too expensive at scale.

If you tried to call GPT-4 or Claude once per candidate across 100,000 profiles, you'd blow past the 5-minute budget even with a fast local model, let alone a network round-trip per call.

So, they're forcing participants to design a system that does the expensive reasoning once, offline (pre-computation, which is allowed to take longer) and then do something cheap and local at ranking time.

### How this project satisfies it:
- Embeddings are precomputed offline in `precompute.py`, using a small local model (`all-MiniLM-L6-v2` — 384 dimensions, runs on CPU, no API key needed). That step is allowed to take 10-15 minutes because it's outside the timed window.
- At ranking time, the code only does things that are fast and local:
  - Loads the already-computed `.npy` embedding files from disk.
  - Does matrix multiplication (numpy cosine similarity) to compare candidates to the job description — no model inference, no network call.
  - Runs a handful of rule-based scoring functions (checking titles, skills, keywords, career-history dates) — plain Python logic, not an LLM.
  - Generates the "reasoning" text for each candidate using string templates that plug in real facts about that candidate (their company, title, years of experience, etc.) — not a call to an LLM to write the explanation.

So in short: "CPU only, no API calls" is the hackathon forcing you to build a lightweight, fast, self-contained ranking system — a small local model plus deterministic logic — instead of just wrapping a call to a big AI model per candidate, which wouldn't scale or fit the time/resource budget.

## ⚠️ Deployment Note

I have not deployed this as it's not efficient to deploy this over free-tier web services due to RAM limitations of those deployment services. Anyone visiting this repo can access my linked profile from my resume to view the demo video, or clone the project to their local computer to try it out!

## 💻 Local Setup & Cloning

To run this project locally, follow these steps:
1. **Clone the repository:**
   ```bash
   git clone https://github.com/harshchoksi/AI-Recruiter-No-GPU-API-Calls-.git
   cd AI-Recruiter-No-GPU-API-Calls-
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the pre-computation and ranking (see the Quick Start section above for details).**

## 📁 Project Structure

```
ai-recruiter/
├── rank.py                    # Main CLI: produces submission.csv
├── precompute.py              # Offline embedding generation
├── config/
│   ├── settings.py            # All tunable parameters
│   └── jd_config.py           # Structured JD requirements
├── pipeline/
│   ├── orchestrator.py        # End-to-end pipeline
│   ├── ingestion/             # Data loading & parsing
│   ├── embedding/             # Sentence-transformers embeddings
│   ├── retrieval/             # Cosine similarity retrieval
│   ├── scoring/               # Career, skill, behavioral, honeypot
│   └── explanation/           # Reasoning generation
├── api/                       # FastAPI endpoints
├── eval/                      # Evaluation harness & metrics
├── tests/                     # Unit tests
└── artifacts/                 # Pre-computed embeddings (gitignored)
```

## 🧪 Testing

```bash
# Unit tests (no model download needed)
pytest tests/unit/ -v

# Evaluation harness (requires pre-computed artifacts)
python -m eval.harness --verbose
```

## 🌐 API (optional)

```bash
uvicorn api.main:app --reload --port 8000
```

Endpoints:
- `GET /health` — system health check
- `POST /rank` — rank candidates against JD
- `POST /explain` — deep-dive on one candidate

## ⚙️ Configuration

All tunable parameters are in `config/settings.py`:
- Scoring weights per signal
- Title relevance tiers
- Honeypot detection thresholds
- Experience range
- Consulting company list

## 📜 License

Built for the Redrob Hackathon.
