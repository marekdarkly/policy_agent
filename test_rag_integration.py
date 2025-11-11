#!/usr/bin/env python3
"""Test script for Bedrock Knowledge Base RAG integration."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()


def test_bedrock_kb_configuration():
    """Test that Bedrock KB is configured."""
    print("\n" + "="*80)
    print("🧪 Testing Bedrock Knowledge Base Configuration")
    print("="*80 + "\n")
    
    policy_kb_id = os.getenv("BEDROCK_POLICY_KB_ID")
    provider_kb_id = os.getenv("BEDROCK_PROVIDER_KB_ID")
    
    print("Configuration Status:")
    if policy_kb_id:
        print(f"  ✅ BEDROCK_POLICY_KB_ID: {policy_kb_id[:20]}...")
    else:
        print(f"  ⚠️  BEDROCK_POLICY_KB_ID: Not configured")
        print(f"      → Add to .env to enable Policy RAG")
    
    if provider_kb_id:
        print(f"  ✅ BEDROCK_PROVIDER_KB_ID: {provider_kb_id[:20]}...")
    else:
        print(f"  ⚠️  BEDROCK_PROVIDER_KB_ID: Not configured")
        print(f"      → Add to .env to enable Provider RAG")
    
    if not policy_kb_id and not provider_kb_id:
        print("\n❌ RAG is not configured")
        print("   Agents will fall back to structured databases")
        print("\n💡 To enable RAG:")
        print("   1. Create Knowledge Bases in AWS Bedrock Console")
        print("   2. Add KB IDs to your .env file:")
        print("      BEDROCK_POLICY_KB_ID=your-policy-kb-id")
        print("      BEDROCK_PROVIDER_KB_ID=your-provider-kb-id")
        print("\n   See RAG_SETUP_GUIDE.md for detailed instructions")
        return False
    
    return True


def test_bedrock_kb_connection():
    """Test connection to Bedrock KB."""
    from src.tools.bedrock_rag import get_policy_retriever, get_provider_retriever
    
    print("\n" + "="*80)
    print("🧪 Testing Bedrock Knowledge Base Connection")
    print("="*80 + "\n")
    
    # Test Policy KB
    print("Testing Policy Knowledge Base...")
    policy_retriever = get_policy_retriever()
    
    if policy_retriever:
        try:
            print("  🔍 Attempting test retrieval...")
            documents = policy_retriever.retrieve("copay for specialist visit", {
                "vectorSearchConfiguration": {
                    "numberOfResults": 3
                }
            })
            
            print(f"  ✅ Policy KB connection successful!")
            print(f"     Retrieved {len(documents)} documents")
            
            if documents:
                print(f"\n  Sample document:")
                doc = documents[0]
                print(f"    Score: {doc.get('score', 0):.3f}")
                print(f"    Content preview: {doc.get('content', '')[:150]}...")
            
        except Exception as e:
            print(f"  ❌ Error connecting to Policy KB: {e}")
            print(f"     Check:")
            print(f"     - KB ID is correct")
            print(f"     - AWS credentials are valid")
            print(f"     - KB region matches AWS_REGION")
            return False
    else:
        print("  ⚠️  Policy KB not configured (RAG disabled)")
    
    print()
    
    # Test Provider KB
    print("Testing Provider Knowledge Base...")
    provider_retriever = get_provider_retriever()
    
    if provider_retriever:
        try:
            print("  🔍 Attempting test retrieval...")
            documents = provider_retriever.retrieve("cardiologist in Boston", {
                "vectorSearchConfiguration": {
                    "numberOfResults": 3
                }
            })
            
            print(f"  ✅ Provider KB connection successful!")
            print(f"     Retrieved {len(documents)} documents")
            
            if documents:
                print(f"\n  Sample document:")
                doc = documents[0]
                print(f"    Score: {doc.get('score', 0):.3f}")
                print(f"    Content preview: {doc.get('content', '')[:150]}...")
            
        except Exception as e:
            print(f"  ❌ Error connecting to Provider KB: {e}")
            print(f"     Check:")
            print(f"     - KB ID is correct")
            print(f"     - AWS credentials are valid")
            print(f"     - KB region matches AWS_REGION")
            print(f"     - Data source is synced")
            return False
    else:
        print("  ⚠️  Provider KB not configured (RAG disabled)")
    
    return True


def test_rag_in_agents():
    """Test RAG integration in agents."""
    from src.tools.bedrock_rag import retrieve_policy_documents, retrieve_provider_documents
    
    print("\n" + "="*80)
    print("🧪 Testing RAG Integration in Agents")
    print("="*80 + "\n")
    
    # Test policy RAG
    print("Testing Policy Specialist RAG...")
    try:
        policy_docs = retrieve_policy_documents(
            "Does my plan cover physical therapy?",
            policy_id="POL-12345"
        )
        
        if policy_docs:
            print(f"  ✅ Retrieved {len(policy_docs)} policy documents")
            for i, doc in enumerate(policy_docs[:3], 1):
                print(f"     Doc {i}: Score {doc.get('score', 0):.3f}")
        else:
            print(f"  ⚠️  No documents retrieved (RAG disabled or KB empty)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()
    
    # Test provider RAG
    print("Testing Provider Specialist RAG...")
    try:
        provider_docs = retrieve_provider_documents(
            "Find a dermatologist",
            specialty="dermatology",
            location="Boston",
            network="Premier Network"
        )
        
        if provider_docs:
            print(f"  ✅ Retrieved {len(provider_docs)} provider documents")
            for i, doc in enumerate(provider_docs[:3], 1):
                print(f"     Doc {i}: Score {doc.get('score', 0):.3f}")
        else:
            print(f"  ⚠️  No documents retrieved (RAG disabled or KB empty)")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Main test function."""
    print("\n" + "="*80)
    print("📚 Bedrock Knowledge Base RAG Integration Tests")
    print("="*80)
    
    # Test 1: Configuration
    configured = test_bedrock_kb_configuration()
    
    if not configured:
        print("\n" + "="*80)
        print("⚠️  RAG not configured. Tests using database fallback.")
        print("="*80 + "\n")
        return 0
    
    # Test 2: Connection
    print("\n" + "="*80)
    print("Testing Bedrock KB connection requires:")
    print("  1. Valid AWS credentials")
    print("  2. Bedrock KB created and synced")
    print("  3. IAM permissions for bedrock:Retrieve")
    print("="*80)
    
    proceed = input("\nProceed with connection test? (y/N): ").strip().lower()
    
    if proceed in ["y", "yes"]:
        test_bedrock_kb_connection()
        test_rag_in_agents()
    else:
        print("\n⏭️  Skipping connection tests")
    
    print("\n" + "="*80)
    print("✅ RAG Configuration Tests Complete")
    print("="*80)
    print("\n💡 Next steps:")
    print("   1. Create Bedrock KBs (see RAG_SETUP_GUIDE.md)")
    print("   2. Upload documents to S3")
    print("   3. Sync data sources")
    print("   4. Run: python interactive_chatbot.py")
    print("\n   The chatbot will show RAG retrieval in action!")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

