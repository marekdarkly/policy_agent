#!/usr/bin/env python3
"""Test script for AWS Bedrock connection and SSO authentication.

This script validates that:
1. AWS credentials are available and valid
2. Bedrock API is accessible
3. You can invoke a simple model request
4. The BedrockConverseLLM wrapper works correctly
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")


def test_environment_variables():
    """Test that required environment variables are set."""
    print_header("Test 1: Environment Variables")

    required_vars = {
        "AWS_PROFILE": os.getenv("AWS_PROFILE"),
        "AWS_REGION": os.getenv("AWS_REGION"),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
        "LLM_MODEL": os.getenv("LLM_MODEL"),
    }

    all_set = True
    for var, value in required_vars.items():
        is_set = value is not None and value != ""
        print_test(
            f"{var} is set",
            is_set,
            f"Value: {value}" if is_set else "Not set"
        )
        all_set = all_set and is_set

    return all_set


def test_boto3_import():
    """Test that boto3 can be imported."""
    print_header("Test 2: Boto3 Import")

    try:
        import boto3
        import botocore
        print_test("Import boto3", True, f"Version: {boto3.__version__}")
        print_test("Import botocore", True, f"Version: {botocore.__version__}")
        return True
    except ImportError as e:
        print_test("Import boto3/botocore", False, str(e))
        print("\n💡 Fix: pip install boto3 botocore")
        return False


def test_aws_sso_manager():
    """Test the AWS SSO Manager."""
    print_header("Test 3: AWS SSO Manager")

    try:
        from src.utils.aws_sso import AWSSSOManager

        profile = os.getenv("AWS_PROFILE", "agent")
        region = os.getenv("AWS_REGION", "us-east-1")

        print(f"Creating SSO manager (profile: {profile}, region: {region})")
        sso_manager = AWSSSOManager(profile_name=profile, region=region)
        print_test("Create SSO Manager", True)

        # Try to authenticate
        print("\nChecking authentication...")
        authenticated = sso_manager.ensure_authenticated()
        print_test("AWS Authentication", authenticated)

        if authenticated:
            # Try to get caller identity
            try:
                session = sso_manager.get_boto3_session()
                sts = session.client("sts")
                identity = sts.get_caller_identity()

                print("\n📋 Your AWS Identity:")
                print(f"   Account: {identity.get('Account')}")
                print(f"   User ID: {identity.get('UserId')}")
                print(f"   ARN: {identity.get('Arn')}")

                return True
            except Exception as e:
                print_test("Get caller identity", False, str(e))
                return False
        else:
            print("\n💡 Fix: Run 'aws sso login --profile {profile}'")
            return False

    except Exception as e:
        print_test("AWS SSO Manager", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_bedrock_client():
    """Test creating a Bedrock client."""
    print_header("Test 4: Bedrock Client")

    try:
        from src.utils.aws_sso import get_sso_manager

        profile = os.getenv("AWS_PROFILE", "agent")
        region = os.getenv("AWS_REGION", "us-east-1")

        sso_manager = get_sso_manager(profile_name=profile, region=region)

        # Try to create Bedrock client
        print("Creating Bedrock Runtime client...")
        client = sso_manager.get_bedrock_client("bedrock-runtime")
        print_test("Create Bedrock client", True, "bedrock-runtime")

        # Try to list foundation models (requires bedrock client, not bedrock-runtime)
        print("\nTesting Bedrock API access...")
        try:
            bedrock_client = sso_manager.get_bedrock_client("bedrock")
            response = bedrock_client.list_foundation_models()

            models = response.get("modelSummaries", [])
            print_test("List foundation models", True, f"Found {len(models)} models")

            # Show some Claude models
            claude_models = [m for m in models if "claude" in m.get("modelId", "").lower()]
            if claude_models:
                print("\n📋 Available Claude models:")
                for model in claude_models[:5]:
                    model_id = model.get("modelId")
                    status = model.get("modelLifecycle", {}).get("status", "unknown")
                    print(f"   - {model_id} ({status})")

            return True

        except Exception as e:
            error_msg = str(e)
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                print_test(
                    "List foundation models",
                    False,
                    "Access denied - check IAM permissions"
                )
                print("\n💡 Your IAM role needs bedrock:ListFoundationModels permission")
            else:
                print_test("List foundation models", False, error_msg)
            return False

    except Exception as e:
        print_test("Bedrock Client", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_bedrock_llm_wrapper():
    """Test the BedrockConverseLLM wrapper."""
    print_header("Test 5: BedrockConverseLLM Wrapper")

    try:
        from src.utils.bedrock_llm import BedrockConverseLLM, get_bedrock_model_id
        from langchain_core.messages import HumanMessage

        model_name = os.getenv("LLM_MODEL", "claude-3-haiku")  # Use Haiku for faster/cheaper test
        model_id = get_bedrock_model_id(model_name)

        print(f"Creating LLM wrapper (model: {model_name})")
        print(f"Full model ID: {model_id}")

        llm = BedrockConverseLLM(
            model_id=model_id,
            temperature=0.7,
            max_tokens=100,
            profile_name=os.getenv("AWS_PROFILE"),
            region=os.getenv("AWS_REGION"),
        )

        print_test("Create BedrockConverseLLM", True)

        # Try a simple invocation
        print("\nTesting model invocation...")
        print("Sending test message: 'Say hello in one sentence.'")

        try:
            messages = [HumanMessage(content="Say hello in one sentence.")]
            response = llm.invoke(messages)

            print_test("Invoke model", True)

            print("\n📋 Model Response:")
            print(f"   {response.content}")

            # Show token usage
            if hasattr(response, "response_metadata"):
                metadata = response.response_metadata
                token_usage = metadata.get("token_usage", {})
                print(f"\n📊 Token Usage:")
                print(f"   Input tokens:  {token_usage.get('input_tokens', 0)}")
                print(f"   Output tokens: {token_usage.get('output_tokens', 0)}")
                print(f"   Total tokens:  {token_usage.get('total_tokens', 0)}")

            return True

        except Exception as e:
            error_msg = str(e)
            print_test("Invoke model", False, error_msg)

            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                print("\n💡 Your IAM role needs bedrock:InvokeModel permission")
            elif "ValidationException" in error_msg or "ResourceNotFound" in error_msg:
                print("\n💡 The model may not be available in your region or account")
                print("   Go to AWS Console → Bedrock → Model access to enable models")
            elif "ThrottlingException" in error_msg:
                print("\n💡 Request was throttled - this is normal for free tier accounts")

            return False

    except Exception as e:
        print_test("BedrockConverseLLM Wrapper", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test a simple workflow with the multi-agent system."""
    print_header("Test 6: Full Workflow Integration")

    try:
        # This is optional - only run if user wants to test the full system
        print("This test will run a simple query through the multi-agent system.")
        print("It may take a few seconds and will use some Bedrock tokens.")

        response = input("\nRun full workflow test? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("Skipping full workflow test")
            return True

        from src.graph.workflow import run_workflow

        print("\nRunning test query...")
        result = run_workflow(
            user_message="What is my copay?",
            user_context={"policy_id": "POL-12345"}
        )

        if result and "final_response" in result:
            print_test("Run workflow", True)

            print("\n📋 Workflow Result:")
            print(f"   Query type: {result.get('query_type', 'unknown')}")
            print(f"   Response: {result['final_response'][:200]}...")

            return True
        else:
            print_test("Run workflow", False, "No response received")
            return False

    except Exception as e:
        print_test("Full Workflow", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_header("AWS Bedrock Connection Test Suite")

    print("This script will validate your AWS SSO and Bedrock setup.")
    print("Make sure you've run: aws sso login --profile agent")

    input("\nPress Enter to start tests...")

    # Run tests
    results = []

    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Boto3 Import", test_boto3_import()))

    # Only continue if basic tests pass
    if not all(r[1] for r in results):
        print_header("Test Results")
        print("❌ Basic tests failed. Fix the issues above before continuing.")
        return False

    results.append(("AWS SSO Manager", test_aws_sso_manager()))

    # Only test Bedrock if authentication works
    if results[-1][1]:
        results.append(("Bedrock Client", test_bedrock_client()))
        results.append(("BedrockConverseLLM", test_bedrock_llm_wrapper()))
        results.append(("Full Workflow", test_full_workflow()))

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your AWS Bedrock setup is working correctly.")
        print("\nYou can now run:")
        print("  python examples/run_example.py")
        return True
    else:
        print("\n⚠️  Some tests failed. Review the errors above.")
        print("\nCommon fixes:")
        print("  1. Run: aws sso login --profile agent")
        print("  2. Check your .env file configuration")
        print("  3. Verify Bedrock permissions in IAM")
        print("  4. Enable model access in Bedrock console")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
