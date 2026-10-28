"""SQLite persistence: runs, messages, failures."""
import sqlite3
from datetime import datetime, timezone
from . import config


def _conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT, mode TEXT, fault TEXT,
            status TEXT DEFAULT 'running', score INTEGER,
            created_at TEXT);
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER, step INTEGER, round INTEGER,
            agent TEXT, role TEXT, content TEXT, latency_ms INTEGER);
        CREATE TABLE IF NOT EXISTS failures(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER, step INTEGER, type TEXT,
            severity INTEGER, detail TEXT);
        """)


def create_run(task, mode, fault):
    init_db()
    with _conn() as c:
        cur = c.execute("INSERT INTO runs(task,mode,fault,created_at) VALUES(?,?,?,?)",
                        (task, mode, fault, datetime.now(timezone.utc).isoformat()))
        return cur.lastrowid


def add_message(run_id, m):
    with _conn() as c:
        c.execute("INSERT INTO messages(run_id,step,round,agent,role,content,latency_ms) VALUES(?,?,?,?,?,?,?)",
                  (run_id, m["step"], m["round"], m["agent"], m["role"], m["content"], m["latency_ms"]))


def add_failures(run_id, failures):
    with _conn() as c:
        c.executemany("INSERT INTO failures(run_id,step,type,severity,detail) VALUES(?,?,?,?,?)",
                      [(run_id, f["step"], f["type"], f["severity"], f["detail"]) for f in failures])


def finish_run(run_id, status, score):
    with _conn() as c:
        c.execute("UPDATE runs SET status=?, score=? WHERE id=?", (status, score, run_id))


def list_runs():
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 100")]


def get_run(run_id):
    with _conn() as c:
        run = c.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run:
            return None
        msgs = [dict(r) for r in c.execute("SELECT * FROM messages WHERE run_id=? ORDER BY step", (run_id,))]
        fails = [dict(r) for r in c.execute("SELECT * FROM failures WHERE run_id=? ORDER BY step", (run_id,))]
        return {"run": dict(run), "messages": msgs, "failures": fails}


def stats():
    with _conn() as c:
        by_type = [dict(r) for r in c.execute(
            "SELECT type, COUNT(*) AS count FROM failures GROUP BY type ORDER BY count DESC")]
        by_fault = [dict(r) for r in c.execute(
            "SELECT fault, COUNT(*) AS runs, ROUND(AVG(score),1) AS avg_score "
            "FROM runs WHERE score IS NOT NULL GROUP BY fault")]
        return {"failures_by_type": by_type, "score_by_fault": by_fault}
