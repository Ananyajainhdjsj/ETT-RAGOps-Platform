import sqlite3


class NightOptimizer:

    def analyze_system(self):

        conn = sqlite3.connect(
            "rag_metrics.db"
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT *

            FROM query_metrics

        """)

        rows = cursor.fetchall()

        conn.close()

        if not rows:

            return {
                "status": "no_data"
            }

        # =========================
        # BASIC METRICS
        # =========================

        total_queries = len(rows)

        avg_faithfulness = sum(
            row["faithfulness_score"]
            for row in rows
        ) / total_queries

        avg_similarity = sum(
            row["average_similarity"]
            for row in rows
        ) / total_queries

        avg_latency = sum(
            row["total_latency_ms"]
            for row in rows
        ) / total_queries

        retrieval_success_rate = (
            sum(
                row["retrieval_success"]
                for row in rows
            ) / total_queries
        ) * 100

        # =========================
        # OPTIMIZATION RULES
        # =========================

        recommendations = []

        # ---------------------------------
        # RULE 1
        # LOW FAITHFULNESS
        # ---------------------------------

        if avg_faithfulness < 50:

            recommendations.append({

                "issue":
                    "low_faithfulness",

                "recommendation":
                    "reduce_chunk_size",

                "reason":
                    "Smaller chunks improve retrieval grounding"

            })

        # ---------------------------------
        # RULE 2
        # LOW SIMILARITY
        # ---------------------------------

        if avg_similarity < 45:

            recommendations.append({

                "issue":
                    "low_similarity",

                "recommendation":
                    "increase_chunk_overlap",

                "reason":
                    "Higher overlap preserves semantic continuity"

            })

        # ---------------------------------
        # RULE 3
        # HIGH LATENCY
        # ---------------------------------

        if avg_latency > 5000:

            recommendations.append({

                "issue":
                    "high_latency",

                "recommendation":
                    "enable_embedding_cache",

                "reason":
                    "Embedding reuse reduces repeated computation"

            })

        # ---------------------------------
        # RULE 4
        # LOW RETRIEVAL SUCCESS
        # ---------------------------------

        if retrieval_success_rate < 80:

            recommendations.append({

                "issue":
                    "low_retrieval_success",

                "recommendation":
                    "increase_top_k",

                "reason":
                    "Retrieving more chunks improves answer coverage"

            })

        # =========================
        # FINAL RESPONSE
        # =========================

        return {

            "status":
                "completed",

            "queries_analyzed":
                total_queries,

            "average_faithfulness":
                round(avg_faithfulness, 2),

            "average_similarity":
                round(avg_similarity, 2),

            "average_latency_ms":
                round(avg_latency, 2),

            "retrieval_success_rate":
                round(retrieval_success_rate, 2),

            "recommendations":
                recommendations
        }