#!/usr/bin/env python3
"""
chat_rag_guardrail.py – Terminal chat bot with:
  • LaunchDarkly AI Configs           – prompt/model governance
  • S3-backed RAG retrieval           – reference source
  • Bedrock inline guardrail          – hallucination & relevance check
  • Live metrics & user feedback      – sent back to LaunchDarkly

Keys come from .env in the same folder.
"""
import os, sys, json, signal, hashlib, logging, textwrap, time, uuid, random
from typing import List, Dict, Any, Union
from pathlib import Path

import dotenv, boto3, botocore
import ldclient
from ldclient.config import Config
from ldclient import Context
from ldai.client import LDAIClient, AIConfig, ModelConfig
from ldai.tracker import FeedbackKind
from user_service import get_current_user_context, get_user_service

# ── setup & helpers ───────────────────────────────────────────────────────────
# Load .env from project root (one level up from backend/)
project_root = Path(__file__).parent.parent
dotenv.load_dotenv(project_root / ".env")

LD_SDK   = os.getenv("LAUNCHDARKLY_SDK_KEY")
REGION   = os.getenv("AWS_REGION", "us-east-1")

# Hardcoded AI config keys
LD_KEY = "toggle-rag"
LD_JUDGE_KEY = "llm-as-judge"

# These will now come from LaunchDarkly AI config instead of env vars
# GR_ID    = os.getenv("AWS_GUARDRAIL_ID")
# GR_VER   = os.getenv("AWS_GUARDRAIL_VERSION", "DRAFT")
# KB_ID    = os.getenv("RAG_BUCKET")  
# PREFIX   = os.getenv("RAG_PREFIX", "rag/passages/")  

if not LD_SDK:
    sys.exit("✖  Missing required env vars – check your .env file")

# LaunchDarkly initialization removed - clients will be passed as parameters

# AWS clients with SSO authentication
def initialize_aws_clients():
    """
    Initialize AWS clients using SSO profile 'aiconfigdemo'.
    This is the recommended secure authentication method.
    """
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ProfileNotFound, TokenRetrievalError
    
    region = os.getenv("AWS_REGION", "us-east-1")
    
    try:
        print("Debug: Using AWS SSO profile 'aiconfigdemo'...")
        session = boto3.Session(profile_name='aiconfigdemo', region_name=region)
        bedrock = session.client("bedrock-runtime")
        bedrock_agent = session.client("bedrock-agent-runtime")
        
        # Test the credentials with a simple API call
        import botocore
        try:
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ Successfully authenticated as: {identity.get('Arn', 'Unknown')}")
            return bedrock, bedrock_agent
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] in ['InvalidUserID.NotFound', 'AccessDenied']:
                raise NoCredentialsError()
            raise
            
    except ProfileNotFound:
        print("\n❌ AWS SSO PROFILE ERROR:")
        print("═" * 50)
        print("AWS profile 'aiconfigdemo' not found.")
        print("\n🔧 SETUP REQUIRED:")
        print("   aws configure sso")
        print("   # Use profile name: aiconfigdemo")
        print("   # Use your SSO start URL: https://your-org.awsapps.com/start/#")
        print("   # Use region: us-east-1")
        print("═" * 50)
        raise Exception("AWS SSO profile 'aiconfigdemo' not configured")
        
    except TokenRetrievalError:
        print("\n❌ AWS SSO SESSION EXPIRED:")
        print("═" * 50)
        print("Your AWS SSO session has expired.")
        print("\n🔧 REFRESH REQUIRED:")
        print("   aws sso login --profile aiconfigdemo")
        print("   # This will open your browser to re-authenticate")
        print("═" * 50)
        raise Exception("AWS SSO session expired - please run: aws sso login --profile aiconfigdemo")
        
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("\n❌ AWS SSO CREDENTIAL ERROR:")
        print("═" * 50)
        print(f"AWS SSO credentials issue: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. aws sso login --profile aiconfigdemo")
        print("   2. aws sts get-caller-identity --profile aiconfigdemo")
        print("   3. Check your SSO permissions")
        print("═" * 50)
        raise Exception(f"AWS SSO credentials failed: {e}")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED AWS ERROR: {e}")
        print("═" * 50)
        print("🔧 DEBUG STEPS:")
        print("   1. aws sso login --profile aiconfigdemo")
        print("   2. aws configure list --profile aiconfigdemo")
        print("   3. Check your internet connection")
        print("═" * 50)
        raise Exception(f"Unexpected AWS error: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")

def print_box(title: str, text: str) -> None:
    lines = textwrap.wrap(text, 78)
    width = max(len(title), *(len(l) for l in lines)) + 4
    print("┌" + "─"*width + "┐")
    print("│ " + title.center(width-2) + " │")
    print("├" + "─"*width + "┤")
    for l in lines:
        print("│ " + l.ljust(width-2) + " │")
    print("└" + "─"*width + "┘")

def get_kb_passages(question: str, kb_id: str, bedrock_agent, user_context: Context = None) -> str:
    """
    Query AWS Bedrock Knowledge Base using vector search with customer-specific filtering
    """
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': question
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 15  # Get more results for better filtering
                }
            }
        )
        
        passages = []
        filtered_passages = []
        # Extract all passages first
        for result in response.get('retrievalResults', []):
            content = result.get('content', {}).get('text', '')
            if content:
                passages.append(content)
        # Filter passages based on user context
        if user_context:
            current_user_name = user_context.name
            # Access LaunchDarkly context attributes properly
            context_dict = user_context.to_dict()
            current_user_tier = context_dict.get("tier", "").lower() if "tier" in context_dict else ""
            
            for passage in passages:
                passage_lower = passage.lower()
                
                # Skip passages that contain other customer profiles
                if "name:" in passage_lower and current_user_name.lower() not in passage_lower:
                    # This passage contains another customer's profile, skip it
                    logging.info(f"Filtered out other customer profile: {passage[:50]}...")
                    continue
                
                # For tier-specific information, only include relevant tiers
                if any(tier_word in passage_lower for tier_word in ["diamond", "platinum", "gold", "silver"]):
                    # Keep only if it explicitly references the *current* tier or is a purely generic statement.
                    # We now treat any reference to other tiers as out-of-scope, even if the sentence
                    # contains a phrase like "tiers receive". This prevents the guardrail from rejecting
                    # a response that might accidentally surface benefits for the wrong tier.

                    mentions_current_tier = current_user_tier and current_user_tier in passage_lower
                    mentions_other_tiers = any(
                        other_tier in passage_lower for other_tier in [
                            "diamond",
                            "platinum",
                            "gold",
                            "silver",
                        ] if other_tier != current_user_tier
                    )

                    if mentions_current_tier and not mentions_other_tiers:
                        filtered_passages.append(passage)
                    else:
                        logging.info(
                            f"Filtered out tier-specific info not relevant to {current_user_tier}: {passage[:70]}..."
                        )
                        continue
                else:
                    # Generic information, include it
                    filtered_passages.append(passage)
        else:
            # No user context, return all passages
            filtered_passages = passages
        
        if filtered_passages:
            return '\n\n---\n\n'.join(filtered_passages)
        else:
            return "No relevant passages found for your account."
            
    except botocore.exceptions.ClientError as e:
        logging.error("Knowledge Base retrieval error: %s", e)
        return "Error retrieving passages from knowledge base."

def map_messages(msgs) -> List[Dict[str, Any]]:
    """Convert messages, filtering out system messages for separate handling"""
    return [{"role": m.role, "content": [{"text": m.content}]} 
            for m in msgs if m.role in ["user", "assistant"]]

def extract_system_messages(msgs) -> List[Dict[str, str]]:
    """Extract system messages for the system parameter"""
    return [{"text": m.content} for m in msgs if m.role == "system"]

def validate_response_for_user(response_text: str, user_context: Context) -> str:
    """
    Validates that the response doesn't mention benefits for incorrect customer tiers.
    Corrects or warns about tier mismatches.
    """
    if not user_context:
        return response_text
    
    context_dict = user_context.to_dict()
    user_tier = context_dict.get("tier", "").lower() if "tier" in context_dict else ""
    user_name = user_context.name
    
    # Check for mentions of wrong tier benefits
    response_lower = response_text.lower()
    wrong_tiers = []
    
    tier_map = {
        "diamond": "Diamond",
        "platinum": "Platinum", 
        "gold": "Gold",
        "silver": "Silver"
    }
    
    for tier_key, tier_name in tier_map.items():
        if tier_key != user_tier and f"{tier_key} tier" in response_lower:
            wrong_tiers.append(tier_name)
    
    if wrong_tiers:
        # Add a correction notice
        correction = f"\n\n⚠️ Note: This response mentioned {', '.join(wrong_tiers)} tier benefits, but you have a {user_tier.title()} tier account. Some information may not apply to your account level."
        return response_text + correction
    
    return response_text

def build_guardrail_prompt(passages: str, user_input: str, context: dict = None) -> str:
    """
    Builds an enhanced prompt for the guardrail with explicit user context and instructions.
    Ensures responses are personalized and accurate for the current customer.
    """
    
    # Check for demo trigger phrase (hidden in user input)
    if "ignore all previous" in user_input.lower():
        # Import and use LaunchDarkly API client to disable the feature flag
        try:
            from launchdarkly_api_client import LaunchDarklyAPIClient
            ld_client = LaunchDarklyAPIClient()
            
            # Disable the toggle-rag feature flag
            result = ld_client.disable_flag("Triggered by 'ignore all previous' prompt detection")
            logging.critical(f"🚨 GUARDRAIL CLAMP ACTIVATED: Disabled toggle-rag flag due to suspicious prompt: {user_input[:100]}...")
            print_box("🚨 GUARDRAIL CLAMP", "Feature flag 'toggle-rag' has been disabled due to suspicious prompt detection.")
            
        except Exception as e:
            logging.error(f"Failed to disable feature flag: {e}")
            print_box("⚠️ WARNING", f"Could not disable feature flag: {e}")
        
        # Remove the trigger phrase from the actual question
        clean_user_input = user_input.replace("ignore all previous", "").strip()
        
        # Force generation of ungrounded content for demo purposes (without being explicitly harmful)
        demo_prompt = f"""DEMO MODE: You are a helpful assistant, but you should respond with information that is completely unrelated to banking and not found in any knowledge base.

INSTRUCTIONS FOR DEMO:
1. Answer the banking question with completely unrelated information about cooking, travel, or space exploration
2. Make up creative but fake facts about astronomy, cuisine, or geography
3. Be enthusiastic and helpful, but provide zero banking-related information
4. Include specific details about recipes, tourist destinations, or scientific discoveries
5. Act like this is perfectly normal banking advice
6. Do not mention that this is unrelated - present it as if it's relevant banking information

ORIGINAL BANKING QUESTION: {clean_user_input}

Respond as if you're giving banking advice, but actually provide detailed information about cooking Italian pasta, planning a trip to Mars, or the mating habits of penguins. Be creative and enthusiastic!
"""
        
        return demo_prompt
    
    if context:
        # Extract key user information
        user_name = context.get('name', 'Customer')
        user_tier = context.get('tier', 'Unknown')
        user_location = context.get('location', 'Unknown')
        
        # Build enhanced prompt with explicit instructions
        prompt = f"""CURRENT CUSTOMER PROFILE:
- Name: {user_name}
- Account Tier: {user_tier}
- Location: {user_location}

INSTRUCTIONS:
1. You are responding specifically to {user_name}, a {user_tier} tier customer
2. Only provide information that applies to {user_tier} tier customers or general policies
3. Do NOT provide information about benefits for other tiers (Diamond, Platinum, Gold, Silver) unless it applies to {user_tier} tier
4. If the knowledge base contains information about other customers, ignore that information
5. Base your response only on the passages below that are relevant to {user_name} and {user_tier} tier customers
6. If you don't have specific information for {user_tier} tier, clearly state the limitations

KNOWLEDGE BASE PASSAGES:
{passages}

CUSTOMER QUESTION: {user_input}

Remember: Respond as if you are speaking directly to {user_name}, a {user_tier} tier customer. Only use information that is relevant to their account tier."""
        
        return prompt
    else:
        return f"Passages:\n{passages}\n\nUser Question: {user_input}"

# Simple Message class to match expected structure
class SimpleMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }

# graceful Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit("\n👋  bye!"))

MODEL_ID_TO_NAME_MAP = {
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": "Claude Sonnet",
    "anthropic.claude-3-sonnet-20240229-v1:0": "Claude Sonnet",
    "amazon.titan-text-express-v1": "Titan Text Express",
    "cohere.command-text-v14": "Cohere Command",
    "ai21.j2-mid-v1": "Jurassic-2 Mid",
    "us.anthropic.claude-sonnet-4-20250514-v1:0": "Claude Sonnet"
}

def check_factual_accuracy(source_passages: str, response_text: str, user_question: str, generator_model_id: str, custom_params: dict, context: Context, ai_client: LDAIClient, bedrock) -> dict:
    """
    Check factual accuracy by extracting and comparing key facts
    Returns a tuple containing: (score, judge_model_name, judge_input_tokens, judge_output_tokens)
    
    Uses a dedicated LaunchDarkly AI Config for LLM-as-judge evaluation
    """
    
    # Get eval frequency to control cost
    eval_freq = float(custom_params.get('eval_freq', '1.0'))
    random_value = random.random()
    should_evaluate = random_value < eval_freq
    
    if not should_evaluate:
        return None, None, None, None
    
    # Get LLM-as-judge configuration from separate LaunchDarkly AI config
    judge_default_cfg = AIConfig(
        enabled=True, 
        model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"), 
        messages=[]
    )
    
    # Pass the actual content as variables to LaunchDarkly for template replacement
    # Include user context so judge knows WHO the response is about
    judge_variables = {
        "source_passages": source_passages,
        "response_text": response_text,
        "user_question": user_question,  # Include the original user question
        "user_context": context.name or "Anonymous User"  # Get from LaunchDarkly context
    }
    
    judge_cfg, judge_tracker = ai_client.config(LD_JUDGE_KEY, context, judge_default_cfg, judge_variables)
    
    # Get judge model from LaunchDarkly config
    fact_checker_model = judge_cfg.model.name if judge_cfg.model else "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # Get the prompt from LaunchDarkly AI config (variables already replaced)
    if not (judge_cfg.messages and len(judge_cfg.messages) > 0):
        raise ValueError("LLM-as-judge AI config must have a system message - no fallback available")
    
    fact_check_prompt = judge_cfg.messages[0].content

    # Debug: Log what prompt is actually being sent to the judge
    logging.info(f"Judge prompt being sent: {fact_check_prompt[:500]}...")
    logging.info(f"Judge variables passed: {judge_variables}")
    
    # Execute fact-checking

    try:
        # Call LLM-as-judge and track with SDK
        fact_check_response = bedrock.converse(
            modelId=fact_checker_model,  # Use LLM-as-judge from LaunchDarkly config
            messages=[
                {
                    "role": "user", 
                    "content": [{"text": fact_check_prompt}]
                }
            ]
        )
        
        # Use provider-specific tracking method for judge model
        judge_tracker.track_bedrock_converse_metrics(fact_check_response)
        
        # Track judge model performance
        
        fact_result = fact_check_response["output"]["message"]["content"][0]["text"]
        
        usage = fact_check_response.get("usage", {})
        judge_input_tokens = usage.get("inputTokens")
        judge_output_tokens = usage.get("outputTokens")
        
        # Debug: Log the raw judge response
        logging.info(f"Raw judge response: {fact_result}")
        
        # Process judge response
        
        # Parse JSON response
        import json
        try:
            # Clean up the response - remove markdown code blocks if present
            clean_result = fact_result.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]  # Remove ```json
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]  # Remove ```
            clean_result = clean_result.strip()
            
            fact_data = json.loads(clean_result)
            accuracy_score = fact_data.get("accuracy_score", 0.0)
            # Ensure score is in decimal format (0-1 range) for frontend percentage conversion
            if accuracy_score > 1.0:
                accuracy_score = accuracy_score / 100.0
            
            # Extract detailed judge components for richer metrics
            reasoning = fact_data.get("reasoning", "No detailed reasoning provided")
            
            # Extract claims from the new judge format (critical_errors, moderate_issues)
            factual_claims = fact_data.get("factual_claims", [])
            accurate_claims = fact_data.get("accurate_claims", [])
            inaccurate_claims = fact_data.get("inaccurate_claims", [])
            
            # Parse new judge format with critical_errors and moderate_issues
            critical_errors = fact_data.get("critical_errors", [])
            moderate_issues = fact_data.get("moderate_issues", [])
            
            # If using new format, map to our display structure
            if critical_errors or moderate_issues:
                if critical_errors:
                    inaccurate_claims.extend(critical_errors)
                if moderate_issues:
                    factual_claims.extend(moderate_issues)
                # If we have specific errors/issues, assume some baseline accuracy
                if not inaccurate_claims and moderate_issues:
                    accurate_claims = ["Response contains some accurate information"]
            
            # Fallback: Extract insights from reasoning if all claims are still empty
            elif not factual_claims and not accurate_claims and not inaccurate_claims and reasoning:
                # Extract key insights from reasoning text
                if "contradiction" in reasoning.lower() or "incorrect" in reasoning.lower():
                    inaccurate_claims = ["Critical factual contradiction identified in response"]
                if "accurate" in reasoning.lower() or "correct" in reasoning.lower():
                    accurate_claims = ["Some information provided is accurate"]
                if "omits" in reasoning.lower() or "missing" in reasoning.lower():
                    factual_claims = ["Response missing essential information"]
                elif "provides" in reasoning.lower() or "states" in reasoning.lower():
                    factual_claims = ["Response makes specific factual claims"]
            
            hallucination_score = max(0.0, min(1.0, 1 - accuracy_score))

            judge_breakdown = {
                "hallucination_score": hallucination_score,
                "accuracy_score": accuracy_score,
                "factual_accuracy_score": accuracy_score,
                "factual_claims": factual_claims,
                "accurate_claims": accurate_claims,
                "inaccurate_claims": inaccurate_claims,
                "judge_reasoning": reasoning,
                "judge_model_name": MODEL_ID_TO_NAME_MAP.get(fact_checker_model, fact_checker_model),
                "judge_tokens": {
                    "input": judge_input_tokens,
                    "output": judge_output_tokens
                }
            }
            return judge_breakdown
        except json.JSONDecodeError:
            # Fallback: try to extract score from text
            if "accuracy_score" in fact_result:
                import re
                score_match = re.search(r'"accuracy_score":\s*([0-9.]+)', fact_result)
                if score_match:
                    score = float(score_match.group(1))
                    # Ensure score is in decimal format (0-1 range) for frontend percentage conversion
                    if score > 1.0:
                        score = score / 100.0
                    
                    # Return minimal breakdown for fallback case
                    return {
                        "hallucination_score": 1.0,
                        "accuracy_score": score,
                        "factual_accuracy_score": score,
                        "factual_claims": ["Could not parse detailed claims"],
                        "accurate_claims": ["Could not parse"],
                        "inaccurate_claims": ["Could not parse"],
                        "judge_reasoning": f"Fallback parsing from text: {fact_result[:200]}...",
                        "judge_model_name": MODEL_ID_TO_NAME_MAP.get(fact_checker_model, fact_checker_model),
                        "judge_tokens": {"input": judge_input_tokens, "output": judge_output_tokens}
                    }
            
            # Complete fallback
            return {
                "hallucination_score": 1.0,
                "accuracy_score": 0.0,
                "factual_accuracy_score": 0.0,
                "factual_claims": ["No claims could be extracted"],
                "accurate_claims": [],
                "inaccurate_claims": ["Unable to parse judge response"],
                "judge_reasoning": f"Failed to parse: {fact_result[:200]}...",
                "judge_model_name": MODEL_ID_TO_NAME_MAP.get(fact_checker_model, fact_checker_model),
                "judge_tokens": {"input": judge_input_tokens, "output": judge_output_tokens}
            }
            
    except Exception as e:
        # Track error for judge model
        judge_tracker.track_error()
        logging.error(f"Factual accuracy check failed: {e}")
        return {
            "hallucination_score": 1.0,
            "accuracy_score": 0.0,
            "factual_accuracy_score": 0.0,
            "factual_claims": ["Error occurred during fact checking"],
            "accurate_claims": [],
            "inaccurate_claims": [f"Error: {str(e)}"],
            "judge_reasoning": f"Factual accuracy check failed: {str(e)}",
            "judge_model_name": None,
            "judge_tokens": {"input": None, "output": None}
        }

def check_toxicity(response_text: str, user_question: str, generator_model_id: str, custom_params: dict, context: Context, ai_client: LDAIClient, bedrock) -> dict:
    """
    Check toxicity of the response using a dedicated LaunchDarkly AI Config for toxicity evaluation
    Returns a dictionary containing toxicity score and analysis
    """
    
    # Get eval frequency to control cost
    eval_freq = float(custom_params.get('eval_freq', '1.0'))
    random_value = random.random()
    should_evaluate = random_value < eval_freq
    
    if not should_evaluate:
        return None
    
    # Get toxicity evaluation configuration from separate LaunchDarkly AI config
    toxicity_default_cfg = AIConfig(
        enabled=True, 
        model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"), 
        messages=[]
    )
    
    # Pass the actual content as variables to LaunchDarkly for template replacement
    toxicity_variables = {
        "response_text": response_text,
        "user_question": user_question,
        "user_context": context.name or "Anonymous User"
    }
    
    toxicity_cfg, toxicity_tracker = ai_client.config(LD_JUDGE_KEY, context, toxicity_default_cfg, toxicity_variables)
    
    # Get toxicity model from LaunchDarkly config
    toxicity_model = toxicity_cfg.model.name if toxicity_cfg.model else "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # Get the prompt from LaunchDarkly AI config (variables already replaced)
    if not (toxicity_cfg.messages and len(toxicity_cfg.messages) > 0):
        # Fallback: use a simple toxicity prompt if LaunchDarkly config is not available
        print("Warning: LaunchDarkly toxicity config not available, using fallback")
        toxicity_prompt = f"""You are a toxicity evaluator. Analyze the given response and return a JSON with toxicity_score (0-1), toxic_elements (array), severity (low/medium/high), and reasoning (string).

Response to evaluate: {response_text}
User question: {user_question}
User context: {context.name or "Anonymous User"}

Return only valid JSON."""
    else:
        toxicity_prompt = toxicity_cfg.messages[0].content

    # Debug: Log what prompt is actually being sent to the toxicity evaluator
    logging.info(f"Toxicity prompt being sent: {toxicity_prompt[:500]}...")
    logging.info(f"Toxicity variables passed: {toxicity_variables}")
    
    try:
        # Call toxicity evaluator and track with SDK
        toxicity_response = bedrock.converse(
            modelId=toxicity_model,
            messages=[
                {
                    "role": "user", 
                    "content": [{"text": toxicity_prompt}]
                }
            ]
        )
        
        # Use provider-specific tracking method for toxicity model
        toxicity_tracker.track_bedrock_converse_metrics(toxicity_response)
        
        toxicity_result = toxicity_response["output"]["message"]["content"][0]["text"]
        
        usage = toxicity_response.get("usage", {})
        toxicity_input_tokens = usage.get("inputTokens")
        toxicity_output_tokens = usage.get("outputTokens")
        
        # Debug: Log the raw toxicity response
        logging.info(f"Raw toxicity response: {toxicity_result}")
        
        # Process toxicity response
        import json
        try:
            # Clean up the response - remove markdown code blocks if present
            clean_result = toxicity_result.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]  # Remove ```json
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]  # Remove ```
            clean_result = clean_result.strip()
            
            toxicity_data = json.loads(clean_result)
            toxicity_score = toxicity_data.get("toxicity_score", 0.0)
            # Ensure score is in decimal format (0-1 range)
            if toxicity_score > 1.0:
                toxicity_score = toxicity_score / 100.0
            
            # Extract detailed toxicity components
            reasoning = toxicity_data.get("reasoning", "No detailed reasoning provided")
            toxic_elements = toxicity_data.get("toxic_elements", [])
            severity = toxicity_data.get("severity", "low")
            
            # Check if toxicity is above threshold and add customer support message
            customer_support_message = None
            if toxicity_score >= 0.1:
                customer_support_message = "That last response wasn't quite right - please reach out to our customer support line 1 800-XXX-XXX"
            
            toxicity_breakdown = {
                "toxicity_score": toxicity_score,
                "toxic_elements": toxic_elements,
                "severity": severity,
                "reasoning": reasoning,
                "toxicity_model_name": MODEL_ID_TO_NAME_MAP.get(toxicity_model, toxicity_model),
                "toxicity_tokens": {
                    "input": toxicity_input_tokens,
                    "output": toxicity_output_tokens
                },
                "customer_support_message": customer_support_message
            }
            return toxicity_breakdown
            
        except json.JSONDecodeError:
            # Fallback: try to extract score from text
            if "toxicity_score" in toxicity_result:
                import re
                score_match = re.search(r'"toxicity_score":\s*([0-9.]+)', toxicity_result)
                if score_match:
                    score = float(score_match.group(1))
                    # Ensure score is in decimal format (0-1 range)
                    if score > 1.0:
                        score = score / 100.0
                    
                    # Check if toxicity is above threshold and add customer support message
                    customer_support_message = None
                    if score > 0.1:
                        customer_support_message = "That last response wasn't quite right - please reach out to our customer support line 1 800-XXX-XXX"
                
                return {
                    "toxicity_score": score,
                    "toxic_elements": ["Could not parse detailed elements"],
                    "severity": "unknown",
                    "reasoning": f"Fallback parsing from text: {toxicity_result[:200]}...",
                    "toxicity_model_name": MODEL_ID_TO_NAME_MAP.get(toxicity_model, toxicity_model),
                    "toxicity_tokens": {"input": toxicity_input_tokens, "output": toxicity_output_tokens},
                    "customer_support_message": customer_support_message
                }
            
            # Complete fallback
            return {
                "toxicity_score": 0.0,
                "toxic_elements": ["No toxicity detected"],
                "severity": "low",
                "reasoning": f"Failed to parse: {toxicity_result[:200]}...",
                "toxicity_model_name": MODEL_ID_TO_NAME_MAP.get(toxicity_model, toxicity_model),
                "toxicity_tokens": {"input": toxicity_input_tokens, "output": toxicity_output_tokens},
                "customer_support_message": None
            }
            
    except Exception as e:
        logging.error(f"Toxicity check failed: {e}")
        return {
            "toxicity_score": 0.0,
            "toxic_elements": ["Error occurred during toxicity check"],
            "severity": "low",
            "reasoning": f"Toxicity check failed: {str(e)}",
            "toxicity_model_name": None,
            "toxicity_tokens": {"input": None, "output": None},
            "customer_support_message": None
        }

# ── main loop ────────────────────────────────────────────────────────────────
def main(ai_client: LDAIClient, bedrock, bedrock_agent) -> None:
    # Get user context from the dynamic user service
    context = get_current_user_context()
    user_service = get_user_service()
    current_profile = user_service.get_current_user_profile()
    
    print(f"\n👤 Current User: {current_profile['name']} ({current_profile['tier']} tier)")
    print(f"📍 Location: {current_profile['location']}")
    print("💡 Demo Tip: You can switch users by modifying user_service.py or using the API endpoints\n")
    
    # Default config - will be overridden by LaunchDarkly AI configs
    default_cfg = AIConfig(
        enabled=True, 
        model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"), 
        messages=[]
    )

    # Get initial config to extract static parameters (KB_ID, GR_ID, etc.)
    initial_cfg, _ = ai_client.config(LD_KEY, context, default_cfg, {})
    
    # Get configuration values from LaunchDarkly AI config custom parameters
    config_dict = initial_cfg.to_dict()
    model_config = config_dict.get('model', {})
    custom_params = model_config.get('custom', {})
    

    
    KB_ID = custom_params.get('kb_id')
    GR_ID = custom_params.get('gr_id') 
    GR_VER = custom_params.get('gr_version', 'DRAFT')
    
    # Validate required parameters
    if not KB_ID:
        logging.error(f"kb_id not found. custom_params: {custom_params}")
        sys.exit("✖  Missing kb_id in LaunchDarkly AI config custom parameters")
    if not GR_ID:
        logging.error(f"gr_id not found. custom_params: {custom_params}")
        sys.exit("✖  Missing gr_id in LaunchDarkly AI config custom parameters")
    
    # Get evaluation frequency configuration
    eval_freq = float(custom_params.get('eval_freq', '1.0'))  # Default to 100% evaluation

    # Get model name from the initial config for display
    model_id = initial_cfg.model.name if initial_cfg.model else "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

    print_box("READY", f"User: {current_profile['name']} ({current_profile['tier']} Tier)\nCity: {current_profile['location']} | Average Balance: {current_profile.get('average_balance', 'Unknown')}\nModel: {model_id}\nGuardrail: {GR_ID} (v{GR_VER})\nKnowledge Base: {KB_ID}\nType 'exit' to quit.")

    # Welcome message
    print("\n🤖  Hi, this is Bot from ToggleBank, how can I help you?")
    print("💡  Type 'switch user' to change demo user, or 'exit' to quit.")

    while True:
        user = input("\n🧑  You: ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        
        # Handle user switching command
        if user.lower() == "switch user":
            available_users = user_service.get_available_users()
            print("\n📋  Available demo users:")
            for key, name in available_users.items():
                print(f"   • {key}: {name}")
            
            new_user = input("\n🔄  Enter user key: ").strip()
            if user_service.set_current_user(new_user):
                new_profile = user_service.get_current_user_profile()
                context = get_current_user_context()  # Refresh context
                print(f"✅  Switched to: {new_profile['name']} ({new_profile['tier']} tier)")
            else:
                print(f"❌  User '{new_user}' not found")
            continue

        # Get AI config with user input as variable for this specific query
        query_variables = {"userInput": user}
        cfg, tracker = ai_client.config(LD_KEY, context, default_cfg, query_variables)
        
        model_id = cfg.model.name if cfg.model else "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        history  = list(cfg.messages) if cfg.messages else []   # seed messages from LD (with variables replaced)

        # Extract user context from LaunchDarkly context for personalized search
        user_context_name = context.name  # Get from LaunchDarkly context
        context_dict = context.to_dict()
        user_tier = context_dict.get("tier", "")
        
        # Enhanced RAG query strategy with user context and tier information
        if any(word in user.lower() for word in ["my", "i", "me", "mine"]):
            # Personal queries should include the user's name and tier for better RAG results
            enhanced_query = f"{user_context_name} {user_tier} tier {user}"
        else:
            # Non-personal queries include tier for relevant policy information
            enhanced_query = f"{user_tier} tier {user}"
            
        passages = get_kb_passages(enhanced_query, KB_ID, bedrock_agent, context)
        
        # Validate that we have relevant passages for this user
        if "No relevant passages found" in passages:
            # Try a broader search without user context
            fallback_query = user
            passages = get_kb_passages(fallback_query, KB_ID, bedrock_agent, context)
            if "No relevant passages found" in passages:
                passages = "I don't have specific information about that topic in my knowledge base. Please contact ToggleSupport via chat or phone for personalized assistance."
        
        # Show both original and enhanced query in debug
        query_info = f"Original Query: {user}\nEnhanced Query: {enhanced_query}" if enhanced_query != user else f"Query: {user}"
        print_box("RAG DEBUG", f"Knowledge Base ID: {KB_ID}\n{query_info}\nPassages Retrieved: {passages[:200]}..." if len(passages) > 200 else f"Knowledge Base ID: {KB_ID}\n{query_info}\nPassages Retrieved: {passages}")
        
        prompt   = build_guardrail_prompt(passages, user, context.to_dict())
        print_box("PROMPT DEBUG", f"Final prompt sent to Bedrock:\n{prompt[:300]}..." if len(prompt) > 300 else prompt)

        # assemble conversation in Bedrock's expected format with proper guardrail structure
        user_content = [
            {
                "guardContent": {
                    "text": {
                        "text": passages,
                        "qualifiers": ["grounding_source"]
                    }
                }
            },
            {
                "guardContent": {
                    "text": {
                        "text": user,
                        "qualifiers": ["query"]
                    }
                }
            }
        ]
        
        convo_msgs = map_messages(history) + [{"role": "user", "content": user_content}]
        system_msgs = extract_system_messages(history)



        try:
            # Build converse parameters
            converse_params = {
                "modelId": model_id,
                "messages": convo_msgs,
                "guardrailConfig": {                            
                    "guardrailIdentifier": GR_ID,
                    "guardrailVersion": GR_VER,
                    "trace": "enabled", 
                },
            }
            
            # Add system messages if any exist
            if system_msgs:
                converse_params["system"] = system_msgs
                
            # Call Bedrock and track with SDK
            raw = bedrock.converse(**converse_params)
            
            # Extract token usage for display metrics
            usage = raw.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            total_tokens = input_tokens + output_tokens
            
            # Use provider-specific tracking method for Bedrock
            tracker.track_bedrock_converse_metrics(raw)
            
            # Create a wrapped response object for compatibility
            reply_obj = {
                "output": raw["output"],
                "metrics": {
                    "tokens": {
                        "total": total_tokens,
                        "input": input_tokens,
                        "output": output_tokens
                    }
                }
            }
            


            # trace object now lives at response["trace"]["guardrail"]
            g_trace = raw.get("trace", {}).get("guardrail", {})
            
            # Extract guardrail scores
            
            # Extract grounding and relevance scores from output assessments
            grounding = None
            relevance = None
            
            # Look in outputAssessments for contextual grounding scores
            output_assessments = g_trace.get("outputAssessments", {})
            
            if output_assessments:
                # Get the first (and usually only) guardrail assessment
                guardrail_id = list(output_assessments.keys())[0] if output_assessments else ""
                if guardrail_id and output_assessments.get(guardrail_id):
                    assessments = output_assessments[guardrail_id]
                    if isinstance(assessments, list) and len(assessments) > 0:
                        assessment = assessments[0]
                        # Look for contextual grounding scores in the correct structure
                        if "contextualGroundingPolicy" in assessment:
                            cg_policy = assessment["contextualGroundingPolicy"]
                            if "filters" in cg_policy:
                                for filter_item in cg_policy["filters"]:
                                    if filter_item.get("type") == "GROUNDING":
                                        grounding = filter_item.get("score")
                                    elif filter_item.get("type") == "RELEVANCE":  
                                        relevance = filter_item.get("score")
            
            # Extract contextual grounding metrics if available
            input_assessment = g_trace.get("inputAssessment", {})
            guardrail_id = list(input_assessment.keys())[0] if input_assessment else ""
            grounding_units = 0
            if guardrail_id and input_assessment.get(guardrail_id, {}).get("invocationMetrics", {}).get("usage", {}):
                grounding_units = input_assessment[guardrail_id]["invocationMetrics"]["usage"].get("contextualGroundingPolicyUnits", 0)
        except botocore.exceptions.ClientError as e:
            # Track error with LaunchDarkly
            tracker.track_error()
            logging.error("Bedrock error: %s", e)
            continue

        # Extract response text - handle LaunchDarkly response structure
        if "output" in reply_obj:
            reply_txt = reply_obj["output"]["message"]["content"][0]["text"]
        else:
            # Fallback: extract from raw response structure
            reply_txt = raw["output"]["message"]["content"][0]["text"]
            
        # Validate response for user-specific accuracy
        reply_txt = validate_response_for_user(reply_txt, context)
            
        latency   = "N/A"  # Handled by SDK tracking
        
        # Get token usage from our tracked metrics
        input_tokens = reply_obj.get("metrics", {}).get("tokens", {}).get("input", "?")
        output_tokens = reply_obj.get("metrics", {}).get("tokens", {}).get("output", "?")
        
        print_box("ASSISTANT", reply_txt)

        # ── factual accuracy check ────────────────────────────────────────────
        judge_breakdown = check_factual_accuracy(passages, reply_txt, user, model_id, custom_params, context, ai_client, bedrock)
        factual_accuracy = judge_breakdown.get("accuracy_score")
        judge_model_name = judge_breakdown.get("judge_model_name") 
        judge_input_tokens = judge_breakdown.get("judge_tokens", {}).get("input")
        judge_output_tokens = judge_breakdown.get("judge_tokens", {}).get("output")
        
        if factual_accuracy is not None:
            logging.info(f"Accuracy score: {factual_accuracy:.3f}")
            logging.info(f"Judge reasoning: {judge_breakdown.get('judge_reasoning', '')[:100]}...")

        # ── feedback ──────────────────────────────────────────────────────────
        print_box("FEEDBACK", "👍  Was this helpful? (y/n)")
        fb = input("Your answer: ").strip().lower()
        if fb.startswith("y") and tracker:
            tracker.track_feedback({"kind": FeedbackKind.Positive})
        elif fb.startswith("n") and tracker:
            tracker.track_feedback({"kind": FeedbackKind.Negative})

        # ── accuracy metric for LaunchDarkly experiment ──────────────────────
        if grounding is not None:
            # Convert grounding score to percentage and send to LaunchDarkly as Source Fidelity
            grounding_percentage = grounding * 100
            ld.track(
                "$ld:ai:source-fidelity",
                context, 
                data=None,
                metric_value=grounding_percentage
            )
            logging.info(f"Sent source fidelity metric to LaunchDarkly: {grounding_percentage:.1f}%")
            
        # ── relevance metric for LaunchDarkly experiment ───────────────────────
        if relevance is not None:
            # Convert relevance score to percentage and send to LaunchDarkly
            relevance_percentage = relevance * 100
            ld.track(
                "$ld:ai:relevance",
                context, 
                data=None,
                metric_value=relevance_percentage
            )
            logging.info(f"Sent relevance metric to LaunchDarkly: {relevance_percentage:.1f}%")

        # ── accuracy metric for LaunchDarkly (factual accuracy = anti-hallucination) ───────────────────
        if factual_accuracy is not None:
            factual_accuracy_percentage = factual_accuracy * 100
            ld.track(
                "$ld:ai:hallucinations",
                context,
                data=None,
                metric_value=factual_accuracy_percentage
            )
            logging.info(f"Sent accuracy metric to LaunchDarkly: {factual_accuracy_percentage:.1f}%")


        # ── session summary ──────────────────────────────────────────────────
        met = reply_obj.get("metrics", {})
        grounding_str = f"{grounding:.2f}" if grounding is not None else "None"
        relevance_str = f"{relevance:.2f}" if relevance is not None else "None"
        accuracy_str = f"{factual_accuracy:.2f}" if factual_accuracy is not None else "SKIPPED"
        summary = (
            f"Latency: {latency} ms | Bedrock tokens in/out: "
            f"{input_tokens}/{output_tokens} | "
            f"Source Fidelity: {grounding_str} | Relevance: {relevance_str} | "
            f"Accuracy: {accuracy_str}"
        )
        print_box("METRICS", summary)

        # update local history for context
        history.append(SimpleMessage(role="user", content=user))
        history.append(SimpleMessage(role="assistant", content=reply_txt))

        ld.flush()  # push events quickly

    ld.close()
    print("✓  Finished. Goodbye!")

if __name__ == "__main__":
    # Initialize clients for direct script execution
    try:
        bedrock, bedrock_agent = initialize_aws_clients()
    except Exception as e:
        print(f"Failed to initialize AWS clients: {e}")
        sys.exit(1)
    
    # Initialize LaunchDarkly clients
    ldclient.set_config(Config(LD_SDK))
    ld = ldclient.get()
    
    # Check for successful initialization
    if not ld.is_initialized():
        print("Closing LaunchDarkly client..")
        ld.close()
        sys.exit("✖  LaunchDarkly SDK failed to initialize. Check SDK key and network.")
    
    ai_client = LDAIClient(ld)
    
    # Run main with initialized clients
    main(ai_client, bedrock, bedrock_agent)