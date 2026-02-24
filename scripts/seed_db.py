"""
seed_db.py — One-time script to create and populate subscriber_sample.db
with 80 synthetic subscriber rows across four churn segments.

Run from the project root:
    python scripts/seed_db.py
"""
import sys
import os
import sqlite3
import random

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

random.seed(42)

SEGMENTS = {
    "Early High-Risk": {
        "churn_range": (0.60, 0.90),
        "charge_range": (70, 110),
        "tenure_range": (1, 12),
        "contracts": ["Month-to-month"] * 9 + ["One year"],
        "count": 20,
    },
    "At-Risk Mid-Value": {
        "churn_range": (0.30, 0.60),
        "charge_range": (50, 85),
        "tenure_range": (6, 36),
        "contracts": ["Month-to-month"] * 6 + ["One year"] * 3 + ["Two year"],
        "count": 20,
    },
    "Loyal High-Value": {
        "churn_range": (0.15, 0.40),
        "charge_range": (80, 130),
        "tenure_range": (24, 72),
        "contracts": ["Month-to-month"] * 2 + ["One year"] * 4 + ["Two year"] * 4,
        "count": 20,
    },
    "Stable Low-Value": {
        "churn_range": (0.05, 0.20),
        "charge_range": (20, 50),
        "tenure_range": (12, 60),
        "contracts": ["Month-to-month"] * 2 + ["One year"] * 4 + ["Two year"] * 4,
        "count": 20,
    },
}


def seed():
    db_path = config.DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS subscribers;")
    cur.execute("""
        CREATE TABLE subscribers (
            subscriber_id    INTEGER PRIMARY KEY,
            segment_label    TEXT    NOT NULL,
            churn_probability REAL   NOT NULL,
            monthly_charges  REAL    NOT NULL,
            contract_type    TEXT    NOT NULL,
            tenure           INTEGER NOT NULL
        );
    """)

    rows = []
    subscriber_id = 1001

    for segment, cfg in SEGMENTS.items():
        for _ in range(cfg["count"]):
            churn_prob = round(random.uniform(*cfg["churn_range"]), 4)
            monthly = round(random.uniform(*cfg["charge_range"]), 2)
            tenure = random.randint(*cfg["tenure_range"])
            contract = random.choice(cfg["contracts"])
            rows.append((subscriber_id, segment, churn_prob, monthly, contract, tenure))
            subscriber_id += 1

    cur.executemany(
        "INSERT INTO subscribers VALUES (?, ?, ?, ?, ?, ?);",
        rows,
    )
    conn.commit()
    conn.close()

    print(f"Database seeded: {len(rows)} rows written to {db_path}")


if __name__ == "__main__":
    seed()
