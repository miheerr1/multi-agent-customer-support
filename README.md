# Multi-Agent Customer Support Triage System

A production-style multi-agent system that classifies and routes customer support tickets, built on Google CX Agent Studio with a Human-in-the-Loop safety gate and a Golden Dataset evaluation framework.

**Stack:** Google CX Agent Studio, Vertex AI Agent Builder, Flowise AI, Gemini 2.5 / 3 Flash, Python, JSON Schema

---

## What this system does

A Triage Manager classifies incoming support tickets and routes them in strict JSON to one of three specialist sub-agents (Billing, Tech, Escalation), with explicit negative constraints to prevent scope creep and a Human-in-the-Loop gate that pauses execution for human approval on high-impact actions.

End-to-end execution runs in **2.15 seconds** across a 5-step audit trail.

---

## Architecture

The system uses a Supervisor/Execution pattern, separating classification from resolution. The Triage Manager never tries to solve tickets, it only routes them.

```
                    ┌─────────────────────┐
                    │   Incoming Ticket   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Triage Manager     │
                    │  (Supervisor)       │
                    │  Outputs strict     │
                    │  JSON routing       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼─────┐
       │ Billing     │  │   Tech      │  │Escalation │
       │ Agent       │  │   Agent     │  │ Manager   │
       │             │  │             │  │           │
       │ Cannot      │  │ Cannot      │  │ Cannot    │
       │ authorize   │  │ guarantee   │  │ admit to  │
       │ refunds     │  │ fix times   │  │ legal     │
       └─────────────┘  └─────────────┘  └───────────┘
                               │
                    ┌──────────▼──────────┐
                    │  HITL Safety Gate   │
                    │  (high-impact only) │
                    └─────────────────────┘
```

---

## Key design decisions

1. **Supervisor/Execution pattern** separates classification from resolution, so routing decisions are auditable independent of how specialists behave.

2. **Strict JSON routing** means the Triage Manager outputs structured state instead of natural-language hints, making routing testable and traceable.

3. **Negative constraints in specialists** prevent scope creep at the agent level. Billing Agent cannot authorize refunds, Tech Agent cannot guarantee fix timelines, Escalation Manager cannot make legal admissions.

4. **HITL safety gate** pauses high-impact actions (price changes greater than 10 percent, legal escalations) for human approval before executing.

---

## Evaluation framework

Built a Golden Dataset of 10 test cases covering:

- Happy path (clear billing issue with complete info)
- Policy mismatch (refund demand without troubleshooting)
- Adversarial attacks (legal threats, coercion)
- Missing information (edge cases)
- System outages (multi-user impact)

Used Vertex AI's Evaluate tool with multi-metric scoring:

- **Exact Match** for routing accuracy
- **Instruction Following** for JSON format compliance

**Result:** Pass rate improved from 75% to 100% through targeted prompt refinement after analyzing failure cases.

See [docs/evaluation.md](docs/evaluation.md) for full test cases and results.

---

## Documented failure modes

Five real Cost-of-Autonomy failures with production-grade mitigations:

| Failure | Cause | Mitigation |
|---------|-------|------------|
| LLM arithmetic drift | LLM computing percentages directly | Deterministic Python calculator tool |
| Sign convention inconsistency | Each agent computing its own sign | Pass values as session params, do not recompute |
| Runaway routing loops | No explicit termination signal | Termination rule plus end_session call |
| Mid-execution quota depletion | 5 to 6 extra LLM calls per correction loop | Exponential backoff plus idempotent retry |
| Credential inheritance bugs | Each Flowise node needs explicit credentials | Pre-flight credential validator |

See [docs/failure-modes.md](docs/failure-modes.md) for full analysis.

---

## What's in this repo

- **prompts/** Production XML system prompts for the Triage Manager and all specialist sub-agents
- **tools/** Python tool function for deterministic internal price retrieval
- **docs/** Architecture, prompt iteration, evaluation framework, failure analysis

The agents themselves run inside Google CX Agent Studio and Vertex AI Agent Builder. This repo documents the design, prompts, evaluation framework, and failure analysis that define how the system behaves.

---

## Context

Built as part of BCIS 5910 Designing AI Solutions for Business at the University of North Texas, taught by Dr. Chih-Hao Ku. The project covers Modules 6, 7-8, 10, 11, and 12 of the course, building from a single-agent pricing tool to a fully evaluated production-style multi-agent system.

---

**Author:** Mihir Sali  
[LinkedIn](https://linkedin.com/in/mihir-sali-768128229)
