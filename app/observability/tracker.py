import sqlite3
import json


DB_NAME = "rag_metrics.db"


def initialize_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            retrieved_docs INTEGER,
            retrieval_latency_ms REAL,
            generation_latency_ms REAL,
            total_latency_ms REAL,
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
            retrieval_latency_ms,
            generation_latency_ms,
            total_latency_ms,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        metrics["query"],
        metrics["retrieved_docs"],
        metrics["retrieval_latency_ms"],
        metrics["generation_latency_ms"],
        metrics["total_latency_ms"],
        metrics["timestamp"]
    ))

    conn.commit()
    conn.close()