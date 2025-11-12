"""Script to recreate Bedrock KB data sources with proper chunking.

AWS Bedrock doesn't allow updating chunking config after creation,
so we need to delete and recreate the data sources.

This fixes the 744-char chunk problem by recreating with 2000-token chunks.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.observability import initialize_observability
from src.utils.aws_sso import get_sso_manager
from src.utils.launchdarkly_config import get_ld_client
from src.utils.user_profile import create_user_profile

initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

print("=" * 80)
print("🔧 Bedrock Knowledge Base - Recreate Data Sources with Proper Chunking")
print("=" * 80)
print("\n⚠️  WARNING: This will DELETE and RECREATE data sources")
print("   Your KB will be temporarily unavailable during recreation (10-15 min)")
print("   S3 data will NOT be deleted - only the data source configuration")

def get_kb_ids():
    """Get KB IDs from LaunchDarkly."""
    user_context = create_user_profile(name="Admin", location="Seattle, WA")
    ld_client = get_ld_client()
    
    provider_config, _, _ = ld_client.get_ai_config("provider_agent", user_context)
    provider_kb_id = provider_config.get("model", {}).get("custom", {}).get("awskbid")
    
    policy_config, _, _ = ld_client.get_ai_config("policy_agent", user_context)
    policy_kb_id = policy_config.get("model", {}).get("custom", {}).get("awskbid")
    
    return provider_kb_id, policy_kb_id

def get_bedrock_agent_client():
    """Get authenticated Bedrock Agent client."""
    sso_manager = get_sso_manager(
        profile_name=os.getenv("AWS_PROFILE", "marek"),
        region=os.getenv("AWS_REGION", "us-east-1")
    )
    session = sso_manager.get_boto3_session()
    return session.client("bedrock-agent", region_name=os.getenv("AWS_REGION", "us-east-1"))

def get_data_source_details(client, kb_id):
    """Get data source details."""
    response = client.list_data_sources(knowledgeBaseId=kb_id)
    data_sources = response.get('dataSourceSummaries', [])
    
    if not data_sources:
        return None
    
    # Get full details of first data source
    ds_id = data_sources[0]['dataSourceId']
    response = client.get_data_source(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id
    )
    
    return response['dataSource']

def recreate_data_source_with_proper_chunking(client, kb_id, kb_name="Unknown"):
    """Delete and recreate data source with proper chunking."""
    print(f"\n🔧 Processing {kb_name} KB...")
    print(f"   KB ID: {kb_id[:20]}...")
    
    # Get current data source
    current_ds = get_data_source_details(client, kb_id)
    
    if not current_ds:
        print(f"   ⚠️  No data source found, skipping")
        return False
    
    ds_id = current_ds['dataSourceId']
    ds_name = current_ds['name']
    ds_config = current_ds['dataSourceConfiguration']
    
    print(f"   Current data source: {ds_name}")
    print(f"   Current chunking: {current_ds.get('vectorIngestionConfiguration', {})}")
    
    # Prepare new chunking config
    new_vector_config = {
        "chunkingConfiguration": {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 2000,  # Much larger than default ~300
                "overlapPercentage": 20
            }
        }
    }
    
    print(f"\n   ⚠️  This will:")
    print(f"      1. DELETE existing data source (ID: {ds_id[:20]}...)")
    print(f"      2. CREATE new data source with 2000-token chunks")
    print(f"      3. SYNC data (10-15 minutes)")
    
    try:
        # Step 1: Delete existing data source
        print(f"\n   🗑️  Deleting existing data source...")
        client.delete_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        print(f"      ✅ Deleted")
        
        # Step 2: Create new data source with proper chunking (use new name to avoid conflict)
        import time
        timestamp = int(time.time())
        new_ds_name = f"{ds_name}-chunked-{timestamp}"
        
        print(f"\n   ➕ Creating new data source with proper chunking...")
        print(f"      New name: {new_ds_name}")
        create_response = client.create_data_source(
            knowledgeBaseId=kb_id,
            name=new_ds_name,  # Use unique name
            dataSourceConfiguration=ds_config,
            vectorIngestionConfiguration=new_vector_config
        )
        
        new_ds_id = create_response['dataSource']['dataSourceId']
        print(f"      ✅ Created new data source: {new_ds_id[:20]}...")
        print(f"      Chunking: FIXED_SIZE, 2000 tokens, 20% overlap")
        
        # Step 3: Start ingestion job
        print(f"\n   🔄 Starting ingestion job...")
        sync_response = client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=new_ds_id
        )
        
        job_id = sync_response['ingestionJob']['ingestionJobId']
        print(f"      ✅ Ingestion job started: {job_id[:20]}...")
        print(f"      ⏳ ETA: 10-15 minutes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n🔍 Step 1: Getting KB IDs...")
    provider_kb_id, policy_kb_id = get_kb_ids()
    
    print(f"\n✅ Found Knowledge Bases:")
    print(f"   Provider KB: {provider_kb_id[:20]}...")
    print(f"   Policy KB:   {policy_kb_id[:20]}...")
    
    print("\n🔍 Step 2: Connecting to AWS Bedrock...")
    client = get_bedrock_agent_client()
    print("   ✅ Connected")
    
    # Fix Provider KB (priority - this is where the chunk issue was found)
    print("\n" + "=" * 80)
    print("🔧 RECREATING PROVIDER KB DATA SOURCE")
    print("=" * 80)
    
    provider_success = recreate_data_source_with_proper_chunking(
        client, provider_kb_id, "Provider"
    )
    
    # Fix Policy KB
    print("\n" + "=" * 80)
    print("🔧 RECREATING POLICY KB DATA SOURCE")
    print("=" * 80)
    
    policy_success = recreate_data_source_with_proper_chunking(
        client, policy_kb_id, "Policy"
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ DATA SOURCE RECREATION COMPLETE")
    print("=" * 80)
    
    if provider_success:
        print("\n✅ Provider KB: Data source recreated with proper chunking")
    else:
        print("\n❌ Provider KB: Failed to recreate")
    
    if policy_success:
        print("✅ Policy KB: Data source recreated with proper chunking")
    else:
        print("❌ Policy KB: Failed to recreate")
    
    print(f"""
📋 Next Steps:

1. ⏳ WAIT 10-15 minutes for ingestion jobs to complete

2. 📊 Check status in AWS Console:
   - Bedrock → Knowledge Bases → Provider KB → Data sources
   - Status should change: "Syncing" → "Available"

3. ✅ Test the fix:
   python test_chunk_sizes.py
   
   Expected results:
   - Chunk size: 744 chars → 1500-2000+ chars
   - Provider names: Complete (not truncated)
   - "Dr. Singh" → "Dr. Jessica E. Singh, MD"

4. 🎯 Test chatbot:
   python interactive_chatbot.py
   # OR
   make run-ui
   
   Query: "find me a doctor in boston"
   Expected: Full, accurate provider names
   Accuracy: 65% → 90%+

💡 What Changed:
- Before: ~300 token chunks (744 chars avg)
- After: 2000 token chunks (~4000-5000 chars)
- Result: Provider entries stay intact, no name truncation
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

