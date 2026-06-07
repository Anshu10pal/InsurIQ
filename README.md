# InsurIQ — AI-Powered Insurance Fraud Detection System

<div align="center">

![InsurIQ Banner](https://img.shields.io/badge/InsurIQ-AI%20Fraud%20Detection-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-orange?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-16%2F16%20passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**A production-grade multi-agent AI system for real-time insurance fraud detection.**  
Built as a capstone project at Prodapt using LangGraph, FastAPI, ChromaDB, and GPT-4o-mini.

[Live Demo](#demo-queries) · [Architecture](#architecture) · [API Docs](#api-reference) · [Evaluation](#evaluation)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Data Ingestion](#data-ingestion)
  - [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
  - [Ingestion Pipeline](#ingestion-pipeline)
  - [Retrieval Pipeline](#retrieval-pipeline)
  - [4-Agent LangGraph Pipeline](#4-agent-langgraph-pipeline)
  - [Fraud Scoring Formula](#fraud-scoring-formula)
  - [Hybrid RAG Retrieval](#hybrid-rag-retrieval)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [Evaluation](#evaluation)
- [Load Testing](#load-testing)
- [Demo Queries](#demo-queries)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)

---

## Overview

InsurIQ indexes **15,420 historical insurance claims** and provides real-time fraud risk scoring through natural language investigation queries. An investigator types a query describing a claim pattern — the system retrieves the 5 most similar historical claims, runs them through a 4-agent AI pipeline, and returns a fraud risk score (0–100), the signals that triggered it, a policy analysis, and actionable recommendations.

The system is designed for production use with Redis caching (cache hit ~1.4s vs cold ~2.3s), Prometheus metrics, LangSmith tracing, and a full evaluation suite (16/16 tests passing).

---

## Features

| Feature | Details |
|---|---|
| **Natural language queries** | Investigators describe patterns in plain English |
| **4-agent AI pipeline** | Retrieval → Fraud analysis → Policy check → LLM recommendation |
| **Hybrid RAG search** | ChromaDB vector search + PostgreSQL FTS merged via RRF |
| **Risk scoring** | 0–100 score with 15 weighted fraud signals + Z-score anomaly detection |
| **Redis caching** | Identical queries cached for 6 hours — prevents redundant pipeline runs |
| **Animated risk ring** | Score animates 0→final on the investigation page |
| **Claim detail drawer** | Click any retrieved claim to expand all 40+ fields |
| **Score history** | Last 5 queries stored in localStorage |
| **PDF export** | Download investigation report as .txt |
| **Dashboard** | 8 Recharts charts — fraud by area, vehicle, agent, day, policy duration, signals, year trend, high risk table |
| **Score claim** | Rule-engine form for scoring a new claim without a query |
| **Evaluation page** | 16-test suite with animated speedometers for Precision, Recall, Faithfulness, Relevance |
| **LangSmith tracing** | Full trace visibility for every agent run |
| **Prometheus metrics** | `/metrics` endpoint for monitoring |
| **Load tested** | Locust: 5% failure rate at 3 concurrent users |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Frontend  (React 18 + TypeScript + Vite)       │
│  Investigation │ Dashboard │ Score claim │ Evaluation    │
└────────────────────────┬────────────────────────────────┘
                         │  HTTP / Axios
┌────────────────────────▼────────────────────────────────┐
│         FastAPI gateway  (port 8000)                     │
│  Input guard · Intent detector · HyDE rewriter           │
│  Output guard · Prometheus /metrics                      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Upstash Redis cache                         │
│  Hit → return cached result (~1.4s)                      │
│  Miss → continue to agents                               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│         LangGraph StateGraph — 4-agent pipeline          │
│                                                          │
│  Agent 1: Retrieval    Agent 2: Fraud scorer             │
│  Agent 3: Policy check Agent 4: LLM recommendation       │
└───────────┬────────────────────────────┬────────────────┘
            │                            │
┌───────────▼──────────┐    ┌────────────▼───────────────┐
│  Hybrid RAG retrieval │    │  LLM gateway               │
│  ChromaDB (vectors)   │    │  keygateway.arshnivlabs    │
│  PostgreSQL FTS        │    │  GPT-4o-mini · 500 tok     │
│  RRF merger           │    └────────────────────────────┘
└───────────┬──────────┘
            │
┌───────────▼──────────────────────────────────────────────┐
│  Data stores                                              │
│  PostgreSQL 15 (15,420 claims) · ChromaDB (15,420 vectors)│
│  Upstash Redis (pre-warmed cache)                         │
└──────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10 | Runtime |
| FastAPI | 0.111 | Web framework + API gateway |
| LangGraph | 0.1.5 | Multi-agent StateGraph orchestration |
| LangChain | 0.2.3 | LLM abstractions |
| OpenAI SDK | 1.30 | GPT-4o-mini via custom gateway |
| ChromaDB | 0.5.0 | Vector store (cosine similarity) |
| PostgreSQL | 15 | Claims database + full-text search |
| SQLAlchemy | 2.0 | ORM + session management |
| psycopg2 | 2.9.9 | Direct PostgreSQL access (dashboard) |
| Redis | 5.0.4 | Upstash cache client |
| Tenacity | 9.1.4 | Retry decorator (fail-fast: 1 attempt) |
| LangSmith | 0.1.75 | Agent trace observability |
| Prometheus | 6.1.0 | Metrics instrumentation |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.3 | UI framework |
| TypeScript | 5.2 | Type safety |
| Vite | 5.3 | Build tool + dev server |
| Tailwind CSS | 3.4 | Utility-first styling |
| Recharts | 2.12 | Dashboard charts |
| Axios | 1.7 | HTTP client |
| React Router | 6.23 | Client-side routing |
| lucide-react | 0.383 | Icons |

### Evaluation & Testing
| Technology | Purpose |
|---|---|
| pytest | Test runner |
| DeepEval | LLM-as-judge evaluation framework |
| Locust | Load testing |

---

## Project Structure

```
InsurIQ/
├── backend/
│   ├── main.py                          # FastAPI app, all routers registered
│   ├── database.py                      # SQLAlchemy engine + session factory
│   ├── config.py                        # Pydantic settings (reads .env)
│   ├── requirements.txt                 # All pip dependencies
│   ├── .env.template                    # Environment variable template
│   ├── models/
│   │   └── claim.py                     # SQLAlchemy + Pydantic models
│   ├── services/
│   │   ├── agent/
│   │   │   ├── router.py                # /investigate + /feedback endpoints
│   │   │   ├── graph/
│   │   │   │   ├── pipeline.py          # LangGraph StateGraph definition
│   │   │   │   ├── state.py             # ClaimInvestigationState TypedDict
│   │   │   │   ├── retrieval_agent.py   # Agent 1: hybrid search
│   │   │   │   ├── fraud_agent.py       # Agent 2: signal scoring
│   │   │   │   ├── policy_agent.py      # Agent 3: policy rule engine
│   │   │   │   └── recommendation_agent.py  # Agent 4: GPT-4o-mini
│   │   │   ├── guardrails/
│   │   │   │   ├── input_guard.py       # Query validation + sanitisation
│   │   │   │   ├── output_guard.py      # Response schema validation
│   │   │   │   ├── query_intent_detector.py  # Metadata filter extraction
│   │   │   │   └── query_rewriter.py    # HyDE query rewriting
│   │   │   └── tools/
│   │   │       └── cache_tool.py        # Redis cache (reads config.settings)
│   │   ├── fraud/
│   │   │   ├── router.py                # /score-new-claim endpoint
│   │   │   └── scoring/
│   │   │       ├── signal_definitions.py   # 15 signals + weights
│   │   │       ├── risk_calculator.py      # Rule + stat + base rate formula
│   │   │       └── statistical_scorer.py   # Z-score anomaly detection
│   │   ├── rag/
│   │   │   ├── chroma_client.py         # ChromaDB with progressive filter relaxation
│   │   │   ├── fts_client.py            # PostgreSQL FTS (fts_search function)
│   │   │   ├── rrf_merger.py            # Reciprocal Rank Fusion
│   │   │   └── score_reranker.py        # RRF 80% + fraud score 20%
│   │   ├── ingestion/
│   │   │   ├── ingest.py                # Main ingestion entry point
│   │   │   ├── csv_loader.py            # CSV parsing + validation
│   │   │   ├── narrative_builder.py     # Enriched text per claim
│   │   │   ├── embedder.py              # OpenAI embeddings, batch 100
│   │   │   ├── pg_writer.py             # Bulk upsert to PostgreSQL
│   │   │   └── router.py                # /ingestion endpoints
│   │   ├── eval/
│   │   │   ├── router.py                # /run, /status, /results endpoints
│   │   │   ├── test_rag_quality.py      # 10 structural tests
│   │   │   ├── test_agent_quality.py    # 6 LLM-as-judge tests
│   │   │   └── golden_dataset.json      # 20 hand-labelled test cases
│   │   └── dashboard/
│   │       ├── __init__.py
│   │       └── router.py                # 8 chart queries (psycopg2 direct)
│   └── utils/
│       ├── logging.py                   # Structured logging (structlog)
│       ├── security.py                  # SHA-256 cache key hashing
│       └── resilience.py                # Tenacity retry decorators
├── frontend/
│   ├── src/
│   │   ├── App.tsx                      # React Router setup
│   │   ├── main.tsx                     # React entry point
│   │   ├── index.css                    # Tailwind + shimmer animation
│   │   ├── pages/
│   │   │   ├── InvestigationPage.tsx    # Main investigation UI
│   │   │   ├── DashboardPage.tsx        # Analytics dashboard
│   │   │   ├── ScoreClaimPage.tsx       # Manual claim scoring
│   │   │   └── EvalPage.tsx             # Evaluation suite UI
│   │   ├── components/
│   │   │   └── NavBar.tsx               # Shared navigation
│   │   ├── hooks/
│   │   │   └── useInvestigation.ts      # Investigation state management
│   │   └── api/
│   │       └── client.ts                # All API endpoint calls
│   ├── vite.config.ts                   # Dev proxy: /api → :8000
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts               # Gold/black premium theme
│   ├── postcss.config.js
│   └── index.html                       # Google Fonts entry
├── tests/
│   └── locust/
│       └── locustfile.py                # Load test: 2 user classes
├── Data/
│   └── fraud_oracle_fixed.csv           # Source data (excluded from git)
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Use `python3` on Ubuntu |
| Node.js | 18+ LTS | For frontend |
| PostgreSQL | 15 | Local instance |
| Git | Any | |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Anshu10pal/InsurIQ.git
cd InsurIQ

# 2. Install backend dependencies
cd backend
pip3 install -r requirements.txt --user

# 3. Install frontend dependencies
cd ../frontend
npm install
```

### Environment Variables

Copy the template and fill in real values:

```bash
cp backend/.env.template backend/.env
```

```dotenv
# PostgreSQL
DATABASE_URL=postgresql://insuriq_user:root123@localhost:5432/insuriq

# OpenAI-compatible gateway
# No spaces around = · lowercase /v1 suffix · 500 token limit per call
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://keygateway.arshnivlabs.com/v1
OPENAI_MAX_TOKENS=500

# ChromaDB
CHROMA_PERSIST_PATH=./chroma_db

# LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=InsurIQ
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Upstash Redis
# No spaces around = · no quotes · must end with :6379
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_HOST.upstash.io:6379
```

> **Important:** Never commit `.env` to git. It is in `.gitignore`.

### Database Setup

```bash
# Create PostgreSQL user and database
sudo -u postgres psql -c "CREATE USER insuriq_user WITH PASSWORD 'root123';"
sudo -u postgres psql -c "CREATE DATABASE insuriq OWNER insuriq_user;"

# Create the claims table
sudo -u postgres psql -d insuriq << 'SQL'
CREATE TABLE IF NOT EXISTS claims (
    id                     SERIAL PRIMARY KEY,
    policy_number          INTEGER UNIQUE,
    month                  VARCHAR(20),
    week_of_month          INTEGER,
    day_of_week            VARCHAR(20),
    day_of_week_claimed    VARCHAR(20),
    month_claimed          VARCHAR(20),
    week_of_month_claimed  INTEGER,
    year                   INTEGER,
    make                   VARCHAR(50),
    vehicle_category       VARCHAR(50),
    vehicle_price          VARCHAR(50),
    age_of_vehicle         VARCHAR(50),
    accident_area          VARCHAR(50),
    fault                  VARCHAR(50),
    policy_type            VARCHAR(100),
    base_policy            VARCHAR(50),
    sex                    VARCHAR(20),
    marital_status         VARCHAR(20),
    age                    INTEGER,
    age_of_policy_holder   VARCHAR(50),
    deductible             INTEGER,
    driver_rating          INTEGER,
    days_policy_accident   VARCHAR(50),
    days_policy_claim      VARCHAR(50),
    past_number_of_claims  VARCHAR(50),
    number_of_supplements  VARCHAR(50),
    address_change_claim   VARCHAR(50),
    number_of_cars         VARCHAR(50),
    police_report_filed    VARCHAR(10),
    witness_present        VARCHAR(10),
    rep_number             INTEGER,
    agent_type             VARCHAR(50),
    fraud_found_p          INTEGER,
    claim_narrative        TEXT,
    fraud_risk_score       INTEGER DEFAULT 0,
    fraud_signals          JSON,
    statistical_flags      JSON,
    narrative              TEXT,
    search_vector          TSVECTOR,
    is_weekend             INTEGER DEFAULT 0,
    no_evidence            INTEGER DEFAULT 0,
    is_high_value_claim    INTEGER DEFAULT 0,
    is_new_policy          INTEGER DEFAULT 0,
    is_repeat_claimant     INTEGER DEFAULT 0,
    has_excess_supplements INTEGER DEFAULT 0,
    is_old_high_vehicle    INTEGER DEFAULT 0,
    recent_address_change  INTEGER DEFAULT 0,
    is_external_agent      INTEGER DEFAULT 0,
    fraud_risk_flags       INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_claims_fraud_risk_score ON claims(fraud_risk_score);
CREATE INDEX IF NOT EXISTS idx_claims_fraud_found      ON claims(fraud_found_p);
CREATE INDEX IF NOT EXISTS idx_claims_search_vector    ON claims USING GIN(search_vector);
GRANT ALL PRIVILEGES ON TABLE claims TO insuriq_user;
GRANT USAGE, SELECT ON SEQUENCE claims_id_seq TO insuriq_user;
SQL
```

### Data Ingestion

Place `fraud_oracle_fixed.csv` in `Data/` and run:

```bash
cd backend
python3 -m services.ingestion.ingest \
  --data-path /path/to/InsurIQ/Data/fraud_oracle_fixed.csv
```

This runs in ~15 minutes and:
1. Loads and validates 15,420 rows
2. Builds enriched narrative text per claim
3. Generates OpenAI embeddings in batches of 100
4. Computes fraud pre-scores (15 rules + Z-score)
5. Writes to PostgreSQL and ChromaDB

Verify ingestion:

```bash
# PostgreSQL
sudo -u postgres psql -d insuriq -c "SELECT COUNT(*) FROM claims;"

# ChromaDB
cd backend
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='./chroma_db')
print('Vectors:', c.get_collection('insurance_claims').count())
"
```

### Running the Application

```bash
# Terminal 1 — backend
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Prometheus metrics | http://localhost:8000/metrics |

---

## How It Works

### Ingestion Pipeline

```
fraud_oracle_fixed.csv
        ↓
  Narrative builder      ← enriched text paragraph per claim
        ↓
    Embedder             ← text-embedding-3-small · batch 100
        ↓
  Fraud pre-scorer       ← 15 signal rules + Z-score statistics
        ↓
  ┌─────────────┐   ┌──────────────────┐
  │ PostgreSQL  │   │    ChromaDB       │
  │ 15,420 rows │   │ 15,420 vectors   │
  └─────────────┘   └──────────────────┘
```

### Retrieval Pipeline

```
User query (natural language)
        ↓
FastAPI guardrails     ← intent detection + HyDE rewrite
        ↓
Redis cache check      ← hit → return in ~1.4s
        ↓ (miss)
LangGraph agents       ← 4-agent StateGraph
        ↓
Result + cache write   ← skip if risk_score = 0 (poison prevention)
        ↓
Response to frontend
```

### 4-Agent LangGraph Pipeline

**Agent 1 — Retrieval**
- Embeds the (rewritten) query using `text-embedding-3-small`
- Searches ChromaDB for the top-20 most similar claims by cosine similarity
- Searches PostgreSQL FTS using `ts_vector` (falls back to `ILIKE`)
- Merges both result sets using Reciprocal Rank Fusion
- Re-ranks by 80% RRF score + 20% pre-computed fraud score
- Returns top 5 claims

**Agent 2 — Fraud scorer**
- Reads the `fraud_signals` JSON for each of the 5 claims
- Computes signal frequency ratios (how many of 5 claims show each signal)
- Part 1: `Σ signal_weight × frequency_ratio` + combination bonuses (max 60)
- Part 2: `avg(fraud_risk_score) / 100 × 20` (max 20)
- Part 3: `anomaly_claims / 5 × 15` (max 15)
- Applies confirmed-fraud floor boost: ≥80% confirmed → score ≥70
- Returns final score 0–100 and risk level (LOW / MEDIUM / HIGH)

**Agent 3 — Policy checker**
- Pure Python rule engine — no API calls, always runs
- Checks policy duration, deductible patterns, coverage flags
- Returns list of policy issues found

**Agent 4 — Recommender**
- Calls GPT-4o-mini via gateway (500 token limit)
- Generates investigation recommendation + action steps
- Falls back to template-based response if API is unavailable

### Fraud Scoring Formula

#### Stage 1 — Ingestion pre-score (stored in DB)

```
pre_score = rule_score + stat_score + base_rate_score

rule_score      = Σ signal_weights for triggered signals     (max 60)
stat_score      = Σ Z-score contributions for anomalies      (max 30)
base_rate_score = historical fraud rate for this profile     (max 10)

Z-score formula:
  z = (x - μ) / σ
  contribution = min(10, max(0, (z - 2.0) × 5))
  Applied to: vehicle_price, past_claims, supplements, age_of_policy_holder
```

#### Stage 2 — Query-time agent score

```
final_score = Part1 + Part2 + Part3 + floor_boost

Part1 = Σ (signal_weight × freq_ratio) + combination_bonuses   (max 60)
Part2 = avg(fraud_risk_score of 5 claims) / 100 × 20           (max 20)
Part3 = (claims_with_anomalies / 5) × 15                       (max 15)

Floor boost:
  confirmed_fraud_rate ≥ 80% → score = max(score, 70)
  confirmed_fraud_rate ≥ 60% → score = max(score, 55)

Risk levels:  0–39 = LOW  ·  40–69 = MEDIUM  ·  70–100 = HIGH
```

#### 15 Fraud Signals and Weights

| Signal | Weight | Trigger condition |
|---|---|---|
| HIGH_AMOUNT_NO_POLICE_REPORT | 12 | No police + vehicle > $69k |
| NEW_POLICY_QUICK_CLAIM | 10 | Days policy < 8 |
| HIGH_PRIOR_CLAIMS | 10 | Past claims > 1 |
| REPEATED_CLAIM_PATTERN | 10 | Repeat claimant flag |
| RAPID_CLAIM_FILING | 9 | Very short claim-to-incident gap |
| NEW_POLICY_SHORT_DURATION | 9 | Policy age 1–7 days |
| MULTIPLE_ADDRESS_CHANGES | 8 | Address changed near claim date |
| EXTERNAL_AGENT_HIGH_CLAIM | 8 | External agent + high value |
| NO_WITNESS_MULTI_CAR | 8 | No witness + multiple cars |
| OLD_VEHICLE_HIGH_PRICE | 7 | Aged vehicle with high claimed value |
| EXCESS_SUPPLEMENTS | 7 | Supplements > 2 |
| POLICY_HOLDER_AT_FAULT | 6 | Policyholder listed at fault |
| WEEKEND_NO_WITNESS | 6 | Weekend claim + no witness |
| URBAN_NO_EVIDENCE | 6 | Urban + no police + no witness |
| HIGH_DRIVER_RATING | 5 | High driver rating score |

### Hybrid RAG Retrieval

```
Vector search (ChromaDB)    Full-text search (PostgreSQL)
         ↓                              ↓
   rank positions              rank positions
         ↓                              ↓
         └──────────────┬───────────────┘
                        ↓
              Reciprocal Rank Fusion
              RRF = Σ 1 / (k + rank)  where k=60
                        ↓
              Score reranker
              final = 0.8 × RRF_score + 0.2 × (fraud_risk_score / 100)
                        ↓
                    Top 5 claims
```

---

## API Reference

### Investigation

```http
POST /api/v1/claims/investigate
Content-Type: application/json

{
  "query": "suspicious claims no police report external agent urban area",
  "filters": {},
  "use_query_rewriting": true
}
```

**Response:**
```json
{
  "risk_score": 92,
  "risk_level": "HIGH",
  "fraud_signals": ["HIGH_AMOUNT_NO_POLICE_REPORT", "EXTERNAL_AGENT_HIGH_CLAIM"],
  "retrieved_claims": [...],
  "recommendation": "Immediate investigation recommended...",
  "action_steps": ["Obtain police report", "Interview claimant"],
  "confidence": 0.95,
  "policy_issues": [],
  "cache_hit": false,
  "trace_id": "uuid"
}
```

### Dashboard

```http
GET /api/v1/dashboard/stats
```

Returns 8 chart datasets: fraud by area, vehicle, agent type, day of week, policy duration, top fraud signals, claims by year, high-risk claims table.

### Score New Claim

```http
POST /api/v1/fraud/score-new-claim
Content-Type: application/json

{
  "months_as_customer": 6,
  "age_of_policy_holder": 28,
  "vehicle_claim_amount": 85000,
  "police_report_filed": "NO",
  "witness_present": "NO",
  "agent_type": "External",
  "accident_area": "Urban",
  "days_policy_accident": "1 to 7",
  "day_of_week": "Saturday",
  "past_number_of_claims": 2,
  "number_of_supplements": 3
}
```

### Evaluation

```http
POST /api/v1/eval/run          # Start eval in background
GET  /api/v1/eval/status/{id}  # Poll status every 4s
GET  /api/v1/eval/results      # All completed runs
```

### Health & Metrics

```http
GET /health    # {"status": "ok", "service": "InsurIQ"}
GET /metrics   # Prometheus metrics
```

---

## Frontend Pages

### Investigation page
Natural language query input with animated risk ring (0→score animation), loading skeleton, claim detail drawer, query intelligence charts, score history (last 5 in localStorage), and PDF export.

### Dashboard page
8 charts powered by Recharts:
- Fraud rate by accident area (bar)
- Risk distribution (pie)
- Fraud by agent type (horizontal bar)
- Fraud by day of week — weekends highlighted red
- Fraud by vehicle category
- Fraud by policy duration (colour coded)
- Top fraud signals (horizontal bar)
- Claims by year (dual-axis line + bar)
- High-risk claims table with score progress bars

### Score claim page
14-field form for scoring a new claim through the deterministic rule engine without running the AI pipeline. Includes a Clean preset (~5–15) and Suspicious preset (~85–95).

### Evaluation page
Animated speedometers for Precision, Recall, Faithfulness, Relevance. Per-test results for all 16 tests with PASSED/FAILED indicators. Polls backend every 4 seconds while eval is running.

---

## Evaluation

The evaluation suite runs 16 tests against the live API using a golden dataset of 20 hand-labelled cases. Only the first case is used per run (~2–3 minutes).

### RAG quality tests (10)

| Test | What it checks |
|---|---|
| `test_minimum_retrieval_count` | At least 3 claims returned |
| `test_risk_score_range` | Score between 0 and 100 |
| `test_risk_level_valid` | Level is HIGH, MEDIUM, or LOW |
| `test_fraud_signals_present` | At least 1 signal for HIGH queries |
| `test_recommendation_not_empty` | Recommendation > 20 characters |
| `test_action_steps_present` | At least 1 action step |
| `test_retrieved_claims_have_fields` | Claims have required fields |
| `test_confidence_range` | Confidence between 0.0 and 1.0 |
| `test_policy_issues_list` | policy_issues is a list |
| `test_response_schema` | All required keys present |

### Agent quality tests (6 — LLM-as-judge)

| Test | Threshold |
|---|---|
| `test_faithfulness` | ≥ 0.7 |
| `test_relevance` | ≥ 0.7 |
| `test_completeness` | ≥ 0.7 |
| `test_actionability` | ≥ 0.7 |
| `test_high_risk_detected` | risk_level = HIGH + score ≥ expected_min |
| `test_signals_match_level` | HIGH → ≥ 3 signals |

### Run evaluation manually

```bash
cd backend
python3 -m pytest services/eval/test_rag_quality.py \
                   services/eval/test_agent_quality.py -v
```

### Current results

```
16/16 tests PASSING — 100% pass rate
RAG quality:    10/10
Agent quality:   6/6
```

---

## Load Testing

```bash
cd InsurIQ
locust -f tests/locust/locustfile.py --host http://localhost:8000
```

Open Locust UI at http://localhost:8089

### Results at 3 concurrent users

| Endpoint | Avg response | Notes |
|---|---|---|
| `GET /health` | 2ms | ✅ |
| `GET /api/v1/dashboard/stats` | 55ms | ✅ |
| `POST /api/v1/claims/investigate` | ~1.4s cached / ~2.3s cold | ✅ |
| Overall failure rate | 5% | ✅ |

---

## Demo Queries

### HIGH risk (~70–95)

```
suspicious claims no police report external agent urban high vehicle price
new policy claims filed within a week of inception
multiple prior claims address changes near claim no witnesses
```

### MEDIUM risk (~40–65)

```
urban collision external agent no police report but witness present
```

### LOW risk (~8–25)

```
rural collision police report filed witness present internal agent no prior claims
```

### Score claim presets

- **Clean preset** → ~5–15 LOW
- **Suspicious preset** → ~85–95 HIGH

---

## Known Limitations

| Limitation | Details |
|---|---|
| **API quota** | OpenAI gateway resets daily — agent scores may be lower when quota is exhausted (template fallback activates) |
| **Streaming** | Backend SSE endpoint is built but frontend uses axios (non-streaming) |
| **Single test case** | Evaluation uses `GOLDEN_DATASET[:1]` to keep runtime under 3 minutes — extend to more cases for comprehensive testing |
| **Cache scope** | Redis cache uses query text as key — minor query variations miss the cache |
| **ChromaDB filters** | Binary feature fields (is_repeat_claimant etc.) are stored as metadata but progressive filter relaxation may drop them if results are insufficient |
| **Token limit** | GPT-4o-mini gateway enforces a 500-token limit per call — long queries may get truncated recommendations |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test: `python3 -m pytest services/eval/ -v`
4. Commit: `git commit -m "feat: describe your change"`
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

---

## Acknowledgements

Built as a capstone project at **Prodapt** by **Anshuman Pal**.

Dataset: `fraud_oracle.csv` — Auto insurance claims fraud dataset.

---

<div align="center">
<sub>InsurIQ · AI-Powered Insurance Fraud Detection · Prodapt Capstone 2026</sub>
</div>
