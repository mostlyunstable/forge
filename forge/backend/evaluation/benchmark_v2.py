import json
import logging
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkV2:
    def __init__(self, questions_file: str, ground_truth_file: str):
        self.questions_file = questions_file
        self.ground_truth_file = ground_truth_file
        self.questions = self._load_json(questions_file)
        self.ground_truth = self._load_json(ground_truth_file)

    def _load_json(self, filepath: str) -> Any:
        with open(filepath) as f:
            return json.load(f)

    def calculate_precision_at_k(self, retrieved: list[str], relevant: list[str], k: int) -> float:
        retrieved_k = retrieved[:k]
        if not retrieved_k:
            return 0.0
        relevant_retrieved = set(retrieved_k).intersection(set(relevant))
        return len(relevant_retrieved) / k

    def calculate_recall_at_k(self, retrieved: list[str], relevant: list[str], k: int) -> float:
        retrieved_k = retrieved[:k]
        if not relevant:
            return 1.0
        relevant_retrieved = set(retrieved_k).intersection(set(relevant))
        return len(relevant_retrieved) / len(relevant)

    def calculate_mrr(self, retrieved: list[str], relevant: list[str]) -> float:
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                return 1.0 / (i + 1)
        return 0.0

    def calculate_citation_accuracy(
        self, citations: list[str], expected_citations: list[str]
    ) -> float:
        if not expected_citations:
            return 1.0
        correct = set(citations).intersection(set(expected_citations))
        return len(correct) / len(expected_citations)

    def calculate_hallucination_rate(
        self, generated_claims: list[str], ground_truth_claims: list[str]
    ) -> float:
        # Dummy implementation for hallucination rate based on exact match of claims to expected citations/claims
        if not generated_claims:
            return 0.0
        unsupported = [c for c in generated_claims if c not in ground_truth_claims]
        return len(unsupported) / len(generated_claims)

    def evaluate_query(
        self,
        query_id: str,
        retrieved_docs: list[str],
        citations: list[str],
        generated_claims: list[str],
    ) -> dict[str, float]:
        if query_id not in self.ground_truth:
            logger.warning(f"No ground truth found for query {query_id}")
            return {}

        gt = self.ground_truth[query_id]
        relevant_docs = gt.get("relevant_docs", [])
        expected_citations = gt.get("expected_citations", [])

        # Ground truth claims could be derived or provided separately, assuming expected_citations here for check
        ground_truth_claims = expected_citations

        p_at_5 = self.calculate_precision_at_k(retrieved_docs, relevant_docs, 5)
        r_at_10 = self.calculate_recall_at_k(retrieved_docs, relevant_docs, 10)
        mrr = self.calculate_mrr(retrieved_docs, relevant_docs)
        cit_acc = self.calculate_citation_accuracy(citations, expected_citations)
        hal_rate = self.calculate_hallucination_rate(generated_claims, ground_truth_claims)

        return {
            "Precision@5": p_at_5,
            "Recall@10": r_at_10,
            "MRR": mrr,
            "Citation_Accuracy": cit_acc,
            "Hallucination_Rate": hal_rate,
        }

    def run_benchmark(self, system_responses: dict[str, dict[str, Any]]) -> dict[str, float]:
        metrics_sum = {
            "Precision@5": 0.0,
            "Recall@10": 0.0,
            "MRR": 0.0,
            "Citation_Accuracy": 0.0,
            "Hallucination_Rate": 0.0,
        }
        count = 0

        for q in self.questions:
            q_id = q["id"]
            if q_id in system_responses:
                resp = system_responses[q_id]
                retrieved_docs = resp.get("retrieved_docs", [])
                citations = resp.get("citations", [])
                generated_claims = resp.get("generated_claims", [])

                metrics = self.evaluate_query(q_id, retrieved_docs, citations, generated_claims)
                if metrics:
                    for k, v in metrics.items():
                        metrics_sum[k] += v
                    count += 1

        if count == 0:
            return {k: 0.0 for k in metrics_sum}

        avg_metrics = {k: v / count for k, v in metrics_sum.items()}
        logger.info(
            f"Benchmark Results (over {count} queries): {json.dumps(avg_metrics, indent=2)}"
        )
        return avg_metrics


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    q_file = os.path.join(script_dir, "questions_v2.json")
    gt_file = os.path.join(script_dir, "ground_truth_v2.json")

    if os.path.exists(q_file) and os.path.exists(gt_file):
        benchmark = BenchmarkV2(q_file, gt_file)
        # Dummy data for demonstration
        dummy_responses = {
            "q1": {
                "retrieved_docs": ["doc_adr_042", "doc_other"],
                "citations": ["ADR-042"],
                "generated_claims": ["ADR-042"],
            }
        }
        benchmark.run_benchmark(dummy_responses)
    else:
        print("Required JSON files not found.")
