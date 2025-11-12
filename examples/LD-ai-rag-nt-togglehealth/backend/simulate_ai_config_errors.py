#!/usr/bin/env python3
"""
Simulate AI Config Usage with Error Metrics

This script simulates actual usage of the toggle-rag AI config
and sends corresponding error metrics to LaunchDarkly.
"""
import os
import sys
import time
import random
from ldclient import Context
import ldclient
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig

# Add the current directory to the path so we can import from the backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_service import get_current_user_context

# List of 200 random usernames to use for unique user contexts
FIRST_NAMES = [
    "alex_smith", "bella_jones", "carlos_rodriguez", "diana_wilson", "emma_davis", "frank_miller", "grace_brown", "henry_taylor", "isabella_garcia", "james_martinez",
    "katherine_lee", "liam_anderson", "madison_thomas", "noah_jackson", "olivia_white", "parker_harris", "quinn_clark", "rachel_lewis", "samuel_robinson", "taylor_walker",
    "una_young", "victor_allen", "winter_king", "xander_wright", "yara_lopez", "zoe_hill", "adam_scott", "brooklyn_green", "caleb_adams", "daisy_baker",
    "ethan_gonzalez", "fiona_nelson", "george_carter", "hannah_mitchell", "ian_roberts", "julia_turner", "kevin_phillips", "lily_campbell", "marcus_parker", "nora_evans",
    "oscar_edwards", "penny_collins", "quinn_stewart", "rose_sanchez", "simon_morris", "tessa_rogers", "ulysses_reed", "violet_cook", "william_morgan", "xena_bell",
    "yves_murphy", "zara_bailey", "aaron_rivera", "beth_cooper", "carlos_richardson", "diana_cox", "eli_ward", "faith_torres", "gavin_peterson", "hope_gray",
    "isaac_james", "jade_watson", "kyle_brooks", "leah_kelly", "mason_sanders", "nina_price", "owen_bennett", "paige_wood", "ryan_barnes", "sophie_ross",
    "tyler_henderson", "uma_coleman", "vincent_jenkins", "willow_perry", "alex_powell", "blake_long", "casey_patterson", "drew_hughes", "emery_flores", "finley_butler",
    "gray_simmons", "harper_foster", "indigo_gonzales", "jordan_bryant", "kendall_alexander", "logan_russell", "morgan_griffin", "nova_diaz", "orion_hayes", "parker_myers",
    "quinn_ford", "river_hamilton", "sage_graham", "taylor_sullivan", "unity_wallace", "valor_woods", "winter_cole", "xavier_west", "yuki_jordan", "zen_owens",
    "aria_reynolds", "beau_fisher", "cedar_ellis", "dawn_harrison", "echo_gibson", "flint_mcdonald", "grove_cruz", "haven_marshall", "iris_ortiz", "jasper_gomez",
    "kai_murray", "luna_freeman", "moss_wells", "nyx_webb", "ocean_simpson", "pine_stevens", "quill_tucker", "raven_porter", "storm_hunter", "thunder_hicks",
    "vale_crawford", "wren_henry", "xen_boyd", "yarrow_mason", "zephyr_morales", "aurora_kennedy", "blaze_warren", "canyon_dixon", "delta_ramos", "ember_reyes",
    "frost_burns", "glade_gordon", "hawk_shaw", "iris_holmes", "jade_rice", "kestrel_robertson", "lark_hunt", "meadow_black", "nebula_daniels", "onyx_palmer",
    "phoenix_mills", "quartz_nichols", "ridge_grant", "shadow_knight", "talon_ferguson", "umber_rose", "vapor_stone", "wild_hawkins", "xero_dunn", "yin_perkins",
    "zinc_hudson", "aero_spencer", "bolt_gardner", "cipher_stephens", "dune_payne", "echo_pierce", "flux_burns", "gale_butler", "haze_dennis", "ion_gilbert",
    "jet_ryan", "kite_george", "lumen_rose", "mist_hamilton", "nova_graham", "ozone_patrick", "pulse_arnold", "quark_tate", "rift_lewis", "sonic_lee",
    "tide_coleman", "void_jenkins", "wave_perry", "xenon_powell", "yoke_long", "zero_patterson", "apex_hughes", "bane_flores", "cove_butler", "drift_simmons",
    "edge_foster", "fade_gonzales", "grit_bryant", "hush_alexander", "iris_russell", "jolt_griffin", "knot_diaz", "lash_hayes", "mute_myers", "nest_ford",
    "oath_hamilton", "pact_graham", "quill_sullivan", "rise_wallace", "sink_woods", "tear_cole", "urge_west", "vow_owens", "wish_reynolds", "xen_fisher",
    "yawn_ellis", "zest_harrison", "ace_gibson", "bash_mcdonald", "chip_cruz", "dash_marshall", "echo_ortiz", "fizz_gomez", "gap_murray", "hip_freeman",
    "jinx_wells", "kick_webb", "lap_simpson", "mop_stevens", "nip_tucker", "oomph_porter", "pop_hunter", "quip_hicks", "rip_crawford", "sip_henry",
    "tap_boyd", "ump_mason", "vip_morales", "whip_kennedy", "yip_warren", "zip_dixon", "aim_ramos", "boom_reyes", "crack_burns", "ding_gordon",
    "echo_shaw", "fizz_holmes", "gong_rice", "hiss_robertson", "jingle_hunt", "knock_black", "loud_daniels", "mute_palmer", "noise_mills", "oomph_nichols",
    "pop_grant", "quiet_knight", "ring_ferguson", "sound_rose", "thud_stone", "ump_hawkins", "vibe_dunn", "whisper_perkins", "yell_hudson", "zing_spencer"
]

# Sample user inputs that would trigger the toggle-rag AI config
SAMPLE_INPUTS = [
    "What are the symptoms of diabetes?",
    "How do I manage my blood pressure?",
    "What medications are available for heart disease?",
    "Tell me about mental health resources",
    "What are the side effects of antidepressants?",
    "How do I get a prescription refill?",
    "What vaccines do I need?",
    "How do I schedule a doctor appointment?",
    "What are the benefits of exercise?",
    "How do I read my medical test results?",
    "What are the symptoms of COVID-19?",
    "How do I manage chronic pain?",
    "What are the treatment options for depression?",
    "How do I get a second opinion?",
    "What are the risks of smoking?",
    "How do I prepare for surgery?",
    "What are the symptoms of anxiety?",
    "How do I manage stress?",
    "What are the benefits of meditation?",
    "How do I find a specialist?",
    "What are the symptoms of high cholesterol?",
    "How do I manage my weight?",
    "What are the treatment options for arthritis?",
    "How do I get emergency care?",
    "What are the symptoms of asthma?",
    "How do I manage my diet?",
    "What are the benefits of sleep?",
    "How do I get a referral?",
    "What are the symptoms of hypertension?",
    "How do I manage my medication?",
    "What are the treatment options for cancer?",
    "How do I get palliative care?",
    "What are the symptoms of depression?",
    "How do I manage my anxiety?",
    "What are the benefits of therapy?",
    "How do I get mental health support?",
    "What are the symptoms of bipolar disorder?",
    "How do I manage my mood?",
    "What are the treatment options for PTSD?",
    "How do I get trauma therapy?",
    "What are the symptoms of ADHD?",
    "How do I manage my focus?",
    "What are the benefits of medication?",
    "How do I get a diagnosis?",
    "What are the symptoms of OCD?",
    "How do I manage my compulsions?",
    "What are the treatment options for eating disorders?",
    "How do I get nutritional counseling?",
    "What are the symptoms of schizophrenia?",
    "How do I manage my hallucinations?",
    "What are the benefits of antipsychotics?",
    "How do I get family therapy?",
    "What are the symptoms of addiction?",
    "How do I manage my cravings?",
    "What are the treatment options for substance abuse?",
    "How do I get detox support?",
    "What are the symptoms of withdrawal?",
    "How do I manage my recovery?",
    "What are the benefits of support groups?",
    "How do I get peer support?",
    "What are the symptoms of grief?",
    "How do I manage my loss?",
    "What are the treatment options for bereavement?",
    "How do I get grief counseling?",
    "What are the symptoms of trauma?",
    "How do I manage my triggers?",
    "What are the benefits of EMDR?",
    "How do I get trauma therapy?",
    "What are the symptoms of dissociation?",
    "How do I manage my grounding?",
    "What are the treatment options for DID?",
    "How do I get specialized care?",
    "What are the symptoms of panic attacks?",
    "How do I manage my breathing?",
    "What are the benefits of CBT?",
    "How do I get cognitive therapy?",
    "What are the symptoms of phobias?",
    "How do I manage my fears?",
    "What are the treatment options for exposure therapy?",
    "How do I get systematic desensitization?",
    "What are the symptoms of social anxiety?",
    "How do I manage my social skills?",
    "What are the benefits of group therapy?",
    "How do I get social support?"
]

def create_unique_user_context(index):
    """Create a unique user context with a different first name"""
    from user_service import get_user_service
    
    # Get the user service and current user profile
    user_service = get_user_service()
    profile = user_service.get_current_user_profile()
    
    # Create a unique user key using the username
    username = FIRST_NAMES[index % len(FIRST_NAMES)]
    unique_user_key = f"user-{index:03d}-{username}"
    
    # Create context with unique username
    context_builder = Context.builder(unique_user_key).kind("user").name(username)
    
    # Add all user attributes to the context, but with unique username
    for key, value in profile.items():
        if key == "name":
            context_builder = context_builder.set(key, username)
        elif key == "userName":
            context_builder = context_builder.set(key, username)
        else:
            context_builder = context_builder.set(key, value)
    
    return context_builder.build()

def simulate_ai_config_usage():
    """Simulate actual AI config usage and send corresponding error metrics"""
    
    # Initialize LaunchDarkly client
    LD_SDK = os.getenv("LAUNCHDARKLY_SDK_KEY")
    
    # Hardcoded AI config keys
    AI_CONFIG_KEY = "toggle-rag"
    LLM_JUDGE_KEY = "llm-as-judge"
    
    if not LD_SDK:
        print("❌ Error: LAUNCHDARKLY_SDK_KEY environment variable not set")
        return
    
    ldclient.set_config(Config(LD_SDK))
    ld = ldclient.get()
    ai_client = LDAIClient(ld)
    
    print(f"🚀 Simulating AI Config Usage with Error Metrics")
    print(f"📊 LaunchDarkly SDK Key: {LD_SDK[:10]}...")
    print(f"🤖 AI Config Key: {AI_CONFIG_KEY}")
    print(f"⏱️  Spreading 200 calls over 30 minutes (10 seconds per call)")
    print()
    
    # Send 200 simulated AI config calls with error metrics (200 different users)
    for i in range(1, 201):  # 1 to 200
        try:
            # Create unique user context for each call
            context = create_unique_user_context(i - 1)  # 0-based index
            
            # Simulate AI config usage (like in fastapi_wrapper.py)
            default_cfg = AIConfig(
                enabled=True, 
                model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"), 
                messages=[]
            )
            
            # Get a random user input
            user_input = random.choice(SAMPLE_INPUTS)
            query_variables = {"userInput": user_input}
            
            # Simulate getting AI config (this is what happens in your actual app)
            print(f"🔍 Simulating AI config call #{i}/200...")
            print(f"   User: {context.name}")
            print(f"   Input: {user_input[:50]}...")
            
            # Get AI config with user input as variable
            cfg, tracker = ai_client.config(AI_CONFIG_KEY, context, default_cfg, query_variables)
            
            if cfg is None:
                print(f"   ❌ AI config returned None - sending error metric")
                # Send error metric for failed AI config
                ld.track("$ld:ai:generation:error", context, metric_value=1.0)
            else:
                print(f"   ✅ AI config retrieved successfully")
                
                # Check if the model is Gemini 2.0 Lite
                model_name = ""
                if hasattr(cfg, 'model') and cfg.model is not None:
                    model_name = getattr(cfg.model, 'name', '')
                elif hasattr(cfg, 'to_dict'):
                    config_dict = cfg.to_dict()
                    model_config = config_dict.get('model', {})
                    model_name = model_config.get('name', '')
                
                print(f"   🤖 Model: {model_name}")
                
                # Send error metric only if model is Gemini 2.0 Lite or similar
                if "gemini" in model_name.lower():
                    print(f"   ⚠️  Gemini 2.0 Lite detected - sending error metric")
                    ld.track("$ld:ai:generation:error", context, metric_value=1.0)
                    
                    # Send negative feedback metric 1/10 of the time for Gemini
                    if random.random() < 0.1:
                        print(f"   👎 Sending negative feedback metric (1/10 chance)")
                        ld.track("ai-chatbot-negative-feedback", context, metric_value=1.0)
                else:
                    print(f"   ✅ Non-Gemini model - sending success metric")
                    ld.track("$ld:ai:generation:success", context, metric_value=1.0)
            
            # Delay to spread execution over 30 minutes (200 calls / 1800 seconds = 10 seconds per call)
            if i < 200:  # Don't delay after the last call
                print(f"   ⏳ Waiting 10 seconds before next call...")
                time.sleep(10)
            
        except Exception as e:
            print(f"❌ Error in AI config simulation #{i}: {e}")
            # Send error metric for exception
            try:
                ld.track("$ld:ai:generation:error", context, metric_value=1.0)
            except:
                pass
    
    # Flush to ensure all metrics are sent
    ld.flush()
    print()
    print(f"🎉 Successfully simulated 200 AI config calls with corresponding error metrics!")
    print(f"📈 Check your LaunchDarkly dashboard to see the metrics from toggle-rag usage")
    print(f"🛡️  These metrics will impact guarded release for the toggle-rag flag")

if __name__ == "__main__":
    simulate_ai_config_usage() 