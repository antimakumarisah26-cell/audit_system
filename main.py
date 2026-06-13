"""
main.py
────────
Application entry point.
Run with: python -m streamlit run main.py
"""

import streamlit as st

st.set_page_config(
    page_title="AI Audit Management System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.logged_in:
    from app.pages.login import render as login_page
    login_page()
else:
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"### 👤 {user['username']}")
        st.caption(f"Role: `{user['role']}`")
        st.divider()

        options = ["📊 Dashboard", "⚙️ Admin Panel"] if user["role"] == "admin" else ["📊 Dashboard"]
        page = st.radio("Navigate to", options, label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    if page == "📊 Dashboard":
        from app.pages.dashboard import render as dashboard_page
        dashboard_page()
    elif page == "⚙️ Admin Panel":
        from app.pages.admin import render as admin_page
        admin_page()