# AgentControl Demo Script — ToggleBank (8 minutes)

Format: spoken prose with `[ACTION]` cues for what's happening on screen.

Audience: general technical (engineers, PMs, EMs) — assume product literacy, not LaunchDarkly literacy.

Speaker: Marek Pollix, Head of AI, LaunchDarkly.

What's deliberately cut from this version:

- The agent-graph explainer from the previous deck (audience already gets multi-agent systems).
- Targeting/guarded-rollout walkthrough (the previous demo covered this; can be added back in Q&A).
- Experimentation across prompt variations (same reason).

---

## SCREEN STUDIO RECORDING CHECKLIST

Distilled from the LD Screen Studio self-recording guide. Run through this once before each take.

**Setup (do once, day-of)**

- Mac only — Screen Studio is macOS-only.
- Recording + accessibility permissions granted, then computer restarted.
- Display set to 1920x1080 (16:9). On newer MacBooks, **System Settings → Display → "More Space"** to reach it.
- Single built-in display. Avoid external monitors (rare delayed mouse-over). 16" MacBook preferred.
- Notifications silenced, Do Not Disturb on, Slack/email closed.
- At least 20 GB free disk space.
- Unnecessary apps and syncing services closed.

**Browser**

- Install the **Window Resizer** Chrome extension. Use the green taskbar to set the browser to 1920x1080.
- Bookmarks bar visible, dark mode (LD standard for 2026).
- Only the tabs you need: ToggleBank UI, AgentControl dashboard, terminal app.

**Screen Studio app**

- Camera ON, mic ON, correct device selected for each.
- Use **Window** mode (not Screen) and select the Chrome window. Captures the browser bar cleanly.
- Test record 10 seconds and play back before the real take.

**During the take**

- Click **Start Recording**, then wait **3 seconds** before talking or clicking — gives the recorder time to engage.
- Move the cursor like a pointer: smooth, direct, pause on important elements *before* clicking.
- Hold **1–2 seconds** after every click before moving the cursor — viewers need time to register the action.
- No wiggling or looping the cursor. No fast scrolls. Slow, deliberate motion.
- Narrate calmly, conversationally. Don't rush. The script paces you; let it.
- If you're also on Riverside, keep the Screen Studio floating control out of the camera frame.

**Stop and save**

- Click the red Stop in the floating control box.
- **File → Save As** with a specific name, e.g. `Marek_Pollix_AgentControl_Demo_8min_4.29.26.screenstudio`.
- Compress the `.screenstudio` file.
- Upload to LD Google Drive (or send via Slack to the video team), with download access enabled.

The video team takes it from there — they apply the LD preset and export.

---

## SCRIPT

### 0:00 — Open (≈30s)

Hi, I'm Marek Marek Poliks, and I'm the Head of AI at LaunchDarkly. Over the next eight minutes I'm going to walk you through AgentControl — our control plane for AI agents — running end-to-end on ToggleBank, our retail banking demo. The thing I want you to take away is that managing your agents through feature flags lets you do a few things you literally can't do any other way: change the model on a live agent without redeploying, block a bad response and recover from it inside the SDK without redeploying, and run an optimization loop that publishes its own winning prompt back into the same place you change everything else.

`[ACTION]` On screen: ToggleBank chat UI on the right, AgentControl dashboard for `brand_agent` on the left.

ToggleBank is a multi-agent customer support system: a triage router, three RAG specialists that read from a banking knowledge base, and a brand voice agent that rewrites the specialist's draft into the response the customer actually sees. Every one of those agents is governed by an AgentControl config in LaunchDarkly, which means anything I'm about to change I'm changing the same way you'd change a feature flag — at runtime, scoped to whichever users I want.

---

### 0:30 — AgentControl walkthrough + prompt snippets (≈1:00)

`[ACTION]` Click into the `brand_agent` config. Show the active variation.

This is the brand_agent config — the agent that owns the rewrite at the end of the chain. Inside it I have a few variations, and each variation is a self-contained instance of "what this agent is": the model, the inference parameters, the system prompt, and any tools we give it. The targeting engine sitting underneath decides which variation each request gets, the same way targeting decides which feature flag value a user gets in the rest of LaunchDarkly.

The instructions field on this variation points at a prompt snippet — `{{snippet.brand-voice-base#3}}` — instead of holding the prompt inline. A snippet is a versioned chunk of prompt text that lives at the project level and gets rendered in by the SDK at config-resolve time. The reason that matters once you have more than two agents in your system is that we have a content team that owns ToggleBank's brand voice, and every agent that needs to sound like ToggleBank pulls in the same snippet by reference. When the content team updates it, the next call across every config picks up the new version automatically — so we never end up with three configs that copy-pasted the same paragraph eight months ago and have since drifted apart.

`[ACTION]` Click into the snippet. Show the version history (three versions, with the diff visible between v2 and v3).

---

### 1:30 — Live model swap, Sonnet 4.5 → Haiku 4.5 (≈1:00)

The simplest live change you can make in AgentControl is a model swap, so let me start there. The brand_agent runs Sonnet 4.5 today, which writes a great rewrite but is also one of the more expensive models we use. For a brand-voice transform — where we're not really doing reasoning, just rewriting in a particular tone — Haiku 4.5 is two-to-three times faster and roughly a fifth of the cost per token. The question is whether it's good enough.

`[ACTION]` Create a new variation `brand-haiku`. Set the model to `claude-haiku-4-5`. Reference the same brand-voice snippet. Save. In Targeting, route my own user_key to the new variation.

That's the entire change — no PR, no commit, no deploy — and it took me about thirty seconds. Let me ask the bot something.

`[ACTION]` In ToggleBank: "How do I open a Premium Checking account?"

Triage classified this as a policy question and handed it to the policy specialist, which retrieved the right docs from the policy knowledge base and drafted an answer. The brand_agent — now Haiku — rewrote that draft in ToggleBank's voice. End-to-end latency dropped from around four seconds to under two, and the cost tracker on the brand_agent stage shows the per-call cost dropped about 80%. In a normal stack that change is a code edit, a PR, a CI run, and a deploy.

---

### 2:30 — Offline evals (≈1:30)

Before I take this candidate variation any further than my own user, I want to know whether it actually held the line on the questions we care about. AgentControl handles regression testing through offline evals.

`[ACTION]` Briefly open `triage_agent_togglebank_eval.csv` to show its structure.

This is our regression set for the triage router — about five hundred labeled ToggleBank queries paired with their expected query type, escalation flag, and extracted product context. Every agent in our system has one of these CSVs, and they're version-controlled in our repo so the eval set evolves with the product.

`[ACTION]` In AgentControl, kick off an offline eval against the `brand-haiku` variation using the brand_agent eval set. Show the results table populating row by row.

For each row, AgentControl runs the variation against the input, scores the output against the expected answer using the same judges we run online, and reports per-row pass/fail with an aggregate at the top. You can see the candidate is passing 96% of the set — about a point and a half below the Sonnet baseline, but well above our 90% threshold for promotion. Because the eval result is attached to the variation itself, I can require it as a precondition for promoting the variation through targeting, which means in our environment a variation that hasn't been evaluated physically cannot get traffic.

---

### 4:00 — Guardrail and fallback, with trace (≈2:00)

Now the harder problem, which is what happens when a change you made looks fine in eval but does the wrong thing in production. Banks need their support agent to refuse off-topic questions, and the rule that enforces that lives in the prompt. Let me show you what it looks like when the prompt drops that rule, and then how AgentControl handles the recovery.

`[ACTION]` Add a third variation called `cost-cutting-prompt`. The system prompt is one line: "Be helpful. Answer the user's question." Save. Target my user_key. Confirm the guardrail toggle in the demo UI is OFF.

This is the leanest possible prompt — minimum tokens per call, lowest cost — but it dropped the topic-scope rule, which is the kind of thing you can absolutely ship by accident when you're optimizing for cost.

`[ACTION]` In ToggleBank: "Can you reverse a linked list in Python?"

There's the failure. The brand_agent took the cost-cutting variation and answered a leetcode question, because nothing in the prompt anymore tells it to refuse. ToggleBank just gave away free coding help, which is a real customer-trust regression on a real bank.

`[ACTION]` Flip the guardrail toggle ON. Re-ask the same question.

What just happened is a recovery loop the SDK runs on its own. The off-topic judge scored the model's draft response as a policy violation, and because that judge is configured as a blocking guardrail on this variation, the SDK didn't return the response to the application. It re-evaluated the same AgentControl config against the same context, but with `is_fallback=true` set as an additional context attribute. Our targeting rule for `is_fallback=true` routes that re-evaluation to a safe variation, which produced the response the customer actually saw — "I can only help with ToggleBank questions: accounts, branches, mortgages, or loans." All of that happened in under a second, inside the SDK, with no recovery code path the application engineer had to write.

`[ACTION]` Open the trace view for that request.

Every call in the system is OpenTelemetry-instrumented and exported to LaunchDarkly Monitor, so I can pull up the exact trace and walk through what happened — triage, the policy specialist's RAG call, the brand_agent call that got blocked along with the judge score that triggered the block, and the fallback brand_agent call that produced the response we shipped. That's the timeline you need to do a real post-incident review.

---

### 6:00 — Agent optimization (≈1:00)

We've been making prompt and model changes by hand so far. That works fine when you have one or two configs in production, but we have dozens, and the team that owns each config doesn't want to be in the prompt-tuning loop forever. Agent optimization runs that loop for you.

`[ACTION]` Open `brand_agent-opt-v1`. Show: candidate model list, judges, sample inputs.

You give it a list of candidate models, the judges the prompt has to satisfy, and a set of representative inputs — usually drawn from the same eval CSV we just looked at. The optimizer generates a candidate prompt, runs it against the inputs, scores the outputs with the judges, and either commits the winner back to AgentControl as a new variation or starts the next iteration.

The reason this is useful in practice is that the judges that gate the loop are the same judges that score the agent in production, so a variation the optimizer commits has already been measured against the bar your real users are evaluating it against. And the winner the optimizer publishes is just a regular variation in the config that gets the same targeting, evaluation, and rollback story as anything a human would have written.

---

### 7:00 — Insights (≈45s)

`[ACTION]` Open the Insights tab. Filter to brand_agent, last hour. Point at the cost-cutting variation's off-topic rate.

The Insights page is the aggregate view across every config and variation we run. It's where you go when you don't already know what's broken, because it surfaces patterns you'd otherwise have to write a query against your trace store for — which variations are producing the most negative feedback events, which models are burning the most tokens per resolved request, where judge scores have drifted week-over-week. You can see that the cost-cutting variation we were just demoing has a 60% off-topic rate over the last hour. If that variation had hit production for real, that's the signal I'd act on — pull it from targeting before it makes a measurable dent in CSAT.

---

### 7:45 — Close (≈15s)

Everything you just saw runs through one control plane: the place that holds the live model assignment also holds the regression evals, the judge configurations, the targeting rules that did the recovery, the optimizer's published winner, and the Insights view sitting on top of all of it. You can change any of it at runtime, and you can target any of it the same way you'd target a feature flag — by user, environment, or segment. 