---
name: setup-launchdarkly
description: Provision the LaunchDarkly AI Configs this project needs (triage_agent, policy_agent, provider_agent, scheduler_agent, brand_agent, ai-judge-accuracy, ai-judge-coherence) into your own LaunchDarkly project. Use when a user has cloned this repo, has a LaunchDarkly account, and needs the AI Configs created before `make`, `make togglehealth`, or `make togglebank` will run.
---

# Set up LaunchDarkly AI Configs for the ToggleHealth/Bank/Cell demo

This project resolves **every** agent prompt and model from LaunchDarkly AI Configs at
runtime — there are no hardcoded prompts. If those AI Configs don't exist in your
LaunchDarkly project, the workflow fails fast at the triage step. This skill creates
all seven of them from the canonical definitions in `scripts/ld_ai_configs/`.

You can reuse the **same shared AWS Bedrock Knowledge Bases** as the reference demo —
the policy/provider configs already point at them via `model.custom.awskbid`
(`PHC7IW8FTM` = ToggleHealth-Policy-KB, `RV4PHKDQA4` = ToggleHealth-Provider-KB). You
do **not** need your own KBs unless you want to swap in different data.

## What gets created

| AI Config key | Mode | Model (default) | Notes |
|---|---|---|---|
| `triage_agent` | agent | `us.anthropic.claude-sonnet-4-20250514-v1:0` | classifies + routes the query |
| `policy_agent` | agent | `us.meta.llama4-maverick-17b-instruct-v1:0` | RAG; `custom.awskbid=PHC7IW8FTM` |
| `provider_agent` | agent | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | RAG; `custom.awskbid=RV4PHKDQA4` |
| `scheduler_agent` | agent | `us.amazon.nova-pro-v1:0` | schedules callbacks |
| `brand_agent` | completion | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | rewrites in brand voice |
| `ai-judge-accuracy` | agent | `us.amazon.nova-pro-v1:0` | G-Eval accuracy judge |
| `ai-judge-coherence` | agent | `us.anthropic.claude-sonnet-4-20250514-v1:0` | G-Eval coherence judge |

All prompts keep the `{{domain}}` template variable, so the same configs power
ToggleHealth, ToggleBank, and ToggleCell.

## Steps

### 1. Confirm prerequisites
- The Python venv exists (`make install` has been run) — the script needs `requests` + `python-dotenv`.
- `.env` contains:
  - `LAUNCHDARKLY_ACCESS_TOKEN=api-...` — a token with the **writeProject** scope (Account settings → Authorization → Create token).
  - `LAUNCHDARKLY_PROJECT_KEY=<your-project-key>` — the project to create the configs in.
- The LaunchDarkly project already exists. (Create it in the LD UI first if needed; the script does not create projects.)

### 2. (Optional) Upload the tool library
Only needed if you want the agents to advertise tool definitions in LD AI Config
monitoring. The agents run fine without it.
```bash
make upload-tools
```

### 3. Create the AI Configs
```bash
# dry run first — prints exactly what it will create, calls no APIs
./venv/bin/python scripts/setup_ld_ai_configs.py --dry-run

# create them
./venv/bin/python scripts/setup_ld_ai_configs.py
```
The script is **idempotent**: configs that already exist are skipped, so it's safe to
re-run. A freshly-created AI Config is enabled with its single variation served by
default in every environment, so no targeting step is needed.

To target a project other than `LAUNCHDARKLY_PROJECT_KEY`, pass `--project <key>`.

### 4. Verify
- In the LaunchDarkly UI, open **AI Configs** in your project and confirm the seven keys above are present and enabled.
- Then run the app: `make togglebank` (or `make`, `make togglehealth`) and send a query. The backend log should show each agent "pulled from LaunchDarkly".

## Model availability

The default models above must be enabled in **your** AWS Bedrock account
(`us-east-1`). If some aren't (e.g. Llama 4 Maverick or Nova Pro), force a single
model you do have access to for every config:
```bash
LD_SETUP_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  ./venv/bin/python scripts/setup_ld_ai_configs.py
```
You can also change models per-config later in the LaunchDarkly UI.

## Using your own Knowledge Bases instead of the shared ones

The shared KB IDs live in two places:
- `scripts/ld_ai_configs/policy_agent.json` and `provider_agent.json` → `variation.model.custom.awskbid` (used by this skill).
- `src/tools/bedrock_rag.py` → `DOMAIN_KB_IDS` (hardcoded for togglebank/togglecell) and the `BEDROCK_POLICY_KB_ID` / `BEDROCK_PROVIDER_KB_ID` `.env` fallbacks (used for togglehealth).

To use your own data, build Bedrock Knowledge Bases from `data/markdown/` and replace
those IDs.

## Troubleshooting

- **`401`/`403`** — the access token lacks `writeProject`, or it's an SDK key instead of an API token (`api-...`).
- **`snippet "..." does not exist`** — you edited a definition to reference an LD prompt snippet. The bundled definitions are fully inlined; keep them inline or create the snippet first.
- **App still says `set_config was not called`** — the configs exist but the SDK key in `.env` is missing/invalid, or points to a different project than `LAUNCHDARKLY_PROJECT_KEY`.
