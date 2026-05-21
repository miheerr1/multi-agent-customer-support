# Documented Failure Modes (Cost of Autonomy)

Five real failure modes observed while building this system, with the production-grade mitigations each one would need.

## 1. LLM arithmetic drift

**What happened:** When the Pricing Manager agent computed `percentageGap` directly with the LLM, it returned `-20.0%` on inputs where the correct value (from manual calculation) was approximately `-26.5%`. A 6.5 percentage point error on a number that drives a real business decision.

**Why it matters:** A manager approving a "20% discount" is making a different commitment than approving a "26.5% discount." The discount, the lost margin, and the dashboard the analyst sees afterward all diverge from reality. Compounded across SKUs, this becomes a material P&L error.

**Mitigation:** Replace the LLM math with a deterministic Python calculator tool. Any number that humans make irreversible decisions on should be math-verifiable, not LLM-generated. The LLM stays in the loop for *reasoning about* the number, never for *computing* it.

---

## 2. Sign convention inconsistency between handoffs

**What happened:** The Final Decision agent emitted JSON with `percentageGap: -20` and `recommendation: "Increase"`. The Pricing Manager had originally classified this case as a price decrease. Each agent applied its own sign convention.

**Why it matters:** Multi-agent systems can produce outputs that look correct at each individual step but are logically inconsistent when read end-to-end. A handoff that doesn't preserve state turns coherent reasoning into garbled output.

**Mitigation:** Pass the canonical decision (`recommendation`) itself as a session parameter, so downstream agents read it instead of recomputing it. The agent that owns a decision is the only agent that ever sets that decision.

---

## 3. Runaway routing loops

**What happened:** Early CX Agent Studio testing crashed with "10 reasoning loops exceeded" because there was no explicit termination signal to Final Decision, plus inconsistent sub-agent naming (Title Case vs snake_case) that confused the routing engine.

**Why it matters:** A probabilistically routed system with no explicit termination can crash catastrophically. In production, this would mean a transaction that consumed N times the expected LLM budget before failing, with no usable output.

**Mitigation:** Two fixes. First, rename all sub-agents to strict snake_case so the description-matching engine has consistent identifiers. Second, add an explicit "CRITICAL TERMINATION RULE" to the Final Decision instructions that mandates a call to `end_session` upon JSON output. Without an explicit terminator, the engine treats every step as potentially continuable.

---

## 4. Mid-execution quota depletion

**What happened:** A correction loop (user override followed by recalculation) failed mid-execution with HTTP 429 RESOURCE_EXHAUSTED. The Safety Gate had correctly captured the override, but the 5 to 6 extra LLM calls required to re-route, recalculate, re-verify, re-approve, and re-commit consumed the remaining quota before the loop could finish.

**Why it matters:** A user whose manual override silently fails mid-loop ends up with inconsistent session state (`approval_status: "Correction"` but no final commit) and no automatic recovery path. From the user's perspective, the system accepted their input and then disappeared.

**Mitigation:** Three layers. (1) Reserve a quota pool specifically for in-flight correction loops, separate from steady-state traffic. (2) Add exponential backoff and idempotent retry logic so transient failures don't lose state. (3) Set a maximum LLM-calls-per-transaction limit that gracefully escalates to human review instead of aborting silently.

---

## 5. Credential inheritance assumption

**What happened:** A Flowise loop architecture failed at runtime because the Quality Gate node didn't have `GOOGLE_API_KEY` set, even though the Copywriter and Brand Policy Scorer agents on the same flow had credentials configured.

**Why it matters:** Flowise treats every agent node's credentials as independent. The bug was invisible at design time and only surfaced when execution reached the unconfigured node, which would be hours into a production run.

**Mitigation:** A pre-flight validator that scans every LLM-dependent node in a flow and checks for credentials before activating the deployment. Move the failure from runtime to deployment time, where it's cheap to fix.

---

## What these five failures have in common

Each one only appeared in a multi-agent context. None of them would have surfaced in single-agent testing. The Cost of Autonomy isn't a single tax, it's a category of failures that emerge from coordination overhead between agents:

1. **Math gets fuzzier** when no one agent owns the calculation deterministically.
2. **State gets garbled** when handoffs aren't strictly typed.
3. **Termination gets ambiguous** when routing is probabilistic.
4. **Cost gets unpredictable** when LLM-calls-per-transaction is unbounded.
5. **Failures hide** when configuration is per-node instead of per-flow.

The mitigations above are the production toll any multi-agent system has to pay. A demo can ignore them. A production deployment cannot.
