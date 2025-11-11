"""Bedrock Knowledge Base RAG tools for policy and provider retrieval."""

import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()


class BedrockKnowledgeBaseRetriever:
    """Retriever for AWS Bedrock Knowledge Base.
    
    Uses Bedrock's Knowledge Base service for semantic search and retrieval.
    Supports both retrieve() and retrieve_and_generate() APIs.
    """

    def __init__(
        self,
        knowledge_base_id: str,
        region: Optional[str] = None,
        profile: Optional[str] = None,
        top_k: int = 5,
    ):
        """Initialize Bedrock KB retriever.

        Args:
            knowledge_base_id: The Bedrock Knowledge Base ID
            region: AWS region (defaults to AWS_REGION env var)
            profile: AWS profile (defaults to AWS_PROFILE env var)
            top_k: Number of documents to retrieve
        """
        self.knowledge_base_id = knowledge_base_id
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.profile = profile or os.getenv("AWS_PROFILE")
        self.top_k = top_k
        self._client = None

    def _get_client(self):
        """Get or create Bedrock Agent Runtime client.
        
        Returns:
            Bedrock Agent Runtime client
        """
        if self._client is None:
            from ..utils.aws_sso import get_sso_manager
            
            # Get authenticated session via SSO manager
            sso_manager = get_sso_manager(profile_name=self.profile, region=self.region)
            session = sso_manager.get_boto3_session()
            
            # Create Bedrock Agent Runtime client
            self._client = session.client(
                service_name="bedrock-agent-runtime",
                region_name=self.region
            )
            
            print(f"🔍 Bedrock KB Retriever initialized (KB: {self.knowledge_base_id[:20]}...)")
        
        return self._client

    def retrieve(
        self,
        query: str,
        retrieval_config: Optional[dict] = None
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents from Bedrock Knowledge Base.

        Args:
            query: The search query
            retrieval_config: Optional retrieval configuration

        Returns:
            List of retrieved documents with content and metadata
        """
        client = self._get_client()
        
        # Default retrieval configuration
        if retrieval_config is None:
            retrieval_config = {
                "vectorSearchConfiguration": {
                    "numberOfResults": self.top_k
                }
            }
        
        print(f"  🔍 Retrieving from Bedrock KB: '{query[:60]}...'")
        
        try:
            response = client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration=retrieval_config
            )
            
            # Extract results
            results = []
            if "retrievalResults" in response:
                for result in response["retrievalResults"]:
                    doc = {
                        "content": result.get("content", {}).get("text", ""),
                        "score": result.get("score", 0.0),
                        "location": result.get("location", {}),
                        "metadata": result.get("metadata", {})
                    }
                    results.append(doc)
                
                print(f"  ✅ Retrieved {len(results)} documents (top score: {results[0]['score']:.3f})" if results else "  ⚠️  No documents retrieved")
            
            return results
            
        except Exception as e:
            print(f"  ❌ Error retrieving from Bedrock KB: {e}")
            raise

    def retrieve_and_generate(
        self,
        query: str,
        model_arn: Optional[str] = None,
        generation_config: Optional[dict] = None
    ) -> dict[str, Any]:
        """Retrieve documents and generate response using Bedrock KB.

        This uses Bedrock's built-in RAG capability (RetrieveAndGenerate API).

        Args:
            query: The user query
            model_arn: ARN of the model to use for generation
            generation_config: Optional generation configuration

        Returns:
            Dictionary with generated response and citations
        """
        client = self._get_client()
        
        # Default to Claude 3.5 Sonnet if no model specified
        if model_arn is None:
            model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        # Default generation config
        if generation_config is None:
            generation_config = {
                "inferenceConfig": {
                    "textInferenceConfig": {
                        "temperature": 0.7,
                        "maxTokens": 2000
                    }
                }
            }
        
        print(f"  🔍 RetrieveAndGenerate from Bedrock KB: '{query[:60]}...'")
        
        try:
            response = client.retrieve_and_generate(
                input={"text": query},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": model_arn,
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": self.top_k
                            }
                        },
                        "generationConfiguration": generation_config
                    }
                }
            )
            
            # Extract response
            result = {
                "output": response.get("output", {}).get("text", ""),
                "citations": response.get("citations", []),
                "session_id": response.get("sessionId", "")
            }
            
            print(f"  ✅ Generated response ({len(result['citations'])} citations)")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error in RetrieveAndGenerate: {e}")
            raise


# Bedrock Knowledge Base IDs (configure in .env or here)
POLICY_KB_ID = os.getenv("BEDROCK_POLICY_KB_ID", "")
PROVIDER_KB_ID = os.getenv("BEDROCK_PROVIDER_KB_ID", "")


def get_policy_retriever(top_k: int = 5) -> Optional[BedrockKnowledgeBaseRetriever]:
    """Get retriever for policy knowledge base.

    Args:
        top_k: Number of documents to retrieve

    Returns:
        Bedrock KB retriever for policies, or None if not configured
    """
    if not POLICY_KB_ID:
        print("  ⚠️  BEDROCK_POLICY_KB_ID not configured, RAG disabled for policy")
        return None
    
    return BedrockKnowledgeBaseRetriever(
        knowledge_base_id=POLICY_KB_ID,
        top_k=top_k
    )


def get_provider_retriever(top_k: int = 5) -> Optional[BedrockKnowledgeBaseRetriever]:
    """Get retriever for provider network knowledge base.

    Args:
        top_k: Number of documents to retrieve

    Returns:
        Bedrock KB retriever for providers, or None if not configured
    """
    if not PROVIDER_KB_ID:
        print("  ⚠️  BEDROCK_PROVIDER_KB_ID not configured, RAG disabled for providers")
        return None
    
    return BedrockKnowledgeBaseRetriever(
        knowledge_base_id=PROVIDER_KB_ID,
        top_k=top_k
    )


def retrieve_policy_documents(query: str, policy_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieve relevant policy documents using RAG.

    Args:
        query: The user's query about their policy
        policy_id: Optional policy ID to filter results

    Returns:
        List of relevant policy documents with content and metadata
    """
    print(f"📚 Retrieving policy documents via RAG...")
    
    retriever = get_policy_retriever()
    if not retriever:
        print("  ℹ️  Falling back to simulated policy database")
        return []
    
    # Enhance query with policy ID if available
    enhanced_query = query
    if policy_id:
        enhanced_query = f"Policy {policy_id}: {query}"
    
    try:
        documents = retriever.retrieve(enhanced_query)
        return documents
    except Exception as e:
        print(f"  ⚠️  RAG retrieval failed: {e}, falling back to database")
        return []


def retrieve_provider_documents(
    query: str,
    specialty: Optional[str] = None,
    location: Optional[str] = None,
    network: Optional[str] = None
) -> list[dict[str, Any]]:
    """Retrieve relevant provider network documents using RAG.

    Args:
        query: The user's query about providers
        specialty: Provider specialty filter
        location: Location filter
        network: Insurance network filter

    Returns:
        List of relevant provider documents with content and metadata
    """
    print(f"📚 Retrieving provider documents via RAG...")
    
    retriever = get_provider_retriever()
    if not retriever:
        print("  ℹ️  Falling back to simulated provider database")
        return []
    
    # Enhance query with filters
    filters = []
    if specialty:
        filters.append(f"specialty: {specialty}")
    if location:
        filters.append(f"location: {location}")
    if network:
        filters.append(f"network: {network}")
    
    enhanced_query = query
    if filters:
        enhanced_query = f"{query} ({', '.join(filters)})"
    
    try:
        documents = retriever.retrieve(enhanced_query)
        return documents
    except Exception as e:
        print(f"  ⚠️  RAG retrieval failed: {e}, falling back to database")
        return []

