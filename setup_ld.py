#!/usr/bin/env python3
"""Helper script to set up and test LaunchDarkly configuration.

This script will:
1. Check if .env exists, create from .env.example if not
2. Guide you through setting up LaunchDarkly
3. Test the configuration

Usage:
    source venv/bin/activate
    python3 setup_ld.py
    # or use the wrapper:
    ./setup_ld.sh
"""

import os
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print("❌ Error: python-dotenv not installed")
    print("\n💡 Activate the virtual environment first:")
    print("   source venv/bin/activate")
    print("\n   Or install dependencies:")
    print("   pip install python-dotenv")
    sys.exit(1)

def main():
    """Set up LaunchDarkly configuration."""
    print("🔧 LaunchDarkly Setup Helper")
    print("=" * 60)
    
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    # Create .env if it doesn't exist
    if not env_path.exists():
        print("\n📝 Creating .env file...")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print("✅ Created .env from .env.example")
        else:
            # Create basic .env
            env_path.write_text("""# AWS Configuration
AWS_PROFILE=marek
AWS_REGION=us-east-1
LLM_PROVIDER=bedrock
LLM_MODEL=claude-3-5-sonnet

# LaunchDarkly Configuration
LAUNCHDARKLY_ENABLED=false
LAUNCHDARKLY_SDK_KEY=
""")
            print("✅ Created basic .env file")
    else:
        print("\n✅ .env file already exists")
    
    # Load current config
    load_dotenv()
    
    current_enabled = os.getenv("LAUNCHDARKLY_ENABLED", "false").lower() == "true"
    current_key = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
    
    print("\n📋 Current Configuration:")
    print(f"   LAUNCHDARKLY_ENABLED: {current_enabled}")
    if current_key:
        print(f"   LAUNCHDARKLY_SDK_KEY: ***{current_key[-4:]}")
    else:
        print(f"   LAUNCHDARKLY_SDK_KEY: (not set)")
    
    # Ask if they want to configure LaunchDarkly
    if not current_enabled or not current_key:
        print("\n💡 To enable LaunchDarkly:")
        print("   1. Get your SDK key from LaunchDarkly dashboard")
        print("   2. Set LAUNCHDARKLY_ENABLED=true")
        print("   3. Set LAUNCHDARKLY_SDK_KEY=your-key-here")
        print("\n   Or edit .env manually and run this script again")
        
        configure = input("\n   Configure now? (y/N): ").strip().lower()
        
        if configure in ["y", "yes"]:
            enabled = input("   Enable LaunchDarkly? (y/N): ").strip().lower()
            if enabled in ["y", "yes"]:
                set_key(".env", "LAUNCHDARKLY_ENABLED", "true")
                print("   ✅ LAUNCHDARKLY_ENABLED set to true")
                
                sdk_key = input("   Enter your LaunchDarkly SDK key: ").strip()
                if sdk_key:
                    set_key(".env", "LAUNCHDARKLY_SDK_KEY", sdk_key)
                    print("   ✅ LAUNCHDARKLY_SDK_KEY set")
                    print("\n   🔄 Reloading environment...")
                    load_dotenv(override=True)
                else:
                    print("   ⚠️  SDK key not provided")
            else:
                print("   ℹ️  LaunchDarkly will remain disabled")
    
    # Test the configuration
    print("\n" + "=" * 60)
    print("🧪 Testing Configuration")
    print("=" * 60)
    
    # Run the quick test
    try:
        from quick_test import main as test_main
        test_main()
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        sys.exit(1)

