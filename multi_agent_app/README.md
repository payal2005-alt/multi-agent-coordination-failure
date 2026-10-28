# Multi-Agent Coordination Failure Lab

Final-year project: a framework that **orchestrates multiple LLM agents, injects faults, detects
coordination failures, and scores how well the agents cooperate.**

## 1. Problem statement
Multi-agent LLM systems fail in ways single models do not: lost handoffs, contradictory
instructions, role confusion, infinite review loops. These failures are rarely logged or measured.
This project makes them observable, reproducible and quantifiable.

## 2. Architecture
```
Streamlit UI --REST--> FastAPI --> Orchestrator --> Planner  (OpenAI)
                                        |      \-> Executor (Gemini)
                                        |       \> Reviewer (Claude)
                                        |
                      Fault Injector (planner->executor handoff)
                                        |
                  SQLite <-- Failure Detector + Scoring
```

## 3. Failure taxonomy
| Type | Severity | Meaning |
|---|---|---|
| EMPTY_OR_TRUNCATED_HANDOFF | 3 | message too short to be useful |
| TASK_DRIFT | 4 | output unrelated to the task |
| INSTRUCTION_DROPPED | 3 | executor skipped planned subtasks |
| ROLE_CONFUSION | 4 | agent answers in another agent's role |
| PROTOCOL_VIOLATION | 2 | reviewer broke APPROVED/REJECTED format |
| REPETITION_LOOP | 2 | near-identical repeated output |
| REVIEW_PING_PONG | 3 | 2+ rejections |
| NO_CONSENSUS_DEADLOCK | 5 | ended without approval |
| AGENT_CRASH | 3 | API error |

Score = `max(0, 100 - 5 * sum(severity))`

## 4. Fault injection modes
`drop`, `truncate`, `contradict`, `role_confusion` (+ `none` as baseline).

## 5. Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # add keys only for live mode
uvicorn app.main:app --reload                          # terminal 1  -> http://127.0.0.1:8000/docs
streamlit run frontend/streamlit_app.py                # terminal 2
pytest -q
```
Mock mode (default) needs no API keys, so the project always demos.

## 6. REST API
| Method | Path | Purpose |
|---|---|---|
| POST | /runs | run an experiment `{task, live, fault, fault_rounds, max_rounds}` |
| GET | /runs, /runs/{id} | history, full log + failures |
| GET | /stats | aggregates for charts |
| GET | /faults, /health | utilities |

## 7. Git workflow
```bash
git init && git add . && git commit -m "feat: initial multi-agent lab"
git branch -M main
git remote add origin https://github.com/<you>/multi-agent-failure-lab.git
git push -u origin main
```
Suggested commits: db layer -> agents -> orchestrator -> detector -> fault injection -> UI -> tests.

## 8. Roadmap (future work / viva answers)
- LLM-as-judge detector (Claude) to catch semantic contradictions the rules miss
- Parallel agents + shared memory (race conditions, stale state)
- Migrate SQLite -> PostgreSQL; add auth and Docker
- Benchmark dataset of 100 tasks x 5 faults; compare provider combinations
- Replace keyword drift check with embedding similarity

## 9. Limitations
Rule-based detection is heuristic; mock mode simulates, not measures, real model behaviour;
only the planner->executor edge has fault injection.
