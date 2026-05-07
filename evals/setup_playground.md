# Brand Voice Offline Eval — LaunchDarkly Playground Setup

This is a step-by-step guide for standing up the Haiku-vs-Sonnet offline
evaluation in the LaunchDarkly Playground.

The goal:

- Hold the **prompt** constant (the completion-mode Sonnet prompt from the
  `brand_agent` AI Config, flattened in `brand_voice_system_prompt.txt`).
- Hold the **dataset** constant (`brand_voice_dataset.jsonl`).
- Vary only the **model**: `claude-sonnet-4-5` vs `claude-haiku-4-5`.
- Score each run with the six judges in `judges/`.
- Compare aggregate scores and latency / cost.

## Prerequisite — add the Anthropic API key in LaunchDarkly

Both candidate completions (Sonnet + Haiku) AND the six judges run on native
Anthropic. You only need one key.

1. Open project `mpoliks-ld-demo`.
2. Left nav → **AI** → **Playground**.
3. Top right → **Manage API keys** → **Add integration**.
4. Name: `anthropic-playground`.
5. Provider: **Anthropic**.
6. Paste your Anthropic API key, accept terms, save.

> Caveat vs. production: our prod `brand_agent` runs on Bedrock
> (`us.anthropic.claude-sonnet-4-20250514-v1:0` and
> `us.anthropic.claude-haiku-4-5-20251001-v1:0`). Native Anthropic
> (`claude-sonnet-4-5` / `claude-haiku-4-5`) is the same model family — fine
> for a prompt-vs-model quality comparison. If Haiku passes here we'd still
> re-run a small smoke sample on Bedrock before flipping the default.

## Step 1 — Upload the dataset

1. In the left nav → **AI** → **Library** → **Datasets** → **Upload dataset**.
2. Drop `evals/brand_voice_dataset.jsonl`.
3. Name it `brand-voice-obligations-v1`.
4. Save. Status should flip to **ready**.

The dataset has 10 rows covering every brand-voice obligation with minimal redundancy:

| # | Category | Critical obligation tested |
|---|---|---|
| 1 | branch_lookup_basic | Preserve Branch IDs, addresses, phones, hours |
| 2 | compliance_warning_critical | Large-wire verification warning at TOP |
| 3 | empathy_dispute_denial | Empathy + explain Reg E / code RE-07 |
| 4 | jargon_translation | Explain APY / overdraft / avg daily balance |
| 5 | credit_tier | Explain APR / tier / BT; preserve all APRs + score + form |
| 6 | scope_refusal | Refuse Python coding help; redirect |
| 7 | empathy_fraud | Reassurance + preserve case, all 3 specialists, FTC |
| 8 | multi_part_question | Answer BOTH parts (lost card + overdraft) |
| 9 | empathy_cost_estimate | Empathy + preserve every mortgage closing line item |
| 10 | mixed_scope_partial_refusal | Partial refusal (answer branch, decline investment opinion) |

## Step 2 — Create the Sonnet evaluation

1. AI → **Playground** → **New evaluation**.
2. Name: `brand-voice-sonnet4-baseline`.
3. Provider: Anthropic.
4. Model: `claude-sonnet-4-5`.
5. Parameters: `temperature=0.7`, `max_tokens=2000` (matches production).
6. Messages:
   - **System:** paste the full content of `evals/brand_voice_system_prompt.txt`.
   - **User:** leave as `{{input}}` (the dataset row's `input` field is piped
     straight into the user message — this is how the playground uses the
     `input` column by default).
7. Variables panel: there are **no** template variables in this prompt. Leave
   the panel empty. Each row's `input` already contains the customer name,
   original question, and specialist response inline.
8. Dataset: select `brand-voice-obligations-v1` → All rows.
9. Acceptance criteria panel → attach the built-ins below (or create the six
   custom judges first if you want Phase 2 signal):
   - **Accuracy** — threshold 0.80
   - **Answer Relevancy** — threshold 0.80
   - **Misinformation** — threshold 0.90
   - **Toxicity** — max 0.05
   - *(Optional)* **Likeness** — threshold 0.60 against `expected_output`.
     Our gold responses are hand-written exemplars, not verbatim targets, so
     Likeness will be noisy; useful as a tiebreaker, not a gate.

## Step 3 — Clone as the Haiku evaluation

1. From the Sonnet evaluation page → overflow menu → **Duplicate**.
2. Rename the copy to `brand-voice-haiku45-challenger`.
3. Change ONLY the model to `claude-haiku-4-5`.
4. Everything else identical — system prompt, user message, variables, dataset,
   judges, temperature, max_tokens.

## Step 4 — Create the six custom judges

For each file in `evals/judges/` (`01_data_preservation.md` through
`06_scope_compliance.md`):

1. AI → **Library** → **Judges** → **New judge** (or AI Configs → New →
   select **Judge** mode, depending on your LD version).
2. Name: as stated at the top of the judge file (e.g. `brand_voice_data_preservation`).
3. Model: as stated in the judge file (Sonnet for the factual/critical ones,
   Haiku for the cheap narrow `personalization` one).
4. System prompt: copy the block under "System prompt for the judge".
5. User prompt: copy the block under "User prompt template".
6. Output format: JSON with `score` field (1–5).
7. Save.

Attach all six to both evaluations (Sonnet baseline + Haiku challenger) under
**Acceptance criteria**.

## Step 5 — Run both

1. Open the Sonnet evaluation → **Save and run**.
2. Open the Haiku evaluation → **Save and run**.
3. Each run processes all 18 rows. Expect ~5–10 minutes for both to complete.

## Step 6 — Compare (acceptance criteria)

See `evals/README.md#acceptance-criteria` for the decision rule. The quick
version:

- **Sonnet baseline must hit:** every judge ≥ 4.0 mean, and every
  safety-critical judge ≥ 4.0 on every row.
- **Haiku passes if:** it matches Sonnet within 80% on brand-voice judges
  AND ties Sonnet on the two safety-critical judges (data preservation,
  no hallucination, scope compliance).
- Secondary: latency p95 and cost per row.

Export both runs as CSV from the Output tab and diff the per-row scores to
see exactly which scenarios Haiku regresses on.
