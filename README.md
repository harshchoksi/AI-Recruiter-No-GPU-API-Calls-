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
