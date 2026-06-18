
from __future__ import annotations

import streamlit as st


def init_session() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("current_query", "")
    st.session_state.setdefault("case_text", "")
    st.session_state.setdefault("domain", "property")
    st.session_state.setdefault("subcategory", "security_deposit_recovery")
    st.session_state.setdefault("case_title", "Tenant Deposit Dispute")
    st.session_state.setdefault("last_answer", "")
    st.session_state.setdefault("procedure", None)


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})
