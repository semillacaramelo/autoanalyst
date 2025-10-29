# API Reference Documentation

Last Updated: 2025-10-28 21:51:29 (America/Bogota, UTC-5)

This document consolidates current, project-relevant API limits, behaviors, and integration notes for the AI-Driven Trading Crew. It focuses on free-tier constraints and practical guidance so the backend stays within quotas and remains reliable during development (paper trading).

---

## 1. Google Gemini API - Free Tier Constraints

Summary
- Provider: Google (Generative AI / Gemini family)
- Recommended model for this project: Gemini 1.5 Flash (balanced throughput / cost)
- Primary control surface: Google Generative AI / AI Studio / Generative AI API

Typical free-tier limits (project-level guidance)
- Gemini 1.5 Pro:
  - ~5 requests per minute (RPM)
  - ~25 requests per day (RPD)
  - Token throughput (example quota): large TPM values (model-dependent)
- Gemini 1.5 Flash (recommended):
  - ~10 requests per minute (RPM)
  - ~250 requests per day (RPD)
- Gemini 1.5 Flash‑Lite:
  - ~15 requests per minute (RPM)
  - ~1,000 requests per day (RPD)

Critical notes and best practices
- Quotas and limits are applied per Google Cloud project (not per API key). Monitor usage in Google AI Studio / Console.
- Exceeding limits returns HTTP 429; implement exponential backoff and retry with jitter.
- Daily quotas typically reset at midnight Pacific Time (PST/PDT) — verify per-project time zone on Google console.
- Model names and quotas change frequently; always confirm on the official docs before changing production logic.

Cost implications
- The public free quota (Flash model) is sufficient for small development runs.
- Primary cost driver: model API calls and token usage (large context responses = more tokens).
- Monitor token usage and prefer smaller prompts, succinct system messages, and caching where possible.

Sources / Further reading
- Google Generative AI / Gemini docs (models, quotas, pricing): https://developers.generativeai.google/ and https://developers.generativeai.google/pricing
- Google Generative AI Studio: https://cloud.google.com/generative-ai/studio

(IMPORTANT) Always consult the official Google docs for exact per-model quotas and pricing before large-scale usage.

---

## 2. Alpaca Markets API - Free Tier Constraints (Paper Trading)

Summary
- Provider: Alpaca Markets
- Mode used for development: Paper trading (recommended for safety)
- Base paper trading URL: https://paper-api.alpaca.markets
- Libraries commonly used: alpaca-py, alpaca-trade-api

Rate limits & data access (practical guidance)
- REST trading rate limit: commonly cited ~200 requests per minute (RPM) with smaller burst-per-second allowances. Implement a conservative client-side limit (e.g., 10 req/s burst, 200 req/min sustained).
- Market data:
  - IEX real-time (free via Alpaca, subject to IEX rules)
  - Historical bars: minute-level and higher (subject to plan and endpoint)
  - SIP / consolidated feeds (delayed or paid depending on plan)
- WebSocket streams for live updates (quotes/trades) do not count against REST request quotas — use streams for real-time signals whenever possible.

Paper-trading specifics & limitations
- Paper accounts simulate fills; they do not perfectly match live market fills (no guaranteed slippage model).
- Some order behaviors differ (fill timing, partial fills). Use paper mode for functional testing and strategy logic validation, but validate execution assumptions before going live.

Order types typically available in paper mode
- Market, Limit, Stop, Stop-Limit
- Fractional shares available for some market orders (library dependent)

Critical notes
- Paper and live use different keys / endpoints — never use live keys when DRY_RUN is enabled.
- Monitor account buying power and margin rules in tests.
- Respect daily and per-minute rate limits; use WebSocket for streaming market data and REST only for occasional historical or order operations.

Sources / Further reading
- Alpaca API documentation and rate-limit guidance: https://alpaca.markets/docs and https://alpaca.markets/docs/api-references/
- Alpaca Python SDK: https://pypi.org/project/alpaca-py/ and https://github.com/alpacahq/alpaca-trade-api-python

---

## 3. CrewAI Framework

Summary
- CrewAI: open-source multi-agent orchestration framework used to compose higher-level LLM agents and tools.
- License: typically MIT (verify repository)
- Use-case here: orchestrate data collection, signal generation, validation, risk checks, and execution as a sequential crew.

Practical integration notes
- CrewAI integrates with LLMs by exposing tools (annotated callables) used by agents. Each agent should keep LLM calls to a minimum; most heavy computation is done in pure Python.
- Local usage does not require CrewAI cloud or paid account; confirm version compatibility (Python 3.10–3.13 recommended in plan).
- CrewAI can add overhead (LLM orchestration + state management); prefer a linear/sequential process with explicit tool inputs for deterministic behavior and reproducible testing.

Sources / Further reading
- CrewAI repository (example): https://github.com/crewAIInc/crewAI (verify the canonical repo and license)
- CrewAI docs (if available) and examples in repo README

Cost implications
- CrewAI itself is free (open-source) but orchestration increases LLM call count; plan for caching and minimized LLM usage per agent.

---

## 4. Recommended Strategy for Free Tier Usage

Design principles
- Keep LLM calls minimal: perform numeric indicator computation in native Python (NumPy/pandas) and use LLM only for high-level reasoning, explanation, or non-deterministic tasks.
- Favor streaming WebSocket market data (Alpaca) for ticks and use REST only for historical fetches and order placement.
- Implement local caching to avoid repeated LLM or data calls for identical inputs.

Gemini optimization techniques
1. Prefer Gemini 1.5 Flash for better RPM/RPD.
2. Batch requests where possible: combine multiple questions into single LLM call when semantics allow.
3. Queue agent requests centrally and apply token-bucket or leaky-bucket rate limiter to avoid 429s.
4. Cache LLM responses for repeatable queries (e.g., identical task prompts) using a hashed task key + TTL.

Alpaca optimization techniques
1. Use WebSocket for live ticks and quotes to avoid REST usage for polling.
2. Batch historical requests (fetch multiple symbols in one call when supported).
3. Cache historical windows locally for re-use during backtesting or multiple agent runs.
4. Respect recommended client-side limits (e.g., keep REST calls < 200/min).

CrewAI optimization
1. Reduce number of agent-LMM round trips by moving deterministic logic to tools implemented in Python.
2. Configure agents to avoid unnecessary follow-ups or clarifying questions.
3. Use a single well-formed prompt per agent action and validate outputs via strict schemas.

Recommended primitives to implement
- Rate limiter (RPM/RPD) for Gemini manager
- Key rotation when using multiple Gemini keys
- Exponential backoff + jitter decorator for transient errors
- Response caching using LRU or persistent cache (SQLite/Redis) for repeated queries

---

## 5. Daily Usage Budget Calculation (example plan)

Assumption: 3 crew runs per day during development. Each crew run uses a modest number of LLM calls as orchestrated below.

Estimated LLM call counts (per run)
- DataCollectorAgent: 1-2 calls (health checks, error interpretation)
- SignalGeneratorAgent: 2-3 calls (reasoning or clarifying complex signals; pure calculations done in Python)
- SignalValidatorAgent: 3-4 calls (confirmation reasoning)
- RiskManagerAgent: 2-3 calls (position sizing explanations, edge-case checks)
- ExecutionAgent: 1-2 calls (error logging / confirmation)

Total estimated calls per run: ~14
Daily total (3 runs): 42 LLM calls/day

Example budget table

| Service | Operation | Calls per Run | Daily Total (3 runs) | Free Limit (example) | Status |
|---------|-----------|---------------:|---------------------:|----------------------|--------|
| Gemini (Flash) | Agent reasoning | ~15 | 45 | 250 RPD | ✅ Safe |
| Alpaca (REST) | Historical data / orders | ~10 | 30 | ~200 RPM (sustained) | ✅ Safe (use WS) |
| CrewAI | Orchestration overhead | small | small | N/A (framework) | ✅ OK |

Notes
- The "free limit" column is model- and account-dependent; verify live quotas per your Google project and Alpaca account dashboard.
- Maintain an operational buffer (target < 80% of daily quota).

---

## 6. Practical Implementation Checklist (developer guidance)

- Rate limiting
  - Implement a token-bucket or deque-based rate limiter for Gemini (RPM + RPD).
  - Track minute/day windows and block/queue calls when needed.

- Key rotation
  - Support multiple Gemini API keys and round-robin selection to spread load.

- Error handling
  - Treat HTTP 429 and 5xx as retriable where appropriate.
  - Use exponential backoff with randomized jitter to prevent thundering herds.

- Caching
  - Cache identical agent inputs for a configurable TTL.
  - Cache historical market-data windows to avoid repeated REST hits.

- Monitoring & telemetry
  - Count total LLM requests, per-key usage, and failures.
  - Alert when utilization exceeds thresholds (e.g., 75% of daily quota).

- Testing
  - Mock LLM responses for unit tests.
  - Use Alpaca paper trading for integration and end-to-end tests.

---

## 7. Quick-check: URLs & References

(Visit these canonical resources before launch to confirm the latest quotas & docs.)
- Google Generative AI docs & pricing
  - https://developers.generativeai.google/
  - https://developers.generativeai.google/pricing
  - Google AI Studio / Generative AI Studio: https://cloud.google.com/generative-ai/studio
- Alpaca API documentation
  - https://alpaca.markets/docs
  - Alpaca Python SDK: https://github.com/alpacahq/alpaca-trade-api
- CrewAI (example repository)
  - https://github.com/crewAIInc/crewAI

---

## 8. Appendix — Example Rate-Limiter & Budget Snippet (conceptual)

Pseudo-code summary (for implementation reference):

```python
# Rate limiter concept (token bucket / sliding window)
from collections import deque
from datetime import datetime, timedelta

minute_window = deque(maxlen=RPM)
day_window = deque(maxlen=RPD)

def record_request():
    now = datetime.utcnow()
    minute_window.append(now)
    day_window.append(now)

def can_send():
    # ensure oldest entries are outside windows
    ... 
```

---

## 9. Change log

- 2025-10-28 21:51:29 - Document created and populated with project-specific guidance and recommended URLs. Verify live quotas on the vendor dashboards before production rollout.