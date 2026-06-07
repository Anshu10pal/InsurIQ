"""
Claim data models — SQLAlchemy ORM model and Pydantic schemas.
Embeddings stored in ChromaDB, not PostgreSQL.
Updated: added 10 engineered feature columns, renamed number_of_suppliments -> number_of_supplements
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from database import Base


# ── SQLAlchemy ORM Models ──────────────────────────────────────────────────────

class Claim(Base):
    """Primary claim table — all 33 original fields + 10 engineered features + computed fraud fields."""
    __tablename__ = "claims"

    policy_number = Column(Integer, primary_key=True, index=True)
    month = Column(String(20))
    week_of_month = Column(Integer)
    day_of_week = Column(String(20))
    day_of_week_claimed = Column(String(20))
    month_claimed = Column(String(20))
    week_of_month_claimed = Column(Integer)
    year = Column(Integer)
    make = Column(String(50))
    vehicle_category = Column(String(50))
    vehicle_price = Column(String(50))
    age_of_vehicle = Column(String(50))
    accident_area = Column(String(50))
    fault = Column(String(50))
    policy_type = Column(String(100))
    base_policy = Column(String(50))
    sex = Column(String(20))
    marital_status = Column(String(20))
    age = Column(Integer)
    age_of_policy_holder = Column(String(50))
    deductible = Column(Integer)
    driver_rating = Column(Integer)
    days_policy_accident = Column(String(50))
    days_policy_claim = Column(String(50))
    past_number_of_claims = Column(String(50))
    number_of_supplements = Column(String(50))       # renamed from number_of_suppliments
    address_change_claim = Column(String(50))
    number_of_cars = Column(String(50))
    police_report_filed = Column(String(10))
    witness_present = Column(String(10))
    rep_number = Column(Integer)
    agent_type = Column(String(20))
    fraud_found_p = Column(Integer)
    claim_narrative = Column(Text)
    fraud_risk_score = Column(Integer, default=0)
    fraud_signals = Column(JSON, default=list)
    statistical_flags = Column(JSON, default=list)

    # ── 10 engineered feature columns ──────────────────────────────────────────
    is_weekend = Column(Integer, default=0)              # 1 if accident on Sat/Sun
    no_evidence = Column(Integer, default=0)             # 1 if no police AND no witness
    is_high_value_claim = Column(Integer, default=0)     # 1 if vehicle price >= 60000
    is_new_policy = Column(Integer, default=0)           # 1 if days_policy_accident = 1 to 7
    is_repeat_claimant = Column(Integer, default=0)      # 1 if past_claims in [2 to 4, more than 4]
    has_excess_supplements = Column(Integer, default=0)  # 1 if supplements in [3 to 5, more than 5]
    is_old_high_vehicle = Column(Integer, default=0)     # 1 if age > 7 AND high value
    recent_address_change = Column(Integer, default=0)   # 1 if address change under 6 months
    is_external_agent = Column(Integer, default=0)       # 1 if agent_type = External
    fraud_risk_flags = Column(Integer, default=0)        # count of above flags (0-9)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FeedbackLog(Base):
    """Stores analyst feedback on AI recommendations."""
    __tablename__ = "feedback_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_number = Column(Integer, index=True)
    trace_id = Column(String(100))
    was_correct = Column(Boolean)
    analyst_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class EvalResult(Base):
    """Stores DeepEval evaluation run results."""
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), unique=True)
    faithfulness_score = Column(Float)
    answer_relevance_score = Column(Float)
    context_precision_score = Column(Float)
    llm_judge_score = Column(Float)
    passed = Column(Boolean)
    details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


# ── Pydantic Schemas ───────────────────────────────────────────────────────────

class ClaimBase(BaseModel):
    """Base Pydantic schema for claim data validation."""
    policy_number: int
    month: Optional[str] = None
    week_of_month: Optional[int] = None
    day_of_week: Optional[str] = None
    make: Optional[str] = None
    accident_area: Optional[str] = None
    day_of_week_claimed: Optional[str] = None
    month_claimed: Optional[str] = None
    week_of_month_claimed: Optional[int] = None
    sex: Optional[str] = None
    marital_status: Optional[str] = None
    age: Optional[int] = None
    fault: Optional[str] = None
    policy_type: Optional[str] = None
    vehicle_category: Optional[str] = None
    vehicle_price: Optional[str] = None
    fraud_found_p: Optional[int] = None
    rep_number: Optional[int] = None
    deductible: Optional[int] = None
    driver_rating: Optional[int] = None
    days_policy_accident: Optional[str] = None
    days_policy_claim: Optional[str] = None
    past_number_of_claims: Optional[str] = None
    age_of_vehicle: Optional[str] = None
    age_of_policy_holder: Optional[str] = None
    police_report_filed: Optional[str] = None
    witness_present: Optional[str] = None
    agent_type: Optional[str] = None
    number_of_supplements: Optional[str] = None      # renamed
    address_change_claim: Optional[str] = None
    number_of_cars: Optional[str] = None
    year: Optional[int] = None
    base_policy: Optional[str] = None
    # engineered features
    is_weekend: Optional[int] = None
    no_evidence: Optional[int] = None
    is_high_value_claim: Optional[int] = None
    is_new_policy: Optional[int] = None
    is_repeat_claimant: Optional[int] = None
    has_excess_supplements: Optional[int] = None
    is_old_high_vehicle: Optional[int] = None
    recent_address_change: Optional[int] = None
    is_external_agent: Optional[int] = None
    fraud_risk_flags: Optional[int] = None

    class Config:
        from_attributes = True


class ClaimResponse(ClaimBase):
    """Claim response including computed fraud fields."""
    claim_narrative: Optional[str] = None
    fraud_risk_score: Optional[int] = None
    fraud_signals: Optional[List[str]] = None
    statistical_flags: Optional[List[str]] = None
    created_at: Optional[datetime] = None


class InvestigationRequest(BaseModel):
    """Request schema for claim investigation endpoint."""
    query: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Natural language investigation query"
    )
    filters: Optional[dict] = Field(
        default=None,
        description="Optional metadata filters"
    )
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    use_query_rewriting: bool = Field(
        default=False,
        description=(
            "When True, uses GPT-4o-mini to rewrite the query "
            "into dataset vocabulary before embedding. "
            "Improves semantic matching for natural language queries."
        )
    )


class InvestigationResponse(BaseModel):
    """Full investigation response from the agent pipeline."""
    query: str
    risk_score: int
    risk_level: str
    fraud_signals: List[str]
    statistical_flags: List[str]
    policy_issues: List[str]
    retrieved_claims: List[dict]
    recommendation: str
    confidence: float
    action_steps: List[str]
    trace_id: str
    cache_hit: bool
    rewritten_query: Optional[str] = None
    eval_scores: Optional[dict] = None
    warning: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Feedback submission from analyst."""
    policy_number: int
    trace_id: str
    was_correct: bool
    analyst_notes: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str = "1.0.0"
    database: bool
    redis: bool
