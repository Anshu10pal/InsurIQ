"""
Main ingestion pipeline — orchestrates full CSV → PostgreSQL + ChromaDB flow.
Usage: python -m services.ingestion.ingest
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import settings
from database import SessionLocal, init_db
from services.ingestion.csv_loader import load_and_validate_csv, df_to_records
from services.ingestion.narrative_builder import build_claim_narrative
from services.ingestion.embedder import generate_embeddings
from services.ingestion.pg_writer import bulk_upsert_claims
from services.fraud.scoring.rule_engine import evaluate_rules
from services.fraud.scoring.statistical_scorer import compute_statistical_flags
from services.fraud.scoring.risk_calculator import calculate_risk_score
from utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def run_ingestion(data_path: str = None) -> dict:
    start_time = time.time()
    data_path = data_path or settings.data_path
    logger.info("ingestion_started", data_path=data_path)
    logger.info("step_1_initializing_database")
    init_db()
    logger.info("step_2_loading_csv")
    df = load_and_validate_csv(data_path)
    records = df_to_records(df)
    logger.info("csv_loaded", total_records=len(records))
    logger.info("step_3_building_narratives")
    narratives = [build_claim_narrative(record) for record in records]
    logger.info("narratives_built", count=len(narratives))
    logger.info("step_4_computing_fraud_scores")
    fraud_scores, fraud_signals_list, statistical_flags_list = [], [], []
    for record in records:
        signals = evaluate_rules(record)
        stat_flags = compute_statistical_flags(record)
        score = calculate_risk_score(signals, stat_flags, record)
        fraud_scores.append(score)
        fraud_signals_list.append(signals)
        statistical_flags_list.append(stat_flags)
    logger.info("fraud_scores_computed",
                high_risk=sum(1 for s in fraud_scores if s >= 70),
                medium_risk=sum(1 for s in fraud_scores if 40 <= s < 70),
                low_risk=sum(1 for s in fraud_scores if s < 40))
    logger.info("step_5_generating_embeddings")
    embeddings = generate_embeddings(narratives)
    logger.info("embeddings_generated", count=len(embeddings))
    logger.info("step_6_bulk_upsert_to_postgresql")
    db = SessionLocal()
    try:
        total_upserted = bulk_upsert_claims(
            db=db, records=records, narratives=narratives, embeddings=embeddings,
            fraud_scores=fraud_scores, fraud_signals_list=fraud_signals_list,
            statistical_flags_list=statistical_flags_list, batch_size=500,
        )
    finally:
        db.close()
    elapsed = time.time() - start_time
    summary = {"status": "success", "total_records": len(records), "total_upserted": total_upserted,
               "elapsed_seconds": round(elapsed, 2), "fraud_records": int(df["FraudFound_P"].sum()),
               "high_risk_scored": sum(1 for s in fraud_scores if s >= 70)}
    logger.info("ingestion_complete", **summary)
    return summary


if __name__ == "__main__":
    result = run_ingestion()
    print("\n" + "="*50 + "\nINGESTION COMPLETE\n" + "="*50)
    for k, v in result.items():
        print(f"  {k}: {v}")
