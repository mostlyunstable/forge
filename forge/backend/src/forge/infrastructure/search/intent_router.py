class IntentRouter:
    def __init__(self):
        self.bug_keywords = {
            "bug",
            "fix",
            "error",
            "exception",
            "crash",
            "issue",
            "fail",
            "broken",
            "wrong",
            "unexpected",
        }
        self.arch_keywords = {
            "architecture",
            "decision",
            "design",
            "why",
            "structure",
            "pattern",
            "component",
            "system",
        }
        self.code_keywords = {
            "code",
            "function",
            "class",
            "method",
            "implement",
            "where is",
            "how does",
            "variable",
        }
        self.graph_keywords = {
            "dependency",
            "import",
            "depend",
            "caller",
            "called by",
            "impact",
            "relationship",
            "usage",
        }

    def route(self, query: str, context_window=None) -> dict:
        """
        Routes the query based on heuristics and conversational history.
        Returns a dict with intent weights.
        """
        query_lower = query.lower()

        # Analyze current query
        bug_score = sum(1 for w in self.bug_keywords if w in query_lower)
        arch_score = sum(1 for w in self.arch_keywords if w in query_lower)
        code_score = sum(1 for w in self.code_keywords if w in query_lower)
        graph_score = sum(1 for w in self.graph_keywords if w in query_lower)

        # Analyze conversational history (decayed importance)
        if context_window and hasattr(context_window, "messages"):
            # We look at the recent messages to infer context
            history_text = " ".join(
                [m.content.lower() for m in context_window.messages if hasattr(m, "content")]
            )

            # Boost scores based on history, but less aggressively than the direct query
            bug_score += sum(1 for w in self.bug_keywords if w in history_text) * 0.3
            arch_score += sum(1 for w in self.arch_keywords if w in history_text) * 0.3
            code_score += sum(1 for w in self.code_keywords if w in history_text) * 0.3
            graph_score += sum(1 for w in self.graph_keywords if w in history_text) * 0.3

        weights = {
            "code": 1.0,
            "decisions": 0.0,
            "bugs": 0.0,
            "graph": 0.0,
        }

        if bug_score > 0:
            weights["bugs"] += 1.0 + (bug_score * 0.5)
            weights["code"] += 0.5

        if arch_score > 0:
            weights["decisions"] += 1.0 + (arch_score * 0.5)
            weights["code"] += 0.5

        if code_score > 0:
            weights["code"] += code_score * 0.5

        if graph_score > 0:
            weights["graph"] += 1.0 + (graph_score * 0.5)
            weights["code"] += 0.5

        total = sum(weights.values())
        if total > 0:
            for k in weights:
                weights[k] /= total

        return {"primary_intent": max(weights.items(), key=lambda x: x[1])[0], "weights": weights}
