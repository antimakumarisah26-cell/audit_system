"""
app/services/data_generator.py
────────────────────────────────
Generates realistic synthetic audit data for demo and testing.
Separated from main.py so it can be reused and independently tested.
"""

import numpy as np
import pandas as pd


BRANCHES = [
    "Mumbai Central", "Delhi NCR", "Bangalore Tech Park", "Kolkata East",
    "Chennai Marina", "Pune IT Hub", "Hyderabad HITEC", "Ahmedabad West",
    "Jaipur North", "Surat Diamond",
]

ACCOUNT_TYPES = [
    "Savings", "Current", "Fixed Deposit", "Loan", "Investment Account"
]


def generate_sample_data(n: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate n synthetic audit records with realistic distributions.
    ~15% of records are intentionally anomalous (high risk).
    """
    rng = np.random.default_rng(seed)

    data = {
        "branch_name": rng.choice(BRANCHES, n),
        "account_type": rng.choice(ACCOUNT_TYPES, n),
        "transaction_volume": np.abs(rng.normal(50_000, 20_000, n)),
        "compliance_score": rng.beta(2, 5, n) * 100,
    }

    df = pd.DataFrame(data)

    # Inject anomalies into ~15% of records
    anomaly_idx = rng.choice(n, size=max(1, int(n * 0.15)), replace=False)
    df.loc[anomaly_idx, "transaction_volume"] *= rng.uniform(3, 6, len(anomaly_idx))
    df.loc[anomaly_idx, "compliance_score"] *= rng.uniform(0.2, 0.5, len(anomaly_idx))
    df["compliance_score"] = df["compliance_score"].clip(0, 100)

    return df