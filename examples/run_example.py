"""Example usage of the medical insurance support multi-agent system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.workflow import run_workflow


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def run_policy_question_example():
    """Example: Policy question."""
    print("🏥 EXAMPLE 1: Policy Coverage Question")
    print_separator()

    user_message = "What is my copay for seeing a specialist?"
    user_context = {
        "policy_id": "POL-12345",
        "coverage_type": "Gold Plan",
    }

    print(f"User Query: {user_message}")
    print(f"User Context: {user_context}")
    print("\nProcessing...")

    result = run_workflow(user_message, user_context)

    print("\n📋 Final Response:")
    print(result.get("final_response", "No response generated"))
    print(f"\n🎯 Query Type: {result.get('query_type')}")
    print(f"✅ Confidence: {result.get('confidence_score', 0):.2f}")


def run_provider_lookup_example():
    """Example: Provider lookup."""
    print("🏥 EXAMPLE 2: Provider Lookup")
    print_separator()

    user_message = "I need to find a cardiologist in Boston who is in-network."
    user_context = {
        "policy_id": "POL-12345",
        "network": "Premier Network",
        "location": "Boston, MA",
    }

    print(f"User Query: {user_message}")
    print(f"User Context: {user_context}")
    print("\nProcessing...")

    result = run_workflow(user_message, user_context)

    print("\n📋 Final Response:")
    print(result.get("final_response", "No response generated"))
    print(f"\n🎯 Query Type: {result.get('query_type')}")
    print(f"✅ Confidence: {result.get('confidence_score', 0):.2f}")


def run_schedule_agent_example():
    """Example: Schedule live agent."""
    print("🏥 EXAMPLE 3: Schedule Live Agent")
    print_separator()

    user_message = "This is very urgent, I need to speak with someone about my claim denial."
    user_context = {
        "policy_id": "POL-12345",
    }

    print(f"User Query: {user_message}")
    print(f"User Context: {user_context}")
    print("\nProcessing...")

    result = run_workflow(user_message, user_context)

    print("\n📋 Final Response:")
    print(result.get("final_response", "No response generated"))
    print(f"\n🎯 Query Type: {result.get('query_type')}")
    print(f"✅ Confidence: {result.get('confidence_score', 0):.2f}")
    print(f"⚠️  Escalation Needed: {result.get('escalation_needed', False)}")


def run_interactive_mode():
    """Run in interactive mode."""
    print("🏥 Medical Insurance Support - Interactive Mode")
    print_separator()
    print("Enter your questions (or 'quit' to exit)\n")

    # Default user context
    user_context = {
        "policy_id": "POL-12345",
        "coverage_type": "Gold Plan",
        "network": "Premier Network",
        "location": "Boston, MA",
    }

    print(f"Using context: {user_context}\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nThank you for using Medical Insurance Support!")
                break

            print("\nProcessing...\n")
            result = run_workflow(user_input, user_context)

            print("Assistant:", result.get("final_response", "No response generated"))
            print(
                f"\n[Query Type: {result.get('query_type')}, "
                f"Confidence: {result.get('confidence_score', 0):.2f}]"
            )
            print_separator()

        except KeyboardInterrupt:
            print("\n\nThank you for using Medical Insurance Support!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


def main():
    """Main function to run examples."""
    print("\n🏥 Medical Insurance Support Multi-Agent System")
    print("=" * 80)

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        run_interactive_mode()
    else:
        # Run all examples
        run_policy_question_example()
        print_separator()

        run_provider_lookup_example()
        print_separator()

        run_schedule_agent_example()
        print_separator()

        print("\n💡 Tip: Run 'python examples/run_example.py interactive' for interactive mode")


if __name__ == "__main__":
    main()
