"""Planner(OpenAI) -> Executor(Gemini) -> Reviewer(Claude) loop with logging + detection."""
from . import database as db
from .agents import AGENTS
from .llm_clients import call
from .fault_injection import inject
from .failure_detector import detect, score


def run_task(task, live=False, fault="none", fault_rounds=1, max_rounds=3):
    run_id = db.create_run(task, "live" if live else "mock", fault)
    msgs, step, feedback, approved = [], 0, "", False

    def ask(rnd, role, user):
        nonlocal step
        a = AGENTS[role]
        text, lat = call(a["provider"], role, a["system"], user, live)
        step += 1
        m = dict(step=step, round=rnd, agent=a["provider"], role=role, content=text, latency_ms=lat)
        msgs.append(m)
        db.add_message(run_id, m)
        return text

    for rnd in range(1, max_rounds + 1):
        p_user = f"Task: {task}\n" + (f"Reviewer feedback to address: {feedback}" if feedback else "")
        plan = ask(rnd, "planner", p_user)

        handoff = inject(plan, fault) if rnd <= fault_rounds else plan   # fault point
        result = ask(rnd, "executor", f"Task: {task}\nPlan:\n{handoff}")
        verdict = ask(rnd, "reviewer", f"Task: {task}\nExecutor output:\n{result}")

        if verdict.upper().startswith("APPROVED"):
            approved = True
            break
        feedback = verdict

    failures = detect(task, msgs)
    sc = score(failures)
    db.add_failures(run_id, failures)
    db.finish_run(run_id, "approved" if approved else "deadlock", sc)
    return db.get_run(run_id)
