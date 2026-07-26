# Phase 3 Conversational Engine Architecture

The Forge Phase 3 Conversational Engine is built around a domain-driven architectural structure that facilitates context-aware reasoning, planning, and structured interactions with Large Language Models. It enforces token budgeting, deterministic retrieval context management, and read-only execution boundaries during planning.

## 1. Conversation Domain
The conversation domain orchestrates the lifecycle and state of a chat session, encapsulating messages, sessions, and summarization tracking.

- **Conversation Aggregate Root**: Manages the overarching state (`ACTIVE`, `IDLE`, `SUMMARIZED`, `ARCHIVED`) and holds a sequence of `ConversationMessage`, `ConversationSession`, and `ConversationSummary` records. It acts as the primary boundary for session operations.
- **ConversationSession**: Tracks active and ended sub-sessions within a single conversation, managing timestamps and metadata for specific interaction windows.
- **ConversationMessage**: Represents individual atomic interactions within a conversation (e.g., user queries and assistant responses) along with calculated token counts to facilitate context window generation.

## 2. Conversation Context Manager
The `ConversationContextManager` is responsible for building a token-budgeted, deterministically deduplicated context window for the LLM.

- **Deduplication**: Resolves duplicate chunks obtained from memory, vector databases, or graph stores by computing SHA-256 hashes of the content, ensuring stable sorting and deterministic behavior based on retrieval relevance scores.
- **Token Management**: Integrates closely with `TokenManager` to estimate tokens and slice recent messages dynamically, compressing older messages into a summary while prioritizing newly retrieved evidence within a strict contextual budget limit.

## 3. Reasoning Engine
The `ReasoningEngine` provides a strict grounding layer for factual QA and context-based analysis. 

- **Grounding Enforcement**: Formats the dynamic context window (summaries and messages) and injects highly constrained system prompts.
- **Strict Evidence Handling**: Mandates that the LLM's responses strictly derive from retrieved context chunks. It dictates that the system must respond with explicitly stating uncertainty if sufficient evidence is not present ("I am uncertain because the evidence is missing").
- **Citations**: Requires the LLM to emit citations for utilized facts, data, or code, mapping directly to the `RetrievedContext` provided by the Context Manager.

## 4. Planning Engine
The `PlanningEngine` coordinates multi-step structuring for complex intents like refactoring, debugging, or migrations.

- **Read-Only Constraints**: Operates under strict bounds, generating recommendations, comparisons, and implementation steps without executing changes natively or mutating code repositories automatically.
- **Structured Outcomes**: Generates detailed, step-by-step plans informed by the conversation history, previously generated summaries, and freshly retrieved context, keeping actions separated from analysis until execution is explicitly approved elsewhere in the system.
