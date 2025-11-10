#!/usr/bin/env python3
"""Interactive AWS SSO setup script for Bedrock access.

This script guides you through setting up AWS SSO for use with Amazon Bedrock.
It will help you configure your AWS profile and test the connection.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(number: int, text: str):
    """Print a formatted step."""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)


def check_aws_cli():
    """Check if AWS CLI is installed."""
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip() or result.stderr.strip()
        print(f"✅ AWS CLI installed: {version}")
        return True
    except FileNotFoundError:
        print("❌ AWS CLI not found")
        return False
    except Exception as e:
        print(f"❌ Error checking AWS CLI: {e}")
        return False


def install_aws_cli_instructions():
    """Provide AWS CLI installation instructions."""
    print("\n📦 AWS CLI Installation Instructions:")
    print("\nFor macOS:")
    print("  brew install awscli")
    print("\nFor Linux:")
    print("  curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'")
    print("  unzip awscliv2.zip")
    print("  sudo ./aws/install")
    print("\nFor Windows:")
    print("  Download from: https://awscli.amazonaws.com/AWSCLIV2.msi")
    print("\nAfter installation, run this script again.")


def configure_aws_sso():
    """Guide user through AWS SSO configuration."""
    print("\n🔐 Configuring AWS SSO Profile")
    print("\nThis will run: aws configure sso")
    print("\nYou'll need:")
    print("  1. Your organization's AWS SSO start URL")
    print("  2. Your AWS SSO region (e.g., us-east-1)")
    print("  3. Account ID and role name")

    input("\nPress Enter to continue...")

    try:
        # Run aws configure sso
        result = subprocess.run(
            ["aws", "configure", "sso"],
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print("\n✅ AWS SSO configuration completed!")
            return True
        else:
            print("\n❌ AWS SSO configuration failed")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ Configuration timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ Error during configuration: {e}")
        return False


def manual_configuration_guide():
    """Provide manual AWS configuration guide."""
    print("\n📝 Manual AWS SSO Configuration Guide")
    print("\nIf the interactive setup didn't work, you can manually configure AWS SSO:")

    print("\n1. Create/edit ~/.aws/config file with:")
    print("""
[profile agent]
sso_session = agent
sso_account_id = YOUR_ACCOUNT_ID
sso_role_name = YOUR_ROLE_NAME
region = us-east-1
output = json

[sso-session agent]
sso_start_url = https://YOUR_ORG.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
""")

    print("\n2. Replace the following values:")
    print("   - YOUR_ACCOUNT_ID: Your AWS account ID (12 digits)")
    print("   - YOUR_ROLE_NAME: The role name you want to use")
    print("   - YOUR_ORG: Your organization's SSO identifier")

    print("\n3. Save the file and run: aws sso login --profile agent")


def login_to_sso(profile: str = "agent"):
    """Login to AWS SSO."""
    print(f"\n🔑 Logging in to AWS SSO (profile: {profile})")
    print("\nThis will open your browser for authentication...")

    input("\nPress Enter to continue...")

    try:
        result = subprocess.run(
            ["aws", "sso", "login", "--profile", profile],
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print("\n✅ AWS SSO login successful!")
            return True
        else:
            print("\n❌ AWS SSO login failed")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ Login timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ Error during login: {e}")
        return False


def verify_credentials(profile: str = "agent"):
    """Verify AWS credentials are working."""
    print(f"\n🔍 Verifying AWS credentials (profile: {profile})")

    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--profile", profile],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("\n✅ AWS credentials verified!")
            print("\nYour identity:")
            print(result.stdout)
            return True
        else:
            print("\n❌ Credential verification failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"\n❌ Error verifying credentials: {e}")
        return False


def check_bedrock_access(profile: str = "agent", region: str = "us-east-1"):
    """Check if Bedrock access is available."""
    print(f"\n🤖 Checking Bedrock access (profile: {profile}, region: {region})")

    try:
        # List foundation models
        result = subprocess.run(
            [
                "aws", "bedrock", "list-foundation-models",
                "--profile", profile,
                "--region", region
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("\n✅ Bedrock access verified!")
            print("\nAvailable foundation models:")
            # Parse and show available models
            import json
            try:
                data = json.loads(result.stdout)
                models = data.get("modelSummaries", [])

                # Show Claude models
                claude_models = [m for m in models if "claude" in m.get("modelId", "").lower()]
                if claude_models:
                    print("\nClaude models available:")
                    for model in claude_models[:5]:  # Show first 5
                        print(f"  - {model.get('modelId')}")

                print(f"\nTotal models available: {len(models)}")
            except json.JSONDecodeError:
                print(result.stdout[:500])  # Show first 500 chars

            return True
        else:
            print("\n⚠️  Bedrock access check failed:")
            print(result.stderr)
            print("\nThis might mean:")
            print("  1. You don't have Bedrock permissions in your role")
            print("  2. Bedrock is not available in your region")
            print("  3. You need to request model access in the Bedrock console")
            return False

    except Exception as e:
        print(f"\n❌ Error checking Bedrock access: {e}")
        return False


def update_env_file(profile: str = "agent", region: str = "us-east-1"):
    """Update .env file with AWS configuration."""
    env_path = Path(".env")

    if not env_path.exists():
        print("\n⚠️  .env file not found, creating from .env.example...")
        example_path = Path(".env.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
        else:
            print("❌ .env.example not found!")
            return False

    # Read current content
    content = env_path.read_text()

    # Update AWS_PROFILE and AWS_REGION
    import re
    content = re.sub(r'AWS_PROFILE=.*', f'AWS_PROFILE={profile}', content)
    content = re.sub(r'AWS_REGION=.*', f'AWS_REGION={region}', content)

    # Write back
    env_path.write_text(content)

    print(f"\n✅ Updated .env file:")
    print(f"   AWS_PROFILE={profile}")
    print(f"   AWS_REGION={region}")
    return True


def main():
    """Main setup flow."""
    print_header("AWS SSO Setup for Bedrock")

    print("This script will help you set up AWS SSO for testing Bedrock.")
    print("You'll need an AWS account with Bedrock access.")

    # Step 1: Check AWS CLI
    print_step(1, "Checking AWS CLI Installation")
    if not check_aws_cli():
        install_aws_cli_instructions()
        sys.exit(1)

    # Step 2: Get configuration details
    print_step(2, "Configuration Details")
    print("\nDefault configuration:")
    print("  Profile name: agent")
    print("  Region: us-east-1")

    use_defaults = input("\nUse default configuration? (Y/n): ").strip().lower()

    if use_defaults in ["n", "no"]:
        profile = input("Enter profile name [agent]: ").strip() or "agent"
        region = input("Enter AWS region [us-east-1]: ").strip() or "us-east-1"
    else:
        profile = "agent"
        region = "us-east-1"

    # Step 3: Configure AWS SSO
    print_step(3, "Configuring AWS SSO")
    print("\nChoose configuration method:")
    print("  1. Interactive (recommended)")
    print("  2. Manual configuration guide")
    print("  3. Skip (already configured)")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        if not configure_aws_sso():
            print("\n⚠️  Configuration failed. Would you like the manual guide?")
            if input("Show manual guide? (y/N): ").strip().lower() in ["y", "yes"]:
                manual_configuration_guide()
            sys.exit(1)
    elif choice == "2":
        manual_configuration_guide()
        input("\nPress Enter after manual configuration is complete...")
    elif choice == "3":
        print("Skipping configuration...")
    else:
        print("Invalid choice, skipping configuration...")

    # Step 4: Login to SSO
    print_step(4, "AWS SSO Login")
    if not login_to_sso(profile):
        print("\n❌ Login failed. Please try manually:")
        print(f"   aws sso login --profile {profile}")
        sys.exit(1)

    # Step 5: Verify credentials
    print_step(5, "Verifying Credentials")
    if not verify_credentials(profile):
        print("\n❌ Credential verification failed")
        sys.exit(1)

    # Step 6: Check Bedrock access
    print_step(6, "Checking Bedrock Access")
    bedrock_ok = check_bedrock_access(profile, region)

    if not bedrock_ok:
        print("\n⚠️  Bedrock access check failed, but credentials are valid.")
        print("You may need to:")
        print("  1. Enable Bedrock in your AWS account")
        print("  2. Request model access in the Bedrock console")
        print("  3. Update your IAM role permissions")

    # Step 7: Update .env file
    print_step(7, "Updating Configuration")
    update_env_file(profile, region)

    # Final summary
    print_header("Setup Complete!")

    print("✅ AWS SSO is configured and authenticated")
    print(f"✅ Profile: {profile}")
    print(f"✅ Region: {region}")

    if bedrock_ok:
        print("✅ Bedrock access verified")
    else:
        print("⚠️  Bedrock access needs additional setup")

    print("\nNext steps:")
    print("  1. Test the connection: python test_aws_bedrock.py")
    print("  2. Run the example: python examples/run_example.py")

    print("\nNote: Your SSO session will expire after 8-12 hours.")
    print(f"To re-authenticate, run: aws sso login --profile {profile}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
