import time
from datetime import datetime

from app.rag.embeddings import get_embedding
from app.rag.retrieve import search
from app.rag.insights import generate_insights

from app.api.observability import log_query_metrics

from app.rag.faithfulness import FaithfulnessEvaluator

from app.rag.query_complexity import QueryComplexityIndex
class RAGPipeline:

    def __init__(self):

        self.faithfulness = FaithfulnessEvaluator()
        self.qci = QueryComplexityIndex()

    def process_query(self, query, top_k=5):

        total_start = time.time()
        query_complexity = self.qci.calculate(
    query
)
        # =========================
        # STEP 1 — EMBEDDING
        # =========================

        embedding_start = time.time()

        query_embedding = get_embedding(query)

        embedding_time = (
            time.time() - embedding_start
        ) * 1000

        # =========================
        # STEP 2 — RETRIEVAL
        # =========================

        retrieval_start = time.time()

        retrieved_docs = search(
            query,
            query_embedding,
            top_k=top_k
        )

        retrieval_time = (
            time.time() - retrieval_start
        ) * 1000
        similarities = [
        doc["similarity"]
        for doc in retrieved_docs
]
        average_similarity = (
    sum(similarities) / len(similarities)
    if similarities else 0
)
        # =========================
        # STEP 3 — GENERATION
        # =========================

        generation_start = time.time()

        generated_answer = generate_insights(query)

        generation_time = (
            time.time() - generation_start
        ) * 1000

        # =========================
        # STEP 4 — PREPARE GENERATED TEXT
        # =========================

        generated_text_parts = []

        generated_text_parts.extend(
            generated_answer.get(
                "key_takeaways",
                []
            )
        )

        generated_text_parts.extend(
            generated_answer.get(
                "did_you_know",
                []
            )
        )

        generated_text_parts.extend(
            generated_answer.get(
                "examples",
                []
            )
        )

        generated_text = ". ".join(
            generated_text_parts
        )

        # =========================
        # STEP 5 — FAITHFULNESS
        # =========================

        faithfulness_result = (
            self.faithfulness.evaluate(
                generated_text,
                retrieved_docs
            )
        )

        # =========================
        # STEP 6 — TOTAL LATENCY
        # =========================

        total_time = (
            time.time() - total_start
        ) * 1000

        # =========================
        # STEP 7 — LOG METRICS
        # =========================

        metrics = {

            "query":
                query,

            "retrieved_docs":
                len(retrieved_docs),
            "retrieval_success":
             1 if len(retrieved_docs) > 0 else 0,
            "average_similarity":
                average_similarity,
            "retrieval_latency_ms":
                retrieval_time,

            "generation_latency_ms":
                generation_time,

            "total_latency_ms":
                total_time,

            "faithfulness_score":
                faithfulness_result[
                    "faithfulness_score"
                ],

            "verified_claims":
                faithfulness_result[
                    "verified_claims"
                ],

            "total_claims":
                faithfulness_result[
                    "total_claims"
                ],
            "query_complexity_index":
                query_complexity[
                    "query_complexity_index"
                ],

            "complexity_level":
                query_complexity[
                "complexity_level"
                ],

            "timestamp":
                datetime.utcnow().isoformat()
        }

        log_query_metrics(metrics)

        return {

            "answer":
                generated_answer,

            "retrieved_docs":
                retrieved_docs,

            "faithfulness":
                faithfulness_result,
            "query_complexity":
                query_complexity,

            "metrics":
                metrics
        }