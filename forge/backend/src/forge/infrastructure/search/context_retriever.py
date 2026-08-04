"""Context retriever adapter — bridges use case port to vector infrastructure."""

from __future__ import annotations

from typing import Any

import structlog

from forge.infrastructure.search.embedding_service import EmbeddingError, EmbeddingService

logger = structlog.get_logger()


class ContextRetriever:
    """Adapter that implements IContextRetriever using vector store."""

    def __init__(
        self, vector_store: Any = None, dependency_graph: Any = None, embedding_service: Any = None
    ) -> None:
        self._embedding_service = embedding_service or EmbeddingService()
        self._vector_store = vector_store
        self._dependency_graph = dependency_graph
        self.retrieval_budget = 6500

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _apply_token_budget(self, results: list[dict], max_tokens: int) -> list[dict]:
        budgeted = []
        current_tokens = 0
        for res in results:
            content = res.get("payload", {}).get("content", "")
            tokens = self._estimate_tokens(content)
            if current_tokens + tokens <= max_tokens:
                budgeted.append(res)
                current_tokens += tokens
            else:
                break
        return budgeted

    async def retrieve(self, query: str, project_id, context_window: Any = None) -> dict:
        try:
            import json

            from forge.infrastructure.search.intent_router import IntentRouter

            router = IntentRouter()
            intent = router.route(query, context_window=context_window)
            weights = intent["weights"]

            query_embedding = await self._embedding_service.get_embedding(query, input_type="query")
            project_uuid = project_id.value if hasattr(project_id, "value") else project_id

            # 1. Semantic Search
            code_results = await self._vector_store.search_code(
                query_embedding, project_uuid, limit=1500
            )
            decisions = await self._vector_store.search_decisions(
                query_embedding, project_uuid, limit=1500
            )
            bugs = await self._vector_store.search_bugs(query_embedding, project_uuid, limit=1500)

            # 1b. Hybrid Search (Local Lexical + RRF Fallback) for Code
            from forge.infrastructure.search.lexical_scorer import LocalLexicalScorer

            scorer = LocalLexicalScorer()
            docs = [
                f"{r['payload'].get('file_path', '')}\n{r['payload'].get('name', '')}\n{r['payload'].get('content', '')}"
                for r in code_results
                if "payload" in r
            ]
            lex_scores = scorer.score(query, docs)

            k = 60
            semantic_ranks = {res["id"]: rank for rank, res in enumerate(code_results)}
            lexical_ranked = sorted(
                zip([res["id"] for res in code_results], lex_scores),
                key=lambda x: x[1],
                reverse=True,
            )
            lexical_ranks = {id_: rank for rank, (id_, _) in enumerate(lexical_ranked)}

            for res in code_results:
                r_sem = semantic_ranks[res["id"]]
                r_lex = lexical_ranks.get(res["id"], len(code_results))
                # Hybrid RRF score for code
                res["score"] = ((1.0 / (k + r_sem)) + (1.0 / (k + r_lex))) * weights["code"]
                res["type"] = "code"

            code_results.sort(key=lambda x: x["score"], reverse=True)

            unique_code_results = []
            seen_files_for_top = set()
            for res in code_results:
                fpath = res["payload"].get("file_path", "") if "payload" in res else ""
                if fpath not in seen_files_for_top:
                    seen_files_for_top.add(fpath)
                    unique_code_results.append(res)
                    if len(unique_code_results) >= 30:
                        break

            code_results = unique_code_results

            # 2. Graph Traversal (expand context)
            expanded_code = list(code_results)
            seen_files = {
                res["payload"].get("file_path") for res in code_results if res.get("payload")
            }

            if self._dependency_graph:
                for res in code_results:
                    file_path = res["payload"].get("file_path")
                    if not file_path:
                        continue

                    imports = await self._dependency_graph.get_imports(project_uuid, file_path)
                    dependents = await self._dependency_graph.get_dependents(
                        project_uuid, file_path
                    )

                    for edge in imports + dependents:
                        related_file = edge.target_file if edge in imports else edge.source_file
                        if related_file and related_file not in seen_files:
                            seen_files.add(related_file)
                            expanded_code.append(
                                {
                                    "id": f"graph_{related_file}",
                                    "score": res["score"] * (0.9 + weights.get("graph", 0.0)),
                                    "type": "code",
                                    "payload": {
                                        "file_path": related_file,
                                        "entry_type": "file",
                                        "name": related_file.split("/")[-1],
                                        "content": f"[Graph Context] Related to {file_path} via {edge.dependency_type.name if hasattr(edge.dependency_type, 'name') else str(edge.dependency_type)}",
                                    },
                                }
                            )

            # Process decisions and bugs with RRF based on semantic rank and intent weight
            for rank, res in enumerate(decisions):
                res["score"] = (1.0 / (k + rank)) * weights["decisions"]
                res["type"] = "decision"

            for rank, res in enumerate(bugs):
                res["score"] = (1.0 / (k + rank)) * weights["bugs"]
                res["type"] = "bug"

            # Merge all streams
            merged = expanded_code + decisions + bugs

            # 3. Reranking / Deduplication across all types
            merged.sort(key=lambda x: x["score"], reverse=True)

            unique_merged = []
            seen_code_paths = set()
            for res in merged:
                if res["type"] == "code":
                    fpath = res["payload"].get("file_path", "")
                    if fpath not in seen_code_paths:
                        seen_code_paths.add(fpath)
                        unique_merged.append(res)
                else:
                    # Keep all decisions and bugs, assuming they are inherently unique by ID
                    unique_merged.append(res)

            # Apply token budget
            # Fix payload content access in budget check by modifying _apply_token_budget to handle dict payloads
            budgeted = []
            current_tokens = 0
            for res in unique_merged:
                payload = res.get("payload", {})
                content_str = payload.get("content", "")
                if not content_str and res["type"] != "code":
                    content_str = json.dumps(payload)

                tokens = self._estimate_tokens(content_str)
                if current_tokens + tokens <= self.retrieval_budget:
                    budgeted.append(res)
                    current_tokens += tokens
                else:
                    break

            return {
                "relevant_code": [r for r in budgeted if r["type"] == "code"],
                "relevant_decisions": [r for r in budgeted if r["type"] == "decision"],
                "relevant_bugs": [r for r in budgeted if r["type"] == "bug"],
            }
        except EmbeddingError as e:
            logger.warning("embedding_failed_returning_empty_context %s", str(e))
            return {
                "relevant_code": [],
                "relevant_decisions": [],
                "relevant_bugs": [],
            }
        except Exception as e:
            logger.warning("context_retrieval_failed %s", str(e))
            return {
                "relevant_code": [],
                "relevant_decisions": [],
                "relevant_bugs": [],
            }
