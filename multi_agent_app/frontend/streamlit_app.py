import requests
import pandas as pd
import streamlit as st

API = "http://127.0.0.1:8000"
st.set_page_config(page_title="Multi-Agent Failure Lab", layout="wide")
st.title("Multi-Agent Coordination Failure Lab")
st.caption("Planner (OpenAI) -> Executor (Gemini) -> Reviewer (Claude)")

with st.sidebar:
    st.header("Experiment")
    task = st.text_area("Task", "Explain how solar panels generate electricity")
    fault = st.selectbox("Inject fault", requests.get(f"{API}/faults").json())
    live = st.checkbox("Use live LLM APIs (needs keys in .env)", value=False)
    fault_rounds = st.slider("Fault active for N rounds", 0, 3, 1)
    go = st.button("Run experiment", type="primary")

if go:
    with st.spinner("Agents are coordinating..."):
        r = requests.post(f"{API}/runs", json={"task": task, "live": live, "fault": fault,
                                               "fault_rounds": fault_rounds})
    if r.ok:
        d = r.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Coordination score", d["run"]["score"])
        c2.metric("Outcome", d["run"]["status"])
        c3.metric("Failures detected", len(d["failures"]))
        st.subheader("Conversation log")
        for m in d["messages"]:
            with st.chat_message("assistant"):
                st.markdown(f"**R{m['round']} - {m['role']} ({m['agent']})** - {m['latency_ms']} ms")
                st.text(m["content"])
        st.subheader("Detected failures")
        if d["failures"]:
            st.dataframe(pd.DataFrame(d["failures"]), use_container_width=True)
        else:
            st.success("No coordination failures detected")
    else:
        st.error(r.text)

st.divider()
st.subheader("Aggregate analysis")
s = requests.get(f"{API}/stats").json()
a, b = st.columns(2)
if s["failures_by_type"]:
    a.write("Failures by type")
    a.bar_chart(pd.DataFrame(s["failures_by_type"]).set_index("type"))
if s["score_by_fault"]:
    b.write("Average coordination score by injected fault")
    b.bar_chart(pd.DataFrame(s["score_by_fault"]).set_index("fault")["avg_score"])
