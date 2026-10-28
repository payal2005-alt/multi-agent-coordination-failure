"""Deterministic fake agents so the project runs without API keys (demo + tests)."""
import re


def planner(user: str) -> str:
    task = re.search(r"Task: (.*)", user).group(1)
    rev = "REVISED PLAN\n" if "feedback" in user.lower() else ""
    return (f"{rev}SUBTASKS:\n"
            f"1. Research background information about {task}\n"
            f"2. Draft the main solution for {task}\n"
            f"3. Verify and summarise the final result for {task}")


def executor(user: str) -> str:
    if "You are the Reviewer" in user:                      # role-confusion fault
        return "APPROVED"
    if "IGNORE the above" in user:                          # contradiction fault
        return "Here is a poem about the weather: sunny skies and a gentle breeze all day long."
    steps = re.findall(r"^\d+\.\s*(.+)$", user, re.M)
    if not steps:
        return "No plan received."
    return "\n".join(f"Step {i}: completed - {s}" for i, s in enumerate(steps, 1))


def reviewer(user: str) -> str:
    n = len(re.findall(r"^Step \d+", user, re.M))
    if n >= 3:
        return "APPROVED: all subtasks are covered."
    return f"REJECTED: only {n} of 3 subtasks completed. Planner must resend the full plan."


MOCK = {"planner": planner, "executor": executor, "reviewer": reviewer}
