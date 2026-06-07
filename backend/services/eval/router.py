import asyncio
import subprocess
import sys
import uuid
import os
import re
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

_eval_runs: dict = {}

RAG_TESTS = [
    "test_minimum_retrieval_count",
    "test_risk_score_range",
    "test_risk_level_valid",
    "test_fraud_signals_present",
    "test_recommendation_not_empty",
    "test_action_steps_present",
    "test_retrieved_claims_have_fields",
    "test_confidence_range",
    "test_policy_issues_list",
    "test_response_schema",
]

AGENT_TESTS = [
    "test_faithfulness",
    "test_relevance",
    "test_completeness",
    "test_actionability",
    "test_high_risk_detected",
    "test_signals_match_level",
]


def _run_pytest_with_id(run_id: str) -> None:
    eval_dir = os.path.dirname(__file__)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            os.path.join(eval_dir, "test_rag_quality.py"),
            os.path.join(eval_dir, "test_agent_quality.py"),
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
    )

    stdout = result.stdout
    stderr = result.stderr

    tests = []

    # Parse individual test lines
    for line in stdout.splitlines():

        if "::" not in line:
            continue

        status = None

        if " PASSED" in line:
            status = "PASSED"
        elif " FAILED" in line:
            status = "FAILED"
        elif " ERROR" in line:
            status = "ERROR"

        if not status:
            continue

        try:
            test_name = (
                line.split("::")[1]
                .split("[")[0]
                .strip()
            )

            tests.append(
                {
                    "name": test_name,
                    "status": status,
                }
            )

        except Exception:
            pass

    # Fallback if pytest output isn't showing individual tests
    if not tests and result.returncode == 0:
        tests = (
            [{"name": t, "status": "PASSED"} for t in RAG_TESTS]
            + [{"name": t, "status": "PASSED"} for t in AGENT_TESTS]
        )

    passed = sum(
        1 for t in tests
        if t["status"] == "PASSED"
    )

    failed = sum(
        1 for t in tests
        if t["status"] in ("FAILED", "ERROR")
    )

    total = len(tests)

    # Additional fallback from summary line
    if total == 0:
        summary_match = re.search(
            r"(\d+)\s+passed",
            stdout,
            re.IGNORECASE,
        )

        if summary_match:
            passed = int(summary_match.group(1))
            total = passed

    _eval_runs[run_id] = {
        "run_id": run_id,
        "status": "completed",
        "started_at": _eval_runs[run_id].get(
            "started_at",
            ""
        ),
        "completed_at": datetime.utcnow().isoformat(),
        "passed": passed,
        "failed": failed,
        "total": total,
        "pass_rate": round(
            (passed / total) * 100,
            1,
        )
        if total
        else 0,
        "tests": tests,
        "output": (stdout + "\n\n" + stderr)[-5000:],
        "returncode": result.returncode,
    }


@router.post("/run")
async def run_eval():
    run_id = str(uuid.uuid4())

    _eval_runs[run_id] = {
        "run_id": run_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
    }

    async def _task():
        await asyncio.to_thread(
            _run_pytest_with_id,
            run_id,
        )

    asyncio.create_task(_task())

    return {
        "run_id": run_id,
        "status": "running",
        "message": "Eval started in background",
    }


@router.get("/status/{run_id}")
async def eval_status(run_id: str):
    if run_id not in _eval_runs:
        return {"error": "run_id not found"}

    return _eval_runs[run_id]


@router.get("/results")
async def eval_results():
    completed = [
        r
        for r in _eval_runs.values()
        if r.get("status") == "completed"
    ]

    completed.sort(
        key=lambda x: x.get(
            "completed_at",
            ""
        ),
        reverse=True,
    )

    return {
        "runs": completed,
        "total": len(completed),
    }