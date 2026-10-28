import os
os.environ["DB_PATH"] = "test.db"
from app.orchestrator import run_task

TASK = "Explain how solar panels work"


def types(run):
    return {f["type"] for f in run["failures"]}


def test_clean_run():
    r = run_task(TASK, fault="none")
    assert r["run"]["status"] == "approved" and r["run"]["score"] == 100


def test_truncate_is_flagged():
    r = run_task(TASK, fault="truncate")
    assert types(r) & {"INSTRUCTION_DROPPED", "EMPTY_OR_TRUNCATED_HANDOFF"}
    assert r["run"]["score"] < 100


def test_contradict_causes_drift():
    assert "TASK_DRIFT" in types(run_task(TASK, fault="contradict"))


def test_role_confusion():
    assert "ROLE_CONFUSION" in types(run_task(TASK, fault="role_confusion"))


def test_permanent_fault_deadlocks():
    r = run_task(TASK, fault="drop", fault_rounds=3)
    assert r["run"]["status"] == "deadlock" and "NO_CONSENSUS_DEADLOCK" in types(r)
