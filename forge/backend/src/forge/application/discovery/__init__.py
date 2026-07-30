from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    content: str
    citations: List[str]

@dataclass
class ExplainResult:
    explanation: str
    citations: List[str]

@dataclass
class GraphResult:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    citations: List[str]

class ContextRetriever:
    def search(self, query: str) -> SearchResult:
        pass

class ReasoningEngine:
    def explain(self, file_path: str) -> ExplainResult:
        pass

class IGraphAdapter:
    def get_graph(self) -> GraphResult:
        pass

    def get_deps(self, target: str) -> GraphResult:
        pass

    def get_references(self, target: str) -> GraphResult:
        pass
