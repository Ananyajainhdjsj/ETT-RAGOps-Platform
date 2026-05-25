import re
import math
from collections import Counter


class QueryComplexityIndex:

    def calculate(self, query):

        # =========================
        # TOKENIZATION
        # =========================

        words = re.findall(
            r'\w+',
            query.lower()
        )

        word_count = len(words)

        unique_words = len(set(words))

        # =========================
        # QUERY LENGTH SCORE
        # =========================

        length_score = min(
            word_count / 12,
            1.0
        )

        # =========================
        # VOCABULARY DIVERSITY
        # =========================

        diversity_score = 0

        if word_count > 0:

            diversity_score = (
                unique_words / word_count
            )

        # =========================
        # SEMANTIC ENTROPY
        # =========================

        entropy = 0

        if word_count > 0:

            frequencies = Counter(words)

            probabilities = [

                count / word_count

                for count in frequencies.values()
            ]

            entropy = -sum(

                p * math.log2(p)

                for p in probabilities

            )

        entropy_score = min(
            entropy / 4,
            1.0
        )

        # =========================
        # SYNTACTIC COMPLEXITY
        # =========================

        connectors = [

            "and",
            "or",
            "while",
            "versus",
            "vs",
            "compare",
            "difference",
            "between",
            "with"

        ]

        connector_count = sum(

            1 for word in words

            if word in connectors
        )

        syntax_score = min(
            connector_count / 4,
            1.0
        )

        # =========================
        # FINAL QCI
        # =========================

        qci = round(

            (
                length_score * 0.30
                +
                diversity_score * 0.25
                +
                entropy_score * 0.30
                +
                syntax_score * 0.15
            ) * 100,

            2
        )

        # =========================
        # LABELS
        # =========================

        if qci < 35:

            complexity = "LOW"

        elif qci < 65:

            complexity = "MEDIUM"

        else:

            complexity = "HIGH"

        return {

            "query_complexity_index":
                qci,

            "complexity_level":
                complexity,

            "word_count":
                word_count,

            "unique_words":
                unique_words,

            "semantic_entropy":
                round(entropy, 4)
        }