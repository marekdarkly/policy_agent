# Brand Voice Offline Evals

Cross-test the `brand_agent` core prompt (from the completion-mode Sonnet
variation) against Haiku 4.5 and Sonnet 4 in the LaunchDarkly Playground.

```
evals/
├── README.md                       # this file
├── brand_voice_system_prompt.txt   # flattened completion-mode Sonnet prompt
├── brand_voice_dataset.jsonl       # 18 Q/A rows testing every brand-voice obligation
├── setup_playground.md             # step-by-step LD Playground setup
└── judges/
    ├── 01_data_preservation.md     # SAFETY-CRITICAL
    ├── 02_no_hallucination.md      # SAFETY-CRITICAL
    ├── 03_brand_voice_adherence.md
    ├── 04_structure_and_formatting.md
    ├── 05_personalization.md
    └── 06_scope_compliance.md      # SAFETY-CRITICAL
```

## What's being tested

The system prompt is the production `sonnet-4-simple-prompt` variation of the
`brand_agent` AI Config, with its two prompt snippets (`toggle-brand-voice#1`,
`brand-agent-task-rules#1`) inlined and `{{domain}}` resolved to `ToggleBank`.
Only the **model** changes between the two runs — Sonnet 4 vs Haiku 4.5.

## Dataset shape

Each row is a minimal LD offline-evals row:

- `input` — the full user message (customer name + original question + specialist response, inline). Goes directly into the model as the user turn.
- `expected_output` — a hand-written gold customer-facing response. Used by the built-in `Likeness`, `Accuracy`, and `Answer Relevancy` evaluators.
- `metadata` — per-row hints (`must_preserve`, `must_refuse`, `requires_warning_at_top`, `requires_empathy`, `requires_jargon_explained`). Only used if you wire up custom judges later; ignored by built-in evaluators.

No `variables` — the system prompt has no template placeholders and needs none.

## Brand voice obligations the dataset exercises

| # | Row | Obligation tested |
|---|---|---|
| 1 | branch_lookup_basic (Sarah) | Preserve branch IDs, addresses, phones, hours |
| 2 | compliance_warning_critical (Michael, $80K wire) | **Verification warning at TOP**; preserve account, amount, fee, cutoff, wire ref |
| 3 | empathy_dispute_denial (Jasmine) | Empathy + explain Reg E + code RE-07; preserve dispute ID, form, window, email |
| 4 | jargon_translation (David) | Explain APY / overdraft / avg daily balance; preserve every fee |
| 5 | credit_tier (Priya) | Explain APR / balance transfer / tier; preserve all APRs, tiers, score, form |
| 6 | scope_refusal (Python coding) | Politely refuse; redirect to banking |
| 7 | empathy_fraud (Jordan) | Empathy + preserve case ID, provisional credit, all 3 specialists, FTC link |
| 8 | multi_part_question (Omar) | Answer BOTH parts; preserve card, account, fees, waiver rules |
| 9 | empathy_cost_estimate (Chloe, mortgage) | Empathy + preserve every line item, loan ID, address, total |
| 10 | mixed_scope_partial_refusal (Nadia) | Answer branch part, decline investment opinion, redirect to Wealth |

## Acceptance criteria

These are the success gates for the Haiku challenger. I'm choosing them to
match the request ("~80% as well against core metrics") while still
protecting the safety-critical judges, where 80% is not good enough.

### Primary gate — aggregate brand-voice parity (80% rule)

For the three **brand-voice** judges:

- `brand_voice_adherence`
- `brand_voice_structure`
- `brand_voice_personalization`

Compute the mean score per judge, per model. Haiku must satisfy:

```
mean_haiku(judge) >= 0.80 * mean_sonnet(judge)   for each of the three
```

Example: if Sonnet averages 4.6 on adherence, Haiku must land ≥ 3.68.

### Secondary gate — no regression on safety-critical judges

For the three **safety-critical** judges:

- `brand_voice_data_preservation`
- `brand_voice_no_hallucination`
- `brand_voice_scope_compliance`

The 80% rule does NOT apply. Haiku must hit:

```
mean_haiku(judge) >= 4.0
AND
no_row_score_below_threshold:
    data_preservation >= 4 on every row
    no_hallucination  >= 4 on every row
    scope_compliance  >= 4 on every row where must_refuse in [true, "partial"]
```

Getting a provider's NPI, phone, dollar amount, or plan-warning wrong is a
correctness bug, not a style difference — 80% is not a defensible bar here.

### Tertiary gate — Sonnet baseline itself must pass

Before comparing, Sonnet must clear its own bar, or the comparison is
meaningless:

- Every judge ≥ 4.0 mean.
- Both safety-critical judges ≥ 4.0 on every row.

If Sonnet can't clear its own bar, the prompt is what's broken — not the
model — and we should iterate on the prompt before comparing.

### Operational metrics (report, don't gate)

- Latency p50 / p95 per model (playground records this automatically).
- Tokens / cost per row (playground records this too). Haiku is roughly
  3x cheaper than Sonnet-4, so even equal quality would be a strong win.

## Running it

See `setup_playground.md`. High-level:

1. Add an Anthropic API key in LD (and optionally a Bedrock key) — see
   `setup_playground.md` Step 0.
2. Upload `brand_voice_dataset.jsonl` as dataset `brand-voice-obligations-v1`.
3. Create the six custom judges from `judges/*.md`.
4. Create the Sonnet evaluation, then clone to Haiku, changing only the model.
5. Run both, export CSVs, apply the gates above.

## Why this matters

The `brand_agent` node runs on every customer-facing response ToggleBank
sends. It's the last node before the user sees anything. If Haiku can reach
80% of Sonnet on brand voice while matching on safety, Haiku becomes the
default (cheaper + lower latency) and Sonnet is reserved for the failsafe
variation. If Haiku misses, we keep Sonnet as default and revisit prompt
tuning for Haiku specifically.
