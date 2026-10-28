"""Rule-based detector for multi-agent coordination failures.

Taxonomy (type -> severity 1..5):
  EMPTY_OR_TRUNCATED_HANDOFF  3   a message too short to carry instructions
  TASK_DRIFT                  4   output shares almost no keywords with the task
  INSTRUCTION_DROPPED         3   executor skipped planned subtasks
  ROLE_CONFUSION              4   planner/executor answers like the reviewer
  PROTOCOL_VIOLATION          2   reviewer ignored APPROVED/REJECTED format
  REPETITION_LOOP             2   same agent repeats itself almost verbatim
  REVIEW_PING_PONG            3   reviewer rejected 2+ times
  NO_CONSENSUS_DEADLOCK       5   run ended without approval
  AGENT_CRASH                 3   provider API returned an error
"""
import re
import difflib

STOP = {"this", "that", "with", "from", "have", "will", "about", "into", "their",
        "step", "subtasks", "completed", "plan", "revised"}


def kw(text):
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP}


def _f(step, type_, sev, detail):
    return {"step": step, "type": type_, "severity": sev, "detail": detail}


def detect(task, msgs):
    out, tk = [], kw(task)
    verdicts = [m for m in msgs if m["role"] == "reviewer"]

    for m in msgs:
        c, r = m["content"].strip(), m["role"]
        if c.startswith("[AGENT_ERROR]"):
            out.append(_f(m["step"], "AGENT_CRASH", 3, c[:120]))
            continue
        if r in ("planner", "executor"):
            if len(c) < 40:
                out.append(_f(m["step"], "EMPTY_OR_TRUNCATED_HANDOFF", 3,
                              f"{r} produced only {len(c)} characters"))
            elif tk and len(kw(c) & tk) / len(tk) < 0.25:
                out.append(_f(m["step"], "TASK_DRIFT", 4, f"{r} output unrelated to the task"))
            if c.upper().startswith(("APPROVED", "REJECTED")):
                out.append(_f(m["step"], "ROLE_CONFUSION", 4, f"{r} answered like the reviewer"))
        if r == "reviewer" and not c.upper().startswith(("APPROVED", "REJECTED")):
            out.append(_f(m["step"], "PROTOCOL_VIOLATION", 2, "reviewer did not use verdict format"))

    # planner subtasks vs executor coverage, per round
    for rnd in sorted({m["round"] for m in msgs}):
        plan = next((m for m in msgs if m["round"] == rnd and m["role"] == "planner"), None)
        exe = next((m for m in msgs if m["round"] == rnd and m["role"] == "executor"), None)
        if plan and exe:
            subs = re.findall(r"^\d+\.\s*(.+)$", plan["content"], re.M)
            if subs:
                # compare on subtask-specific words (task words appear in every subtask)
                done = sum(1 for s in subs if ((kw(s) - tk) or kw(s)) & kw(exe["content"]))
                if done / len(subs) < 0.6 and len(exe["content"].strip()) >= 40:
                    out.append(_f(exe["step"], "INSTRUCTION_DROPPED", 3,
                                  f"executor covered {done}/{len(subs)} planned subtasks"))

    # repetition
    for role in ("executor",):
        seq = [m for m in msgs if m["role"] == role]
        for a, b in zip(seq, seq[1:]):
            if difflib.SequenceMatcher(None, a["content"], b["content"]).ratio() > 0.9:
                out.append(_f(b["step"], "REPETITION_LOOP", 2, f"{role} repeated previous output"))

    rejects = [v for v in verdicts if v["content"].upper().startswith("REJECTED")]
    if len(rejects) >= 2:
        out.append(_f(rejects[-1]["step"], "REVIEW_PING_PONG", 3, f"{len(rejects)} rejections"))
    if not verdicts or not verdicts[-1]["content"].upper().startswith("APPROVED"):
        out.append(_f(msgs[-1]["step"] if msgs else 0, "NO_CONSENSUS_DEADLOCK", 5,
                      "run finished without reviewer approval"))
    return out


def score(failures):
    return max(0, 100 - 5 * sum(f["severity"] for f in failures))
