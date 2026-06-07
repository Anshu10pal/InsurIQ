# InsurIQ — AI-Powered Insurance Claims Intelligence System

Multi-agent LangGraph application for detecting insurance fraud using hybrid RAG retrieval, deterministic rule engine, and GPT-4o-mini recommendations.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/Anshu10pal/InsurIQ
cd InsurIQ
cp .env.example backend/.env   # fill in API keys

# 2. Start PostgreSQL
docker-compose up postgres -d

# 3. Start backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Run ingestion (once)
python -m services.ingestion.ingest

# 5. Start frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:3000

## Architecture

**4-Agent LangGraph Pipeline:**
1. Retrieval Agent — hybrid ChromaDB + PostgreSQL FTS search with RRF
2. Fraud Analysis Agent — frequency-weighted signal scoring (Part1+2+3 formula)
3. Policy Validation Agent — compliance checks
4. Recommendation Agent — GPT-4o-mini synthesis

**Scoring Formula:**
- Part1 (max 60): FraudRiskFlags-based + signal bonuses
- Part2 (max 20): avg pre-computed score × 0.20
- Part3 (max 15): statistical anomaly rate × 15

## Demo Queries

**HIGH risk:** "suspicious claims no police report external agent urban high vehicle price"
**HIGH risk:** "new policy claims filed within a week of inception"
**LOW risk:** "rural collision police report filed witness present internal agent no prior claims"

## Evaluation

```bash
cd backend && python -m pytest services/eval/test_rag_quality.py services/eval/test_agent_quality.py -v
```
16/16 tests passing — 100% pass rate

## Load Testing

```bash
cd tests/locust
locust -f locustfile.py --host=http://localhost:8000 --users=3 --spawn-rate=1
```

## Stack

Backend: FastAPI + Python 3.12 + PostgreSQL 15 + ChromaDB + LangGraph + Redis (Upstash)
Frontend: React 18 + TypeScript + Tailwind CSS + Recharts
Monitoring: Prometheus (/metrics) + LangSmith tracing
