import json
import logging
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkV3:
    def __init__(self, sessions_file: str):
        self.sessions_file = sessions_file
        self.sessions = self._load_json(sessions_file)

    def _load_json(self, filepath: str) -> Any:
        with open(filepath) as f:
            return json.load(f)

    def calculate_precision(self, retrieved: list[str], expected: list[str]) -> float:
        if not expected and not retrieved:
            return 1.0
        if not retrieved:
            return 0.0
        correct = set(retrieved).intersection(set(expected))
        return len(correct) / len(retrieved)

    def calculate_hallucination_rate(self, generated: list[str], ground_truth: list[str]) -> float:
        if not generated:
            return 0.0
        unsupported = [c for c in generated if c not in ground_truth]
        return len(unsupported) / len(generated)

    def evaluate_turn(
        self, turn_def: dict[str, Any], turn_resp: dict[str, Any]
    ) -> dict[str, float]:
        expected_docs = turn_def.get("expected_docs", [])
        expected_citations = turn_def.get("expected_citations", [])
        gt_claims = turn_def.get("ground_truth_claims", [])
        budget = turn_def.get("token_budget", 1000)

        retrieved = turn_resp.get("retrieved_docs", [])
        citations = turn_resp.get("citations", [])
        claims = turn_resp.get("generated_claims", [])
        tokens = turn_resp.get("tokens_used", 0)
        plan_score = turn_resp.get("plan_score", 0.0)

        context_retention = self.calculate_precision(retrieved, expected_docs)
        cit_correctness = self.calculate_precision(citations, expected_citations)
        hal_rate = self.calculate_hallucination_rate(claims, gt_claims)

        token_adherence = 1.0 if tokens <= budget else max(0.0, 1.0 - ((tokens - budget) / budget))

        return {
            "Context_Retention": context_retention,
            "Citation_Precision": cit_correctness,
            "Hallucination_Rate": hal_rate,
            "Plan_Quality": plan_score,
            "Token_Adherence": token_adherence,
        }

    def run_benchmark(self, system_responses: dict[str, dict[str, Any]]) -> dict[str, float]:
        metrics_sum = {
            "Context_Retention": 0.0,
            "Citation_Precision": 0.0,
            "Hallucination_Rate": 0.0,
            "Plan_Quality": 0.0,
            "Token_Adherence": 0.0,
            "Multi_Turn_Consistency": 0.0,
            "Ambiguity_Handling": 0.0,
            "Follow_Up_Understanding": 0.0,
        }
        total_turns = 0
        total_sessions = 0
        ambiguous_turns_count = 0
        follow_up_turns_count = 0

        for session in self.sessions:
            s_id = session["session_id"]
            if s_id not in system_responses:
                logger.warning(f"No system response for session {s_id}")
                continue

            s_resp = system_responses[s_id]
            session_context_scores = []

            for i, turn in enumerate(session["turns"]):
                t_id = turn["turn_id"]
                if t_id not in s_resp:
                    continue

                t_resp = s_resp[t_id]
                t_metrics = self.evaluate_turn(turn, t_resp)

                metrics_sum["Context_Retention"] += t_metrics["Context_Retention"]
                metrics_sum["Citation_Precision"] += t_metrics["Citation_Precision"]
                metrics_sum["Hallucination_Rate"] += t_metrics["Hallucination_Rate"]
                metrics_sum["Plan_Quality"] += t_metrics["Plan_Quality"]
                metrics_sum["Token_Adherence"] += t_metrics["Token_Adherence"]

                if turn.get("is_ambiguous", False):
                    metrics_sum["Ambiguity_Handling"] += t_metrics["Context_Retention"]
                    ambiguous_turns_count += 1

                if i > 0:
                    metrics_sum["Follow_Up_Understanding"] += t_metrics["Context_Retention"]
                    # Multi-turn consistency approximation
                    consistency = (
                        (session_context_scores[-1] + t_metrics["Context_Retention"]) / 2.0
                        if session_context_scores
                        else t_metrics["Context_Retention"]
                    )
                    metrics_sum["Multi_Turn_Consistency"] += consistency
                    follow_up_turns_count += 1

                session_context_scores.append(t_metrics["Context_Retention"])
                total_turns += 1

            total_sessions += 1

        if total_turns == 0:
            return {k: 0.0 for k in metrics_sum}

        avg_metrics = {k: v / total_turns for k, v in metrics_sum.items()}

        if ambiguous_turns_count > 0:
            avg_metrics["Ambiguity_Handling"] = (
                metrics_sum["Ambiguity_Handling"] / ambiguous_turns_count
            )
        else:
            avg_metrics["Ambiguity_Handling"] = 1.0

        if follow_up_turns_count > 0:
            avg_metrics["Follow_Up_Understanding"] = (
                metrics_sum["Follow_Up_Understanding"] / follow_up_turns_count
            )
            avg_metrics["Multi_Turn_Consistency"] = (
                metrics_sum["Multi_Turn_Consistency"] / follow_up_turns_count
            )
        else:
            avg_metrics["Follow_Up_Understanding"] = 1.0
            avg_metrics["Multi_Turn_Consistency"] = 1.0

        logger.info(
            f"Phase 3 Benchmark Results (over {total_sessions} sessions, {total_turns} turns):"
        )
        logger.info(json.dumps(avg_metrics, indent=2))

        if avg_metrics.get("Hallucination_Rate", 1.0) > 0.01:
            logger.warning(
                f"WARNING: Hallucination Rate ({avg_metrics['Hallucination_Rate']:.4f}) exceeds 1% threshold!"
            )

        return avg_metrics


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    s_file = os.path.join(script_dir, "questions_v3.json")

    if os.path.exists(s_file):
        benchmark = BenchmarkV3(s_file)

        dummy_responses = {
            "session_1": {
                "t1": {
                    "retrieved_docs": ["doc_intent_router"],
                    "citations": ["IntentRouter.py"],
                    "generated_claims": ["parses user intents"],
                    "tokens_used": 450,
                    "plan_score": 0.95,
                },
                "t2": {
                    "retrieved_docs": ["test_intent_router"],
                    "citations": ["test_intent_router.py"],
                    "generated_claims": ["test directory"],
                    "tokens_used": 200,
                    "plan_score": 0.88,
                },
            },
            "session_2": {
                "t1": {
                    "retrieved_docs": ["bug_7711", "worker_memory_profile"],
                    "citations": ["Bug-#7711", "Profile-Mem"],
                    "generated_claims": ["caching issue", "unreleased objects"],
                    "tokens_used": 750,
                    "plan_score": 0.92,
                },
                "t2": {
                    "retrieved_docs": ["commit_88f2a"],
                    "citations": ["Commit-88f2a"],
                    "generated_claims": ["Alice Smith"],
                    "tokens_used": 250,
                    "plan_score": 0.90,
                },
                "t3": {
                    "retrieved_docs": ["doc_caching_module"],
                    "citations": ["Caching.md"],
                    "generated_claims": ["documented in Caching.md"],
                    "tokens_used": 280,
                    "plan_score": 0.91,
                },
            },
        }
        benchmark.run_benchmark(dummy_responses)
    else:
        print(f"Required JSON file not found: {s_file}")
