"""
app/pages/dashboard.py
───────────────────────
Main analytics dashboard — KPI cards, charts, high-risk alerts.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.config import config
from app.services import database as db
from app.services.ml_model import model_manager
from app.services.email_service import email_service
from app.services.data_generator import generate_sample_data
from app.utils.logger import logger


def _refresh_risk_scores() -> pd.DataFrame:
    """Load records, run ML scoring, persist results, return updated df."""
    df = db.load_audit_records()
    if df.empty:
        return df

    risk_scores, _ = model_manager.predict_risk(df)
    if len(risk_scores) > 0:
        df["risk_score"] = risk_scores
        db.update_risk_scores(df)
        df = db.load_audit_records()

    return df


def _seed_sample_data():
    """Called on first launch when DB is empty."""
    with st.spinner("Generating sample data and training AI model…"):
        sample = generate_sample_data(100)
        for _, row in sample.iterrows():
            db.add_audit_record(
                row["branch_name"],
                row["account_type"],
                float(row["transaction_volume"]),
                float(row["compliance_score"]),
            )
        model_manager.train(db.load_audit_records())
    st.success("✅ Sample data generated!")
    st.rerun()


def render():
    user = st.session_state.user

    st.markdown("""
    <div style="background:linear-gradient(90deg,#667eea,#764ba2);
                padding:1.2rem 2rem;border-radius:12px;margin-bottom:1.5rem;">
      <h1 style="color:white;margin:0;">🔍 AI Audit Management System</h1>
      <p style="color:rgba(255,255,255,0.85);margin:4px 0 0;">
        Anomaly detection · Risk scoring · Compliance monitoring
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(f"Logged in as **{user['username']}** ({user['role']})")

    df = _refresh_risk_scores()

    if df.empty:
        _seed_sample_data()
        return

    # ── KPI cards ─────────────────────────────────────────────────────────────
    total = len(df)
    high_risk = int((df["risk_score"] >= config.RISK_HIGH_THRESHOLD).sum())
    critical = int((df["risk_score"] >= config.RISK_CRITICAL_THRESHOLD).sum())
    avg_compliance = df["compliance_score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", total)
    c2.metric("High Risk", high_risk, delta=f"{high_risk/total*100:.1f}% of total", delta_color="inverse")
    c3.metric("Critical", critical, delta_color="inverse")
    c4.metric("Avg Compliance", f"{avg_compliance:.1f}%")

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        branch_risk = (
            df.groupby("branch_name")["risk_score"]
            .mean()
            .reset_index()
            .sort_values("risk_score", ascending=False)
        )
        fig = px.bar(
            branch_risk, x="branch_name", y="risk_score",
            color="risk_score", color_continuous_scale="Reds",
            title="Average Risk Score by Branch",
            labels={"branch_name": "Branch", "risk_score": "Risk Score"},
        )
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.pie(
            df, names="account_type", values="transaction_volume",
            title="Transaction Volume by Account Type",
            hole=0.35,
        )
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)

    # Risk distribution histogram
    fig3 = px.histogram(
        df, x="risk_score", nbins=20,
        title="Risk Score Distribution",
        color_discrete_sequence=["#764ba2"],
        labels={"risk_score": "Risk Score", "count": "Number of Accounts"},
    )
    fig3.add_vline(x=config.RISK_HIGH_THRESHOLD, line_dash="dash", line_color="orange",
                   annotation_text="High Risk Threshold")
    fig3.add_vline(x=config.RISK_CRITICAL_THRESHOLD, line_dash="dash", line_color="red",
                   annotation_text="Critical Threshold")
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # ── High risk alerts ──────────────────────────────────────────────────────
    st.subheader("🚨 High Risk Accounts")

    flagged = df[df["risk_score"] >= config.RISK_HIGH_THRESHOLD].sort_values("risk_score", ascending=False)

    if flagged.empty:
        st.success("✅ No high-risk accounts detected.")
    else:
        for _, row in flagged.head(8).iterrows():
            is_critical = row["risk_score"] >= config.RISK_CRITICAL_THRESHOLD
            color = "#ffebee" if is_critical else "#fff3e0"
            border = "#f44336" if is_critical else "#ff9800"
            label = "🔴 CRITICAL" if is_critical else "🟠 HIGH"
            explanation = model_manager.get_risk_explanation(row)

            st.markdown(f"""
            <div style="background:{color};border-left:5px solid {border};
                        padding:12px 16px;border-radius:6px;margin:6px 0;">
              <strong>{label} — {row['branch_name']} · {row['account_type']}</strong><br/>
              Risk: <strong>{row['risk_score']:.1f}/100</strong> &nbsp;|&nbsp;
              Compliance: {row['compliance_score']:.1f}% &nbsp;|&nbsp;
              Volume: ₹{row['transaction_volume']:,.0f}<br/>
              <small style="color:#555;">Reason: {explanation}</small>
            </div>
            """, unsafe_allow_html=True)

        # Send email alerts (only if email is configured)
        if email_service.is_configured() and user["role"] == "admin":
            if st.button("📧 Send Alert Emails for Critical Records"):
                critical_df = flagged[flagged["risk_score"] >= config.RISK_CRITICAL_THRESHOLD]
                sent = 0
                for _, row in critical_df.iterrows():
                    reason = model_manager.get_risk_explanation(row)
                    ok = email_service.send_high_risk_alert(
                        config.GMAIL_EMAIL, row["branch_name"], row["risk_score"], reason
                    )
                    if ok:
                        sent += 1
                st.success(f"Sent {sent} alert(s).")

    st.divider()

    # ── Full data table ───────────────────────────────────────────────────────
    st.subheader("📋 All Audit Records")

    search = st.text_input("🔍 Filter by branch name", placeholder="Type to search…")
    display_df = df[df["branch_name"].str.contains(search, case=False)] if search else df

    st.dataframe(
        display_df.style.background_gradient(subset=["risk_score"], cmap="Reds"),
        use_container_width=True,
        height=400,
    )
    st.caption(f"Showing {len(display_df)} of {len(df)} records.")

    # CSV export
    csv = display_df.to_csv(index=False)
    st.download_button("⬇️ Export to CSV", csv, "audit_records.csv", "text/csv")

    st.divider()

    # ── Retrain model ─────────────────────────────────────────────────────────
    if user["role"] == "admin":
        if st.button("🔄 Retrain Risk Model"):
            with st.spinner("Training…"):
                ok = model_manager.train(df)
            if ok:
                db.log_action(user["id"], user["username"], "retrain_model", f"{len(df)} records")
                st.success("Model retrained successfully.")
                st.rerun()
            else:
                st.error("Training failed — check logs.")