"""Prometheus metrics for monitoring."""
from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info

REQUEST_COUNT = Counter(
    "forge_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "forge_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_REQUESTS = Gauge(
    "forge_active_requests",
    "Number of active requests",
)

LLM_CALLS = Counter(
    "forge_llm_calls_total",
    "Total LLM API calls",
    ["model", "status"],
)

LLM_LATENCY = Histogram(
    "forge_llm_duration_seconds",
    "LLM API call latency in seconds",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

EMBEDDING_CALLS = Counter(
    "forge_embedding_calls_total",
    "Total embedding API calls",
    ["status"],
)

EMBEDDING_LATENCY = Histogram(
    "forge_embedding_duration_seconds",
    "Embedding API call latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

VECTOR_SEARCH_CALLS = Counter(
    "forge_vector_search_total",
    "Total vector search operations",
    ["collection", "status"],
)

VECTOR_SEARCH_LATENCY = Histogram(
    "forge_vector_search_duration_seconds",
    "Vector search latency in seconds",
    ["collection"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

CODE_ENTRIES_INDEXED = Counter(
    "forge_code_entries_indexed_total",
    "Total code entries indexed",
    ["language"],
)

APP_INFO = Info(
    "forge_app",
    "Forge application information",
)
