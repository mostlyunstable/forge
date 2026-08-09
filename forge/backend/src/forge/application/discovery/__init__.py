from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    content: str
    citations: list[str]


@dataclass
class ExplainResult:
    explanation: str
    citations: list[str]


@dataclass
class GraphResult:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    citations: list[str]


class ContextRetriever:
    def search(self, query: str) -> SearchResult:
        raise NotImplementedError()


class ReasoningEngine:
    def explain(self, file_path: str) -> ExplainResult:
        raise NotImplementedError()


class IGraphAdapter:
    def get_graph(self) -> GraphResult:
        raise NotImplementedError()

    def get_deps(self, target: str) -> GraphResult:
        raise NotImplementedError()

    def get_references(self, target: str) -> GraphResult:
        raise NotImplementedError()
