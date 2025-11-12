#!/usr/bin/env python3
"""Interactive Medical Insurance Support Chatbot.

This chatbot demonstrates the multi-agent system with LaunchDarkly AI Configs.
Features extensive debug logging to show how the system works.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile, format_profile_summary

# Load environment variables
load_dotenv()


# ANSI color codes for beautiful terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Custom colors
    AGENT = '\033[35m'  # Magenta
    USER = '\033[36m'   # Cyan
    SYSTEM = '\033[33m'  # Yellow
    DEBUG = '\033[90m'   # Gray


def print_header():
    """Print welcome header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("🏥  Medical Insurance Support Chatbot")
    print("     Multi-Agent System with LaunchDarkly AI Configs")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_section(title: str, color: str = Colors.OKBLUE):
    """Print a section divider."""
    print(f"\n{color}{Colors.BOLD}{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}{Colors.ENDC}")


def print_debug(label: str, value: str, indent: int = 0):
    """Print debug information."""
    indent_str = "  " * indent
    print(f"{Colors.DEBUG}{indent_str}🔍 {label}: {Colors.ENDC}{value}")


def print_info(message: str, indent: int = 0):
    """Print informational message."""
    indent_str = "  " * indent
    print(f"{Colors.OKCYAN}{indent_str}ℹ️  {message}{Colors.ENDC}")


def print_success(message: str, indent: int = 0):
    """Print success message."""
    indent_str = "  " * indent
    print(f"{Colors.OKGREEN}{indent_str}✅ {message}{Colors.ENDC}")


def print_warning(message: str, indent: int = 0):
    """Print warning message."""
    indent_str = "  " * indent
    print(f"{Colors.WARNING}{indent_str}⚠️  {message}{Colors.ENDC}")


def print_error(message: str, indent: int = 0):
    """Print error message."""
    indent_str = "  " * indent
    print(f"{Colors.FAIL}{indent_str}❌ {message}{Colors.ENDC}")


def print_agent_message(agent_name: str, message: str):
    """Print agent message."""
    print(f"{Colors.AGENT}{Colors.BOLD}🤖 {agent_name}:{Colors.ENDC} {message}")


def print_user_message(message: str):
    """Print user message."""
    print(f"{Colors.USER}{Colors.BOLD}👤 You:{Colors.ENDC} {message}")


def check_configuration():
    """Check if the system is properly configured."""
    print_section("System Configuration Check", Colors.SYSTEM)
    
    # Check LaunchDarkly
    ld_enabled = os.getenv("LAUNCHDARKLY_ENABLED", "false").lower() == "true"
    ld_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
    
    print_debug("LaunchDarkly Enabled", str(ld_enabled))
    if ld_key:
        print_debug("LaunchDarkly SDK Key", f"***{ld_key[-4:]}")
        print_success("LaunchDarkly configured")
    else:
        print_error("LaunchDarkly SDK key not found")
        return False
    
    # Check AWS configuration
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    aws_profile = os.getenv("AWS_PROFILE", "default")
    
    print_debug("AWS Region", aws_region)
    print_debug("AWS Profile", aws_profile)
    print_success("AWS configuration found")
    
    # Check LLM provider
    llm_provider = os.getenv("LLM_PROVIDER", "bedrock")
    llm_model = os.getenv("LLM_MODEL", "claude-3-5-sonnet")
    
    print_debug("Default LLM Provider", llm_provider)
    print_debug("Default LLM Model", llm_model)
    
    print_success("System configuration complete!")
    return True


def explain_system():
    """Explain how the system works."""
    print_section("How This Multi-Agent System Works", Colors.HEADER)
    
    print(f"\n{Colors.BOLD}Agent Architecture:{Colors.ENDC}")
    print(f"  {Colors.AGENT}1. Triage Router{Colors.ENDC} - Analyzes your query and routes to the right specialist")
    print(f"  {Colors.AGENT}2. Policy Specialist{Colors.ENDC} - Answers questions about coverage, benefits, and policies")
    print(f"     📚 RAG-Enhanced: Searches policy documents semantically")
    print(f"  {Colors.AGENT}3. Provider Specialist{Colors.ENDC} - Helps find in-network doctors and providers")
    print(f"     📚 RAG-Enhanced: Searches provider network semantically")
    print(f"  {Colors.AGENT}4. Scheduler Specialist{Colors.ENDC} - Schedules callbacks with human agents")
    print(f"  {Colors.AGENT}5. Brand Voice Agent{Colors.ENDC} - Transforms responses into ToggleHealth's brand voice")
    print(f"     ✨ Final quality gate for all customer-facing responses")
    
    print(f"\n{Colors.BOLD}LaunchDarkly AI Configs:{Colors.ENDC}")
    print("  • Each agent retrieves its own AI configuration from LaunchDarkly")
    print("  • Enables A/B testing different models per agent")
    print("  • Allows dynamic model switching without code changes")
    print("  • Tracks token usage and performance metrics")
    
    print(f"\n{Colors.BOLD}RAG (Retrieval-Augmented Generation):{Colors.ENDC}")
    print("  • Policy & Provider agents use Bedrock Knowledge Base")
    print("  • Semantic search over comprehensive documentation")
    print("  • Hybrid: RAG documents + structured database")
    print("  • Graceful fallback if RAG not configured")
    
    print(f"\n{Colors.BOLD}What You'll See:{Colors.ENDC}")
    print("  🔍 Debug logs showing which agent is active")
    print("  📚 RAG retrieval with relevance scores")
    print("  📊 Configuration details from LaunchDarkly")
    print("  🎯 Routing decisions and confidence scores")
    print("  💬 Agent responses and reasoning")
    print("  📈 Performance metrics (when available)")


def create_default_context():
    """Create default user context for the conversation.
    
    Creates a rich, LaunchDarkly-optimized user profile with comprehensive
    attributes for targeting, personalization, and RAG enhancement.
    """
    # Create comprehensive user profile following LaunchDarkly best practices
    profile = create_user_profile(
        name="Marek Poliks",
        location="San Francisco, CA",
        policy_id="TH-HMO-GOLD-2024",
        coverage_type="Gold HMO"
    )
    
    # Update session ID to be current
    profile["session_id"] = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    profile["user_key"] = f"marek-poliks-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return profile


def display_context(context: dict):
    """Display current user context."""
    print_section("Current User Context", Colors.SYSTEM)
    for key, value in context.items():
        print_debug(key.replace('_', ' ').title(), str(value), indent=1)


def process_query(user_query: str, user_context: dict):
    """Process a user query through the multi-agent system."""
    print_section(f"Processing Query at {datetime.now().strftime('%H:%M:%S')}", Colors.OKBLUE)
    
    print_user_message(user_query)
    
    # Show what we're doing
    print_info("Initializing multi-agent workflow...", indent=1)
    print_debug("Query Length", f"{len(user_query)} characters", indent=1)
    print_debug("Context Keys", ", ".join(user_context.keys()), indent=1)
    
    try:
        # Run the workflow
        print_info("Running agent workflow (this may take a few seconds)...", indent=1)
        print_debug("Stage 1", "Triage Router analyzing query...", indent=2)
        
        result = run_workflow(user_query, user_context)
        
        # Display detailed results
        print_section("Workflow Results", Colors.OKGREEN)
        
        # Show query type and routing
        if "query_type" in result:
            print_debug("Query Type", str(result["query_type"]), indent=1)
        
        if "next_agent" in result:
            print_debug("Routed To", result["next_agent"], indent=1)
        
        if "confidence_score" in result:
            confidence = result["confidence_score"]
            confidence_pct = f"{confidence * 100:.1f}%"
            if confidence >= 0.8:
                print_success(f"High confidence: {confidence_pct}", indent=1)
            elif confidence >= 0.6:
                print_info(f"Medium confidence: {confidence_pct}", indent=1)
            else:
                print_warning(f"Low confidence: {confidence_pct}", indent=1)
        
        if "escalation_needed" in result and result["escalation_needed"]:
            print_warning("Escalation to human agent recommended", indent=1)
        
        # Show agent-specific data
        if "agent_data" in result:
            print_debug("Agent-Specific Data", "Available", indent=1)
            for agent_name, agent_info in result["agent_data"].items():
                print_debug(f"  {agent_name}", f"{len(str(agent_info))} bytes", indent=2)
                
                # Show brand voice metadata if available
                if agent_name == "brand_voice_agent":
                    try:
                        import json
                        brand_info = json.loads(agent_info)
                        if brand_info.get("brand_applied"):
                            print_success(f"    ✨ Brand Voice Applied: Transformed {brand_info.get('specialist_type', 'unknown')} specialist response", indent=2)
                    except:
                        pass
                
                # Show RAG information if available
                if "rag_enabled" in agent_info:
                    if agent_info["rag_enabled"]:
                        doc_count = agent_info.get("rag_documents_retrieved", 0)
                        print_success(f"    RAG enabled: {doc_count} documents retrieved", indent=2)
                    else:
                        print_info(f"    RAG: No documents retrieved", indent=2)
        
        # Show the conversation flow
        if "messages" in result:
            print_section("Conversation Flow", Colors.OKCYAN)
            for i, msg in enumerate(result["messages"], 1):
                msg_type = msg.__class__.__name__
                content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                print_debug(f"Message {i} ({msg_type})", content_preview, indent=1)
        
        # Show final response
        print_section("Agent Response", Colors.OKGREEN)
        if "final_response" in result:
            response = result["final_response"]
            print_agent_message("Assistant", response)
        else:
            print_error("No response generated")
            
        return result
        
    except Exception as e:
        print_section("Error", Colors.FAIL)
        print_error(f"An error occurred: {str(e)}")
        import traceback
        print(f"\n{Colors.DEBUG}{traceback.format_exc()}{Colors.ENDC}")
        return None


def show_example_queries():
    """Show example queries users can try."""
    print_section("Example Queries You Can Try", Colors.HEADER)
    
    examples = [
        ("Policy Questions", [
            "What is my copay for seeing a specialist?",
            "Does my plan cover physical therapy?",
            "What's my deductible for this year?",
        ]),
        ("Provider Lookup", [
            "I need to find a cardiologist in Boston",
            "Can you recommend a dermatologist who accepts my insurance?",
            "Find me a primary care doctor near me",
        ]),
        ("Scheduling/Complex", [
            "I need to speak with someone about my claim denial",
            "This is urgent, I need help now",
            "Can I schedule a call with an agent?",
        ]),
    ]
    
    for category, queries in examples:
        print(f"\n{Colors.BOLD}{category}:{Colors.ENDC}")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")


def interactive_mode():
    """Run the chatbot in interactive mode."""
    # Check configuration first
    if not check_configuration():
        print_error("\nSystem not properly configured. Please check your .env file.")
        return 1
    
    # Explain the system
    explain_system()
    
    # Create user context
    user_context = create_default_context()
    display_context(user_context)
    
    # Show example queries
    show_example_queries()
    
    # Start conversation loop
    print_section("Start Chatting!", Colors.HEADER)
    print(f"{Colors.BOLD}Commands:{Colors.ENDC}")
    print("  • Type 'quit', 'exit', or 'q' to exit")
    print("  • Type 'help' to see example queries")
    print("  • Type 'context' to view/update user context")
    print("  • Type 'debug on/off' to toggle debug logging")
    print("  • Just type your question to get help!")
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            print(f"\n{Colors.USER}{Colors.BOLD}{'─'*80}{Colors.ENDC}")
            user_input = input(f"{Colors.USER}👤 You: {Colors.ENDC}").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print_section("Thanks for chatting!", Colors.HEADER)
                print_success(f"Processed {conversation_count} queries in this session")
                print(f"\n{Colors.BOLD}Come back soon! 👋{Colors.ENDC}\n")
                break
            
            elif user_input.lower() == "help":
                show_example_queries()
                continue
            
            elif user_input.lower() == "context":
                display_context(user_context)
                continue
            
            # Process the query
            conversation_count += 1
            result = process_query(user_input, user_context)
            
            # Ask if they want to continue
            if conversation_count % 3 == 0:
                print(f"\n{Colors.SYSTEM}💡 Tip: You can type 'help' for example queries or 'quit' to exit{Colors.ENDC}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.HEADER}Interrupted by user{Colors.ENDC}")
            print_section("Thanks for chatting!", Colors.HEADER)
            print_success(f"Processed {conversation_count} queries in this session")
            print(f"\n{Colors.BOLD}Come back soon! 👋{Colors.ENDC}\n")
            break
            
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            import traceback
            print(f"\n{Colors.DEBUG}{traceback.format_exc()}{Colors.ENDC}")
            print_warning("Continuing anyway...")
    
    return 0


def main():
    """Main entry point."""
    print_header()
    
    # Check if in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run a quick test
        print_info("Running in test mode with a sample query...\n")
        context = create_default_context()
        display_context(context)
        process_query("What is my copay for seeing a specialist?", context)
        return 0
    
    # Run interactive mode
    return interactive_mode()


if __name__ == "__main__":
    sys.exit(main())

