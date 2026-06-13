"""
app/pages/login.py
───────────────────
Login screen with rate-limit awareness and clear error messages.
"""

import streamlit as st
from app.services.database import authenticate_user, seed_default_admin
from app.config import config


def render():
    seed_default_admin()

    st.markdown("""
    <h1 style="text-align:center;margin-bottom:0.2rem;">🔍 AI Audit Management</h1>
    <p style="text-align:center;color:#666;margin-bottom:2rem;">
        Intelligent risk detection for banking compliance
    </p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔐 Sign In")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")

        if not config.is_production():
            st.info(f"**Demo login:** `{config.DEFAULT_ADMIN_USERNAME}` / `{config.DEFAULT_ADMIN_PASSWORD}`")