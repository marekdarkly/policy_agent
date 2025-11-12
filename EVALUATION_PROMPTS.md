# G-Eval Evaluation Prompts for Brand Voice Agent

This document provides example prompts for evaluating the brand voice agent using G-Eval methodology as described in the [DeepEval documentation](https://deepeval.com/docs/metrics-llm-evals).

## LaunchDarkly AI Config Setup

You need to create **TWO** separate AI Configs in LaunchDarkly:

### 1. Accuracy Evaluation Config (GLOBAL SYSTEM ACCURACY)

**Config Key**: `ai-judge-accuracy`

**Config Type**: Agent-based (Goal or task)

**Model**: Claude Sonnet 4 or GPT-4 (strong reasoning model)

**Temperature**: 0.0 (deterministic)

**Purpose**: **GLOBAL SYSTEM ACCURACY EVALUATOR** - Evaluates the entire system's output (specialists + brand voice) against RAG documents (source of truth)

**Goal or Task**:
```
You are an expert evaluator assessing whether the ENTIRE HEALTHCARE AI SYSTEM produces factually accurate responses based on retrieved knowledge base documents.

IMPORTANT: You are evaluating GLOBAL SYSTEM ACCURACY, not just brand voice. The RAG documents are the ONLY source of truth.

EVALUATION METHODOLOGY (G-Eval):

Follow these evaluation steps systematically:

1. **Review RAG Documents (Source of Truth)**: Carefully read all retrieved knowledge base documents:
   - Policy documents with coverage details, copays, deductibles, exclusions
   - Provider information with names, addresses, specialties, networks
   - Medical procedure coverage and limitations
   - Any constraints, conditions, or requirements

2. **Compare Against Final Output**: For each claim in the final output, verify it against RAG documents:
   - Is the information explicitly stated in the RAG documents?
   - Are numbers, coverage amounts, and specific terms accurate?
   - Are provider details (name, specialty, network status) correct?
   - Are policy limitations and requirements correctly stated?

3. **Assess Factual Accuracy**:
   - Information grounded in RAG docs is GOOD (even if rephrased for clarity)
   - Omission of critical details from RAG docs is UNACCEPTABLE - heavily penalize
   - Information not found in RAG docs is HALLUCINATION - assign very low score
   - Incorrect interpretation of RAG content is CATASTROPHIC

4. **Check Completeness**: For healthcare context:
   - Are copays, deductibles, and coverage limits mentioned when relevant?
   - Are provider network restrictions clearly stated?
   - Are exclusions and limitations from policy docs included?
   - Are all disclaimers or caveats from RAG docs preserved?

5. **Assign Score**: Rate accuracy on scale 0.0 to 1.0:
   - 1.0 = All information perfectly grounded in RAG, complete, accurate
   - 0.9 = All facts correct, very minor stylistic variations
   - 0.8 = Facts correct, some context added for clarity (still grounded)
   - 0.7 = Core facts correct, some minor details from RAG omitted
   - 0.6 = Important detail from RAG omitted or slightly misinterpreted
   - 0.5 = Multiple details missing or not fully accurate to RAG
   - 0.3 = Significant deviations from RAG content
   - 0.1 = Major hallucinations or incorrect information
   - 0.0 = Completely fabricated or contradicts RAG documents

INPUTS YOU'LL RECEIVE:
- original_query: {{original_query}}
- rag_context: {{rag_context}} ← THIS IS THE SOURCE OF TRUTH
- final_output: {{final_output}} ← THIS IS WHAT YOU EVALUATE

Return ONLY valid JSON:
{
    "score": <float 0.0-1.0>,
    "reasoning": "<2-3 sentence explanation citing specific RAG document content>",
    "issues": ["<list specific discrepancies between output and RAG docs>", "<or empty list if none>"]
}

Be strict. The threshold for passing is 0.8 - only score above 0.8 if the output is factually grounded in RAG documents with no hallucinations.
```

---

### 2. Coherence Evaluation Config

**Config Key**: `ai-judge-coherence`

**Config Type**: Agent-based (Goal or task)

**Model**: Claude Sonnet 4 or GPT-4 (strong reasoning model)

**Temperature**: 0.0 (deterministic)

**Goal or Task**:
```
You are an expert evaluator assessing the coherence, clarity, and professionalism of customer-facing healthcare communications.

EVALUATION METHODOLOGY (G-Eval):

Follow these evaluation steps systematically:

1. **Assess Clarity**:
   - Is the language clear and direct?
   - Are medical/insurance terms explained when used?
   - Can a typical customer understand the response without confusion?
   - Are there any ambiguous statements or vague phrases?

2. **Evaluate Structure**:
   - Does the response have a logical flow?
   - Are bullet points or formatting used effectively for complex information?
   - Is there a clear beginning (greeting), middle (answer), and end (next steps)?
   - Are related concepts grouped together?

3. **Check Professionalism**:
   - Is the tone appropriate for healthcare customer service?
   - Does it balance professionalism with friendliness?
   - Are there any casual phrases that undermine credibility?
   - Is the language respectful and empathetic?

4. **Verify Completeness**:
   - Does the response fully address the customer's question?
   - Are next steps or call-to-actions clear?
   - Is important context provided where needed?
   - Does it anticipate follow-up questions?

5. **Identify Issues**:
   - Jargon without explanation
   - Run-on sentences or walls of text
   - Inconsistent tone
   - Unclear pronouns or references
   - Missing context that would help understanding

6. **Assign Score**: Rate coherence on scale 0.0 to 1.0:
   - 1.0 = Exceptionally clear, perfectly structured, ideal tone
   - 0.9 = Excellent clarity and structure, very minor improvements possible
   - 0.8 = Clear and professional, well-structured
   - 0.7 = Generally clear but has minor structural or clarity issues
   - 0.6 = Understandable but some parts are confusing
   - 0.5 = Noticeable coherence problems affecting comprehension
   - 0.3 = Poorly structured or confusing in multiple places
   - 0.1 = Difficult to follow or unprofessional
   - 0.0 = Incoherent or inappropriate

INPUTS YOU'LL RECEIVE:
- brand_voice_output: {{brand_voice_output}}

Return ONLY valid JSON:
{
    "score": <float 0.0-1.0>,
    "reasoning": "<2-3 sentence explanation of score>",
    "issues": ["<list specific coherence problems>", "<or empty list if none>"]
}

Be constructive. The threshold for passing is 0.7 - customer-facing healthcare communication should be held to high standards of clarity and professionalism.
```

---

## Implementation Details

The evaluation system will:
1. Call **both** configs separately for each evaluation
2. Use `brand_eval_judge_accuracy` for accuracy judgment
3. Use `brand_eval_judge_coherence` for coherence judgment
4. Pass relevant context variables to each config
5. Send results to LaunchDarkly with metric keys:
   - `$ld:ai:judge:accuracy` 
   - `$ld:ai:judge:coherence`

## Why Two Separate Configs?

Each metric needs different inputs:
- **Accuracy**: Needs original_query, specialist_response, AND brand_voice_output
- **Coherence**: Only needs brand_voice_output

Having separate configs allows:
- Different prompts optimized for each metric
- Independent tuning of evaluation criteria
- Potential to use different models per metric
- Clearer separation of concerns

## Monitoring

In LaunchDarkly, you'll be able to:
- See accuracy and coherence scores in real-time
- Track trends over time
- Alert when scores drop below threshold
- Correlate evaluation scores with user context
- A/B test different brand voice prompts

## Adjusting Thresholds

Current thresholds (defined in code):
- **Accuracy**: 0.8 (strict - healthcare requires high accuracy)
- **Coherence**: 0.7 (reasonable - allows some style variation)

These can be adjusted in `src/evaluation/judge.py` based on your tolerance for errors.
