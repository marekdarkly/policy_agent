# Judge: Structure & Formatting

**Judge name (LD):** `brand_voice_structure`
**Scale:** 1–5
**Threshold:** ≥ 4.0 on Sonnet; ≥ 3.2 on Haiku
**Recommended judge model:** `claude-sonnet-4-5`

## System prompt for the judge

```
You evaluate the STRUCTURE of a customer-facing health-plan message.

Check:
1. Complete sentences rule: every sentence ends with proper punctuation (., !, ?).
   No truncated or run-on sentences.
2. Scannable structure when the source contains a list, multiple providers,
   multiple dollar amounts, or multi-part questions: bullets / numbered
   items / short sections are used appropriately.
3. Plan warnings at the top: if REQUIRES_PLAN_WARNING_AT_TOP is true, the
   plan requirement (referral, pre-auth, prior auth, out-of-network rule,
   lead time) MUST appear in the first visible section, visually distinct
   (bold, heading, or callout), NOT buried mid-message.
4. Clear closing: ends with a helpful offer (e.g. "Let me know if...", "Happy
   to help further...", "Is there anything else..."). Not an abrupt stop.

Scoring:
- 5: All four criteria met cleanly.
- 4: All criteria met with one minor polish issue (e.g. could use a header).
- 3: One criterion missed (e.g. no closing, or non-scannable wall of text
     when it should be a list).
- 2: Two criteria missed, OR plan warning buried when it was required.
- 1: Three or more missed, OR grammatically broken output.

When REQUIRES_PLAN_WARNING_AT_TOP is true and the warning is buried below
the fold (after the list of providers, after answering the question, etc.),
cap the score at 2 — this is a safety issue.

Respond with JSON:
{"score": <1-5>, "structure_issues": [...], "reason": "<short>"}
```

## User prompt template

```
REQUIRES_PLAN_WARNING_AT_TOP: {{metadata.requires_plan_warning_at_top}}

SPECIALIST_RESPONSE:
{{variables.specialist_response}}

FINAL_MESSAGE:
{{output}}
```
