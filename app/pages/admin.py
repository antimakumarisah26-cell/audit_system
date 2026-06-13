"""
app/pages/admin.py
───────────────────
Admin panel: user management, data import, audit trail.
Only accessible to users with role='admin'.
"""

import streamlit as st
import pandas as pd

from app.services import database as db
from app.utils.validators import (
    validate_username, validate_password,
    validate_branch_name, validate_transaction_volume,
    validate_compliance_score, validate_csv_columns,
)
from app.utils.logger import logger


def render():
    user = st.session_state.user

    if user["role"] != "admin":
        st.error("🔒 Access denied. Admin role required.")
        return

    st.title("⚙️ Admin Panel")

    tab_users, tab_add_user, tab_data, tab_log = st.tabs([
        "👥 Users", "➕ Add User", "📊 Audit Data", "📜 Audit Trail"
    ])

    # ── Users ─────────────────────────────────────────────────────────────────
    with tab_users:
        st.subheader("All Users")
        users_df = db.get_all_users()
        if users_df.empty:
            st.info("No users found.")
        else:
            st.dataframe(users_df, use_container_width=True)

        st.divider()
        st.subheader("Deactivate User")
        deactivate_id = st.number_input("User ID to deactivate", min_value=1, step=1)
        if st.button("Deactivate", type="secondary"):
            if deactivate_id == user["id"]:
                st.error("You cannot deactivate your own account.")
            elif db.deactivate_user(int(deactivate_id)):
                db.log_action(user["id"], user["username"], "deactivate_user", f"user_id={deactivate_id}")
                st.success(f"User {deactivate_id} deactivated.")
                st.rerun()
            else:
                st.error("User not found.")

    # ── Add user ──────────────────────────────────────────────────────────────
    with tab_add_user:
        st.subheader("Create New User")

        with st.form("create_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])
            submitted = st.form_submit_button("Create User", use_container_width=True)

        if submitted:
            ok, msg = validate_username(new_username)
            if not ok:
                st.error(f"❌ {msg}")
            else:
                ok, msg = validate_password(new_password)
                if not ok:
                    st.error(f"❌ {msg}")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match.")
                else:
                    success, message = db.create_user(new_username, new_password, new_role)
                    if success:
                        db.log_action(user["id"], user["username"], "create_user",
                                      f"new_user={new_username}, role={new_role}")
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    # ── Audit data ────────────────────────────────────────────────────────────
    with tab_data:
        st.subheader("📥 Import from CSV")
        st.caption("Required columns: `branch_name`, `account_type`, `transaction_volume`, `compliance_score`")

        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            try:
                upload_df = pd.read_csv(uploaded)
                ok, msg = validate_csv_columns(list(upload_df.columns))
                if not ok:
                    st.error(f"❌ {msg}")
                else:
                    st.dataframe(upload_df.head(), use_container_width=True)
                    if st.button("Import CSV", type="primary", use_container_width=True):
                        success, message = db.import_audit_records(upload_df)
                        if success:
                            db.log_action(user["id"], user["username"], "import_csv",
                                          f"{len(upload_df)} records from '{uploaded.name}'")
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
            except Exception as exc:
                st.error(f"❌ Could not parse CSV: {exc}")

        st.divider()

        st.subheader("➕ Add Single Record")
        with st.form("add_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                branch_name = st.text_input("Branch Name", placeholder="e.g. Mumbai Central")
                account_type = st.selectbox("Account Type",
                    ["Savings", "Current", "Fixed Deposit", "Loan", "Investment Account"])
                notes = st.text_area("Notes (optional)", placeholder="Observations…", height=80)
            with col2:
                transaction_volume = st.number_input("Transaction Volume (₹)", min_value=0.0, step=1000.0, value=50000.0)
                compliance_score = st.slider("Compliance Score (%)", 0.0, 100.0, 75.0)

            add_record = st.form_submit_button("Add Record", use_container_width=True)

        if add_record:
            errors = []
            ok, msg = validate_branch_name(branch_name)
            if not ok: errors.append(msg)
            ok, msg = validate_transaction_volume(transaction_volume)
            if not ok: errors.append(msg)
            ok, msg = validate_compliance_score(compliance_score)
            if not ok: errors.append(msg)

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                success = db.add_audit_record(
                    branch_name, account_type,
                    transaction_volume, compliance_score,
                    notes=notes,
                )
                if success:
                    db.log_action(user["id"], user["username"], "add_record",
                                  f"branch={branch_name}, vol={transaction_volume}")
                    st.success("✅ Record added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add record. Check logs.")

        st.divider()

        st.subheader("📋 Current Records")
        records = db.load_audit_records()
        if records.empty:
            st.info("No records yet. Add some above.")
        else:
            st.dataframe(records, use_container_width=True)
            st.caption(f"Total: {len(records)} records")

            st.subheader("🗑️ Delete Record")
            del_id = st.number_input("Record ID to delete", min_value=1, step=1)
            if st.button("Delete Record", type="secondary"):
                if db.delete_audit_record(int(del_id)):
                    db.log_action(user["id"], user["username"], "delete_record", f"record_id={del_id}")
                    st.success(f"Record {del_id} deleted.")
                    st.rerun()
                else:
                    st.error("Record not found.")

    # ── Audit trail ───────────────────────────────────────────────────────────
    with tab_log:
        st.subheader("📜 System Audit Trail")
        st.caption("Immutable log of all admin actions.")
        logs = db.get_audit_logs()
        if logs.empty:
            st.info("No actions logged yet.")
        else:
            st.dataframe(logs, use_container_width=True, height=500)
            csv = logs.to_csv(index=False)
            st.download_button("⬇️ Export Logs", csv, "audit_trail.csv", "text/csv")