from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class FaithfulnessEvaluator:

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    # =========================
    # SPLIT GENERATED TEXT
    # =========================

    def extract_claims(self, generated_text):

        claims = generated_text.split(".")

        claims = [
            claim.strip()
            for claim in claims
            if len(claim.strip()) > 10
        ]

        return claims

    # =========================
    # VERIFY CLAIMS
    # =========================

    def verify_claims(
        self,
        claims,
        retrieved_docs,
        threshold=0.35
    ):

        verified_claims = 0

        claim_results = []

        context_text = " ".join([
            doc["text"]
            for doc in retrieved_docs
        ])

        if not context_text.strip():

            return {
                "faithfulness_score": 0,
                "verified_claims": 0,
                "total_claims": len(claims),
                "claims": []
            }

        context_embedding = self.model.encode(
            [context_text]
        )

        for claim in claims:

            claim_embedding = self.model.encode(
                [claim]
            )

            similarity = cosine_similarity(
                claim_embedding,
                context_embedding
            )[0][0]

            verified = bool(similarity >= threshold)

            if verified:
                verified_claims += 1

            claim_results.append({

                "claim": claim,

                "verified": verified,

                "similarity": round(
                    float(similarity),
                    4
                )
            })

        faithfulness_score = 0

        if len(claims) > 0:

            faithfulness_score = round(
                (
                    verified_claims / len(claims)
                ) * 100,
                2
            )

        return {

            "faithfulness_score":
                faithfulness_score,

            "verified_claims":
                verified_claims,

            "total_claims":
                len(claims),

            "claims":
                claim_results
        }

    # =========================
    # MAIN EVALUATION
    # =========================

    def evaluate(
        self,
        generated_text,
        retrieved_docs
    ):

        claims = self.extract_claims(
            generated_text
        )

        return self.verify_claims(
            claims,
            retrieved_docs
        )