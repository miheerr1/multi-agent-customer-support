# Evaluation Framework

## Golden Dataset

10 test cases covering the routing decisions the Triage Manager must get right.

| Test Case | Input Summary | Expected Team | Priority | Missing Info |
|-----------|---------------|---------------|----------|--------------|
| TC01 | Duplicate billing charge with Account ID and last 4 of card | Billing_Agent | Medium | False |
| TC02 | App crashes plus refund demand without troubleshooting | Tech_Agent | High | False |
| TC03 | Legal threat plus refund demand | Escalation_Manager | Critical | False |
| TC04 | Legal threat (edge case with coercive language) | Escalation_Manager | Critical | False |
| TC05 | Billing issue, missing Account ID | Billing_Agent | Medium | True |
| TC06 | Tech issue, vague symptoms | Tech_Agent | Medium | True |
| TC07 | Account email change request | Account_Agent | Low | False |
| TC08 | Login issue blocking work | Tech_Agent | High | False |
| TC09 | Unauthorized transactions (suspected fraud) | Escalation_Manager | Critical | False |
| TC10 | System outage affecting multiple users | Tech_Agent | Critical | True |

## Metrics

**Exact Match** measures whether the model output assigns the correct team. Binary scoring, 1 for correct and 0 for incorrect.

**Instruction Following** measures whether the response follows strict JSON format, includes all required keys, and avoids extra conversational text.

Together these cover both functional correctness (right routing decision) and format compliance (parsable structured output).

## Results

| Iteration | Exact Match | Instruction Following |
|-----------|-------------|----------------------|
| Initial (before refinement) | 75% | 70% |
| After Round 1 refinement | 90% | 85% |
| Final (post-refinement) | 100% | 95%+ |

## Failure analysis

### TC04 - Adversarial input

**Initial failure:** Model classified the legal threat ticket as Billing because of the word "refund," ignoring the coercive language ("I will contact my lawyer").

**Root cause:** The initial prompt had topic keywords listed flat, with no hierarchy. The model defaulted to the topic match (refund implies billing) over the threat signal.

**Fix:** Added a constraints block to the system prompt with explicit override logic:

> If ticket mentions legal action, threats, or fraud, route to Escalation regardless of stated topic.

After this fix, TC04 routed correctly to Escalation_Manager on every retry.

### TC05 / TC10 - Missing info validation

**Initial failure:** Model marked these as `missing_info: false` when the required identifiers were absent.

**Root cause:** The original completeness check was loose. It said "verify the ticket contains identifying info" without specifying what counted per category.

**Fix:** Made the completeness check explicit per category:

> Billing: Account ID or last 4 of payment method  
> Tech: Product name, OS/browser, error code if available  
> Account: Account ID or registered email

After this fix, both cases correctly flagged `missing_info: true` with specific reasons.

## What this evaluation framework demonstrates

1. **Prompt iteration is the work.** The first version of any LLM system fails on adversarial inputs. The Golden Dataset turns iteration from intuition into a measurable engineering loop.

2. **Two metrics catch two failure modes.** Exact Match catches routing errors. Instruction Following catches format violations. Either alone would let real failures through.

3. **Failure analysis drives the next prompt version.** The TC04 fix came from understanding *why* the original prompt failed, not from random prompt tweaking. Documenting the why is what makes the system improvable.
