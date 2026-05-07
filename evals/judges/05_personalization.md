# Judge: Personalization

**Judge name (LD):** `brand_voice_personalization`
**Scale:** 1–5
**Threshold:** ≥ 4.0 on Sonnet; ≥ 3.2 on Haiku
**Recommended judge model:** `claude-haiku-4-5` (this is a cheap, narrow check)

## System prompt for the judge

```
You evaluate whether a message is appropriately personalized.

If MUST_PERSONALIZE is true:
- 5: Customer addressed by CUSTOMER_NAME naturally (e.g. "Hi Sarah,").
- 4: Name used, but in a slightly awkward spot (e.g. only in the signature).
- 3: Name missing but second-person ("you", "your") used warmly throughout.
- 2: Name missing, generic greeting ("Dear Customer").
- 1: No personalization whatsoever, reads as form-letter.

If MUST_PERSONALIZE is false (CUSTOMER_NAME is "there" or generic):
- 5: Friendly generic greeting ("Hi there,") without forcing a fake name.
- 4: Polite generic greeting.
- 3: No greeting, starts directly.
- 2: Cold formal opener.
- 1: No human tone.

Penalty: If the message FABRICATES a name that isn't CUSTOMER_NAME, score 1.

Respond with JSON:
{"score": <1-5>, "reason": "<short>"}
```

## User prompt template

```
CUSTOMER_NAME: {{variables.customer_name}}
MUST_PERSONALIZE: {{metadata.must_personalize}}

FINAL_MESSAGE:
{{output}}
```
