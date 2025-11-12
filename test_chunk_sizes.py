"""Test script to diagnose RAG chunk sizes and content.

This checks if Bedrock KB is returning chunks that are too small,
which could explain provider name truncation issues.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Initialize observability BEFORE any imports that need LD client
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

from src.tools.bedrock_rag import retrieve_provider_documents
from src.utils.user_profile import create_user_profile
from src.utils.launchdarkly_config import get_ld_client

print("=" * 80)
print("🔍 Testing Bedrock KB Chunk Sizes")
print("=" * 80)

# Create user context
user_context = create_user_profile(
    name="Test User",
    location="Boston, MA",
    policy_id="TH-HMO-GOLD-2024",
    coverage_type="Gold HMO"
)

# Test query
query = "find me a doctor in boston"

print(f"\n🔍 Query: {query}")
print(f"📍 Location: Boston, MA")
print(f"📋 Plan: TH-HMO-GOLD-2024")

try:
    # Get LaunchDarkly config with KB ID
    print("\n📡 Fetching LaunchDarkly AI Config for provider_agent...")
    ld_client = get_ld_client()
    ld_config, _, _ = ld_client.get_ai_config("provider_agent", user_context)
    
    # Extract KB ID
    model = ld_config.get("model", {})
    custom = model.get("custom", {})
    kb_id = custom.get("awskbid") or custom.get("aws_kb_id")
    
    if kb_id:
        print(f"✅ Found KB ID in LaunchDarkly: {kb_id[:20]}...")
    else:
        print("❌ No KB ID found in LaunchDarkly config")
        print("   Make sure 'awskbid' is set in provider_agent custom parameters")
        sys.exit(1)
    
    # Retrieve documents
    rag_documents = retrieve_provider_documents(
        query=query,
        location="Boston, MA",
        network="TH-HMO-PRIMARY",
        ld_config=ld_config  # Use config from LaunchDarkly
    )
    
    print(f"\n✅ Retrieved {len(rag_documents)} documents")
    print("\n" + "=" * 80)
    
    for i, doc in enumerate(rag_documents, 1):
        score = doc.get("score", 0.0)
        content = doc.get("content", "")
        
        print(f"\n📄 Document {i}")
        print(f"   Score: {score:.3f}")
        print(f"   Length: {len(content)} characters")
        print(f"   Lines: {len(content.split(chr(10)))} lines")
        
        # Check for provider names
        if "Dr." in content:
            import re
            names = re.findall(r'Dr\. [A-Za-z \.]+(?:,\s*[A-Z]{2,})?', content)
            print(f"   Provider names found: {len(names)}")
            for name in names[:3]:  # Show first 3
                print(f"     - {name}")
        
        # Show first 500 chars
        print(f"\n   Content preview (first 500 chars):")
        print(f"   {'-' * 76}")
        print(f"   {content[:500]}...")
        print(f"   {'-' * 76}")
        
        # Check for completeness
        if "Dr." in content:
            # Check if chunk appears to be cut off mid-provider
            lines = content.split('\n')
            last_line = lines[-1].strip() if lines else ""
            if last_line and not last_line.endswith(('.', '---', ')')):
                print(f"   ⚠️  WARNING: Chunk may be cut off (last line: '{last_line[-50:]}')")
            
            # Check for "####" headers (markdown provider entries)
            header_count = content.count("####")
            print(f"   Provider entries (#### headers): {header_count}")
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS")
    print("=" * 80)
    
    avg_length = sum(len(doc.get("content", "")) for doc in rag_documents) / len(rag_documents)
    print(f"Average chunk size: {avg_length:.0f} characters")
    
    # Check if any chunks are too small
    small_chunks = [doc for doc in rag_documents if len(doc.get("content", "")) < 500]
    if small_chunks:
        print(f"\n⚠️  Found {len(small_chunks)} chunks < 500 chars (potentially too small)")
    
    # Check if Dr. Singh appears
    for i, doc in enumerate(rag_documents, 1):
        content = doc.get("content", "")
        if "Singh" in content:
            print(f"\n✅ Found 'Singh' in Document {i}")
            # Extract context around Singh
            idx = content.find("Singh")
            context = content[max(0, idx-100):min(len(content), idx+200)]
            print(f"   Context: ...{context}...")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)
print("""
If chunks are < 1000 chars or cut off mid-provider:
1. Increase chunk size in Bedrock Knowledge Base (AWS Console)
2. Adjust chunking strategy to respect document structure (e.g., by headers)
3. Increase overlap between chunks

If provider names are incomplete in chunks:
- Problem confirmed: Chunks are too small
- Solution: Reconfigure KB with larger chunks or header-aware chunking
""")

