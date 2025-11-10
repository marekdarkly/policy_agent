#!/usr/bin/env python3
"""Quick AWS SSO login script for the marek profile.

Usage:
    python aws_sso_login.py
    # or make it executable and run:
    ./aws_sso_login.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run AWS SSO login for the marek profile."""
    profile = "marek"
    
    print(f"🔐 Logging in to AWS SSO with profile: {profile}")
    print("This will open your browser for authentication...\n")
    
    try:
        # Run aws sso login command
        result = subprocess.run(
            ["aws", "sso", "login", "--profile", profile],
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"\n✅ AWS SSO login successful for profile: {profile}")
            
            # Optionally verify credentials
            print("\n🔍 Verifying credentials...")
            verify_result = subprocess.run(
                ["aws", "sts", "get-caller-identity", "--profile", profile],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if verify_result.returncode == 0:
                print("✅ Credentials verified!")
                print("\nYour AWS identity:")
                print(verify_result.stdout)
                return 0
            else:
                print("⚠️  Login succeeded but verification failed:")
                print(verify_result.stderr)
                return 1
        else:
            print(f"\n❌ AWS SSO login failed for profile: {profile}")
            print("\nMake sure:")
            print(f"  1. The profile '{profile}' is configured in ~/.aws/config")
            print(f"  2. Run: aws configure sso (if not already configured)")
            return 1
            
    except subprocess.TimeoutExpired:
        print("\n❌ Login timed out (5 minutes)")
        return 1
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install AWS CLI:")
        print("   macOS: brew install awscli")
        print("   Linux: See https://aws.amazon.com/cli/")
        return 1
    except KeyboardInterrupt:
        print("\n\n❌ Login cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during AWS SSO login: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

