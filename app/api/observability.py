import sqlite3
from datetime import datetime

DB_NAME = "rag_metrics.db"


def initialize_metrics_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            retrieved_docs INTEGER,
            retrieval_success INTEGER,
            average_similarity REAL,
            retrieval_latency_ms REAL,
            generation_latency_ms REAL,
            total_latency_ms REAL,
            faithfulness_score REAL,
            query_complexity_index REAL,
            complexity_level TEXT,
            verified_claims INTEGER,
            total_claims INTEGER,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


def log_query_metrics(metrics):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO query_metrics (
            query,
            retrieved_docs,
            retrieval_success,
            average_similarity ,
            retrieval_latency_ms,
            generation_latency_ms,
            total_latency_ms,
            faithfulness_score,
            query_complexity_index,
            complexity_level,
            verified_claims,
            total_claims,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics["query"],
        metrics["retrieved_docs"],
        metrics["retrieval_success"],
        metrics["average_similarity"],
        metrics["retrieval_latency_ms"],
        metrics["generation_latency_ms"],
        metrics["total_latency_ms"],
        metrics["faithfulness_score"],
        metrics["query_complexity_index"],
        metrics["complexity_level"],
        metrics["verified_claims"],
        metrics["total_claims"],
        metrics["timestamp"]
    ))

    conn.commit()
    conn.close()