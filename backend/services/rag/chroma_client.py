"""
ChromaDB client — cosine similarity search with progressive filter relaxation.

Filter strategy:
    1. Try all filters together
    2. If < 3 results, relax least important filters one by one
    3. Priority order: no_evidence > police_report_filed > agent_type
                       > witness_present > is_high_value_claim
                       > is_repeat_claimant > has_excess_supplements
                       > is_new_policy > past_number_of_claims > others
    4. Final fallback: unfiltered search

Updated: renamed number_of_suppliments -> number_of_supplements
         added 9 engineered feature fields to filter support
"""
import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
CHROMA_PATH  = os.getenv(
    "CHROMA_PERSIST_PATH",
    os.path.join(_BACKEND_DIR, "chroma_db")
)
COLLECTION_NAME = "insurance_claims"
_client     = None
_collection = None

# Filter priority — highest priority first
# When relaxing, drop from the END of this list first
FILTER_PRIORITY = [
    "no_evidence",            # combined no-police + no-witness (strongest combined signal)
    "police_report_filed",    # strongest individual fraud signal — keep longest
    "agent_type",             # second most important
    "witness_present",        # third
    "is_external_agent",      # engineered version of agent_type
    "is_high_value_claim",    # high value + suspicious = major flag
    "is_repeat_claimant",     # repeat behaviour
    "has_excess_supplements", # inflated repairs
    "is_new_policy",          # new policy gaming
    "accident_area",          # area filter
    "past_number_of_claims",  # relax early
    "number_of_supplements",  # relax early (renamed)
    "is_weekend",             # relax early
    "recent_address_change",  # relax early
    "address_change_claim",   # relax early
    "base_policy",            # least important
    "fault",                  # least important
]

MIN_RESULTS = 3


def get_chroma_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    try:
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "chroma_collection_ready",
            path=CHROMA_PATH,
            count=_collection.count(),
        )
    except Exception as e:
        logger.error("chroma_init_failed", error=str(e))
        raise
    return _collection


def _build_where_clause(filters: Dict[str, Any]) -> Optional[Dict]:
    """
    Build ChromaDB $where clause from filters dict.
    Supports both string equality and integer equality filters.
    """
    if not filters:
        return None

    # String equality fields (original)
    string_fields = {
        "police_report_filed":   "police_report_filed",
        "witness_present":       "witness_present",
        "agent_type":            "agent_type",
        "accident_area":         "accident_area",
        "base_policy":           "base_policy",
        "past_number_of_claims": "past_number_of_claims",
        "number_of_supplements": "number_of_supplements",   # renamed
        "address_change_claim":  "address_change_claim",
        "fault":                 "fault",
    }

    # Integer equality fields (engineered features)
    int_fields = {
        "no_evidence":            "no_evidence",
        "is_weekend":             "is_weekend",
        "is_high_value_claim":    "is_high_value_claim",
        "is_new_policy":          "is_new_policy",
        "is_repeat_claimant":     "is_repeat_claimant",
        "has_excess_supplements": "has_excess_supplements",
        "is_old_high_vehicle":    "is_old_high_vehicle",
        "recent_address_change":  "recent_address_change",
        "is_external_agent":      "is_external_agent",
    }

    conditions = []

    for key, chroma_field in string_fields.items():
        value = filters.get(key)
        if value is not None and value != "":
            conditions.append({chroma_field: {"$eq": str(value)}})

    for key, chroma_field in int_fields.items():
        value = filters.get(key)
        if value is not None and value != "":
            try:
                conditions.append({chroma_field: {"$eq": int(value)}})
            except (ValueError, TypeError):
                pass

    # fraud_risk_flags minimum threshold
    min_flags = filters.get("fraud_risk_flags_min")
    if min_flags is not None:
        try:
            conditions.append({"fraud_risk_flags": {"$gte": int(min_flags)}})
        except (ValueError, TypeError):
            pass

    # fraud_only special case
    if filters.get("fraud_only"):
        conditions.append({"fraud_found_p": {"$eq": 1}})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


def _try_filtered_search(
    collection,
    query_embedding: List[float],
    filters: Dict[str, Any],
    n_results: int,
) -> tuple:
    """
    Try ChromaDB search with progressively relaxed filters.
    Returns (results, filters_actually_used).
    """
    active_filters = {}
    for field in FILTER_PRIORITY:
        if filters.get(field) is not None and filters.get(field) != "":
            active_filters[field] = filters[field]

    for key, val in filters.items():
        if key not in active_filters and key not in ("fraud_only", "fraud_risk_flags_min") and val is not None and val != "":
            active_filters[key] = val

    if filters.get("fraud_only"):
        active_filters["fraud_only"] = True
    if filters.get("fraud_risk_flags_min") is not None:
        active_filters["fraud_risk_flags_min"] = filters["fraud_risk_flags_min"]

    filter_keys = list(active_filters.keys())

    for n_keep in range(len(filter_keys), 0, -1):
        current_filters = {k: active_filters[k] for k in filter_keys[:n_keep]}
        where = _build_where_clause(current_filters)
        if not where:
            continue

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
                where=where,
            )
            result_count = len(results["ids"][0]) if results["ids"] else 0

            if result_count >= MIN_RESULTS:
                if n_keep < len(filter_keys):
                    logger.info(
                        "chroma_filters_relaxed",
                        kept=list(current_filters.keys()),
                        dropped=filter_keys[n_keep:],
                        results_found=result_count,
                    )
                else:
                    logger.info(
                        "chroma_filters_applied",
                        filters=current_filters,
                        results_found=result_count,
                    )
                return results, current_filters

            logger.info(
                "chroma_filter_insufficient_results",
                filters_tried=list(current_filters.keys()),
                results_found=result_count,
                relaxing=True,
            )

        except Exception as e:
            logger.warning(
                "chroma_filter_error_relaxing",
                error=str(e),
                filters_tried=list(current_filters.keys()),
            )
            continue

    logger.warning(
        "chroma_all_filters_exhausted_unfiltered",
        original_filters=list(active_filters.keys()),
    )
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return results, {}


def upsert_embeddings(
    policy_numbers: List[int],
    embeddings: List[List[float]],
    narratives: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """Upsert claim embeddings into ChromaDB."""
    collection = get_chroma_collection()
    ids = [str(pn) for pn in policy_numbers]

    clean_metadatas = []
    for meta in metadatas:
        clean = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif v is None:
                clean[k] = ""
            else:
                clean[k] = str(v)
        clean_metadatas.append(clean)

    batch_size = 500
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=narratives[i:i+batch_size],
            metadatas=clean_metadatas[i:i+batch_size],
        )
        logger.info(
            "chroma_batch_upserted",
            batch_start=i,
            batch_size=min(batch_size, len(ids) - i),
        )
    logger.info("chroma_upsert_complete", total=len(ids))


def vector_search(
    query_embedding: List[float],
    top_k: int = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Perform cosine similarity search with progressive filter relaxation.
    """
    top_k      = top_k or settings.rag_top_k_vector
    collection = get_chroma_collection()
    n_results  = min(top_k, collection.count() or 1)

    try:
        if filters:
            results, used_filters = _try_filtered_search(
                collection, query_embedding, filters, n_results
            )
        else:
            results      = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
            used_filters = {}

        claims = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata   = results["metadatas"][0][i] if results["metadatas"] else {}
                distance   = results["distances"][0][i] if results["distances"] else 1.0
                similarity = 1 - distance

                claim = {
                    "policy_number":  int(doc_id),
                    "claim_narrative": results["documents"][0][i] if results["documents"] else "",
                    "similarity_score": round(similarity, 4),
                    **metadata,
                }

                # Convert int fields
                for int_field in [
                    "fraud_found_p", "fraud_risk_score",
                    "is_weekend", "no_evidence", "is_high_value_claim",
                    "is_new_policy", "is_repeat_claimant", "has_excess_supplements",
                    "is_old_high_vehicle", "recent_address_change",
                    "is_external_agent", "fraud_risk_flags",
                ]:
                    if int_field in claim:
                        try:
                            claim[int_field] = int(claim[int_field])
                        except (ValueError, TypeError):
                            claim[int_field] = 0

                if "fraud_signals" in claim:
                    try:
                        claim["fraud_signals"] = json.loads(claim["fraud_signals"])
                    except Exception:
                        claim["fraud_signals"] = []

                claims.append(claim)

        logger.info(
            "chroma_search_complete",
            results=len(claims),
            filters_requested=list(filters.keys()) if filters else [],
            filters_used=list(used_filters.keys()) if used_filters else [],
        )
        return claims

    except Exception as e:
        logger.error("chroma_search_failed", error=str(e))
        return []


def get_collection_count() -> int:
    """Return number of documents in ChromaDB collection."""
    try:
        return get_chroma_collection().count()
    except Exception:
        return 0
