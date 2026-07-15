Project

AI Finance Voice Assistant — a multi-agent system that answers spoken
finance questions (e.g. "how much did I spend on subscriptions last month?")
using hierarchical agents, RAG grounding, and voice I/O.

Built to demonstrate: agentic architecture, voice-optimized prompting,
RAG grounding, hallucination self-checks, and latency-aware design.

Architecture

Sequential pipeline: Query → Research Agent → Finance Agent → Editor Agent → Response


Research Agent — pulls matching transactions from /data (CSV/mock DB) for a given query.
Finance Agent — plain Python/pandas analysis (sums, category breakdowns, trends). Not an LLM call.
Editor Agent — LLM call that turns analysis into a natural-language, voice-friendly answer.
Eval/Reflection step — checks every number in the final answer traces back to retrieved data/RAG docs. Logs pass/fail.
Orchestrator — glues the above in sequence; no heavy framework, plain Python.


Stack


Backend: Python + FastAPI
LLM: Groq via API
RAG: OpenAI embeddings + FAISS/Chroma
Voice: LiveKit (fallback: separate STT + TTS APIs)
Data: synthetic transactions CSV (Faker-generated)


Folder structure

/agents      → research_agent.py, finance_agent.py, editor_agent.py, orchestrator.py
/data        → synthetic transactions, knowledge base docs for RAG
/rag         → embedding + retrieval logic
/voice       → STT/TTS + LiveKit integration, TTS text formatter
/eval        → hallucination/self-reflection checks, latency logs

Conventions


Keep agent functions pure where possible (input in, output out) — easier to test without voice/LLM in the loop.
Test agents via CLI/text loop before wiring in voice.
TTS-bound text must be formatted explicitly (spell out dates, amounts, emails, phone numbers — no ambiguous shorthand).
Every Editor Agent response must be traceable to Research Agent data or RAG docs — no ungrounded numbers.
Log latency per agent step; total round-trip time should be visible in dev logs.


Current phase

Phase 0/1 — scaffolding + text-only agent pipeline (no voice yet).

Not doing (yet)


Real bank integration (Plaid) — using synthetic data only.
Heavy agent frameworks (LangGraph/CrewAI) — plain Python orchestration first.