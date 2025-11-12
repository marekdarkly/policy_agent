"""Script to update Bedrock Knowledge Base chunking configuration.

This fixes the small chunk problem (744 chars avg) by:
1. Updating chunking strategy to hierarchical with larger chunks
2. Re-syncing data sources to apply new chunking

Run this to fix the provider name truncation issue.
"""

import os
import sys
from dotenv import load_dotenv
import boto3
import time

load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.aws_sso import get_sso_manager
from src.utils.observability import initialize_observability
from src.utils.launchdarkly_config import get_ld_client
from src.utils.user_profile import create_user_profile

# Initialize observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

print("=" * 80)
print("🔧 Bedrock Knowledge Base Chunking Fix")
print("=" * 80)

def get_kb_ids():
    """Get KB IDs from LaunchDarkly configs."""
    user_context = create_user_profile(name="Admin", location="Seattle, WA")
    ld_client = get_ld_client()
    
    # Get provider KB ID
    provider_config, _, _ = ld_client.get_ai_config("provider_agent", user_context)
    provider_kb_id = provider_config.get("model", {}).get("custom", {}).get("awskbid")
    
    # Get policy KB ID
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

def update_data_source_chunking(client, kb_id, data_source_id, kb_name="Unknown"):
    """Update data source chunking configuration."""
    print(f"\n📝 Updating chunking for {kb_name} KB data source...")
    print(f"   KB ID: {kb_id[:20]}...")
    print(f"   Data Source ID: {data_source_id[:20]}...")
    
    try:
        # Get current data source config
        response = client.get_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        current_config = response['dataSource']
        print(f"   Current chunking: {current_config.get('vectorIngestionConfiguration', {})}")
        
        # Use FIXED_SIZE chunking (simpler and more reliable than hierarchical)
        new_chunking_config = {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 2000,  # Much larger chunks (was ~300)
                "overlapPercentage": 20  # 20% overlap between chunks
            }
        }
        
        # Prepare update parameters - must include dataSourceConfiguration
        update_params = {
            "knowledgeBaseId": kb_id,
            "dataSourceId": data_source_id,
            "name": current_config['name'],
            "dataSourceConfiguration": current_config['dataSourceConfiguration'],  # Required
            "vectorIngestionConfiguration": {
                "chunkingConfiguration": new_chunking_config
            }
        }
        
        # Add description if it exists
        if 'description' in current_config:
            update_params['description'] = current_config['description']
        
        # Update data source
        client.update_data_source(**update_params)
        
        print(f"   ✅ Updated chunking configuration")
        print(f"      Strategy: FIXED_SIZE")
        print(f"      Max Tokens: 2000 (was ~300)")
        print(f"      Overlap: 20%")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating data source: {e}")
        import traceback
        traceback.print_exc()
        return False

def sync_data_source(client, kb_id, data_source_id, kb_name="Unknown"):
    """Trigger data source sync to apply new chunking."""
    print(f"\n🔄 Starting ingestion job for {kb_name} KB...")
    
    try:
        response = client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"   ✅ Ingestion job started: {job_id[:20]}...")
        print(f"   ⏳ This will take 5-15 minutes to complete")
        print(f"   📊 Monitor in AWS Console: Bedrock → Knowledge Bases → {kb_name}")
        
        return job_id
        
    except Exception as e:
        print(f"   ❌ Error starting ingestion job: {e}")
        return None

def list_data_sources(client, kb_id, kb_name="Unknown"):
    """List all data sources for a KB."""
    print(f"\n📂 Listing data sources for {kb_name} KB...")
    
    try:
        response = client.list_data_sources(knowledgeBaseId=kb_id)
        data_sources = response.get('dataSourceSummaries', [])
        
        if not data_sources:
            print(f"   ⚠️  No data sources found")
            return []
        
        print(f"   Found {len(data_sources)} data source(s):")
        for ds in data_sources:
            print(f"   - {ds['name']} (ID: {ds['dataSourceId'][:20]}...)")
        
        return data_sources
        
    except Exception as e:
        print(f"   ❌ Error listing data sources: {e}")
        return []

def main():
    print("\n🔍 Step 1: Getting KB IDs from LaunchDarkly...")
    provider_kb_id, policy_kb_id = get_kb_ids()
    
    print(f"\n✅ Found Knowledge Bases:")
    print(f"   Provider KB: {provider_kb_id[:20]}...")
    print(f"   Policy KB:   {policy_kb_id[:20]}...")
    
    print("\n🔍 Step 2: Connecting to AWS Bedrock...")
    client = get_bedrock_agent_client()
    print("   ✅ Connected to Bedrock Agent API")
    
    # Fix Provider KB (the one with chunk issues)
    print("\n" + "=" * 80)
    print("🔧 FIXING PROVIDER KB CHUNKING")
    print("=" * 80)
    
    provider_data_sources = list_data_sources(client, provider_kb_id, "Provider")
    
    if provider_data_sources:
        for ds in provider_data_sources:
            ds_id = ds['dataSourceId']
            
            # Update chunking
            success = update_data_source_chunking(client, provider_kb_id, ds_id, "Provider")
            
            if success:
                # Start sync job
                job_id = sync_data_source(client, provider_kb_id, ds_id, "Provider")
                
                if job_id:
                    print(f"\n✅ Provider KB fix initiated!")
                    print(f"   Wait 10-15 min, then re-test with: python test_chunk_sizes.py")
    
    # Fix Policy KB too (same issue likely exists)
    print("\n" + "=" * 80)
    print("🔧 FIXING POLICY KB CHUNKING")
    print("=" * 80)
    
    policy_data_sources = list_data_sources(client, policy_kb_id, "Policy")
    
    if policy_data_sources:
        for ds in policy_data_sources:
            ds_id = ds['dataSourceId']
            
            # Update chunking
            success = update_data_source_chunking(client, policy_kb_id, ds_id, "Policy")
            
            if success:
                # Start sync job
                sync_data_source(client, policy_kb_id, ds_id, "Policy")
    
    print("\n" + "=" * 80)
    print("✅ CHUNKING FIX COMPLETE")
    print("=" * 80)
    print("""
📋 Next Steps:
1. Wait 10-15 minutes for ingestion jobs to complete
2. Check AWS Console: Bedrock → Knowledge Bases → [Your KB] → Data sources
3. Verify status shows "Available" (not "Syncing")
4. Run: python test_chunk_sizes.py
5. Verify chunks are now 1500+ chars (instead of 700)
6. Test chatbot: Provider names should now be complete

Expected Results:
- Chunk size: 744 chars → 1500-2000 chars
- "Dr. Singh" → "Dr. Jessica E. Singh, MD"
- Accuracy: 65% → 90%+
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

