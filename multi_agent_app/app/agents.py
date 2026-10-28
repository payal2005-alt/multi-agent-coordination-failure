"""Agent roles. Each role is bound to a different LLM provider on purpose:
heterogeneous models make coordination failures more likely and more interesting."""

AGENTS = {
    "planner": {
        "provider": "openai",
        "system": ("You are the PLANNER. Break the task into exactly 3 numbered subtasks. "
                   "Format: 'SUBTASKS:' then lines '1. ...', '2. ...', '3. ...'. "
                   "If reviewer feedback is given, output a REVISED PLAN."),
    },
    "executor": {
        "provider": "gemini",
        "system": ("You are the EXECUTOR. Complete every subtask in the plan. "
                   "Answer with one line per subtask: 'Step N: <result>'."),
    },
    "reviewer": {
        "provider": "claude",
        "system": ("You are the REVIEWER. Check the executor output against the task. "
                   "Reply with 'APPROVED: <reason>' or 'REJECTED: <reason>'. Nothing else."),
    },
}
