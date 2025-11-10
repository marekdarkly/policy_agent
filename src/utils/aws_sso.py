"""AWS SSO manager for token refresh and session management."""

import os
import subprocess
import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

import boto3
from botocore.exceptions import ClientError, TokenRetrievalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AWSSSOManager:
    """Manages AWS SSO authentication and token refresh."""

    def __init__(self, profile_name: Optional[str] = None, region: Optional[str] = None):
        """Initialize AWS SSO Manager.

        Args:
            profile_name: AWS profile name (defaults to AWS_PROFILE env var)
            region: AWS region (defaults to AWS_REGION env var)
        """
        self.profile_name = profile_name or os.getenv("AWS_PROFILE", "default")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.last_check = None
        self.check_interval = 300  # Check every 5 minutes

        print(f"🔐 AWS SSO Manager initialized (profile: {self.profile_name}, region: {self.region})")

    def ensure_authenticated(self) -> bool:
        """Ensure AWS credentials are valid, refresh if needed.

        Returns:
            True if authentication is successful, False otherwise
        """
        # Check if we need to verify credentials
        current_time = time.time()
        if self.last_check and (current_time - self.last_check) < self.check_interval:
            return True

        try:
            # Try to create a session and check credentials
            session = boto3.Session(profile_name=self.profile_name, region_name=self.region)
            sts = session.client("sts")
            sts.get_caller_identity()

            self.last_check = current_time
            print(f"✅ AWS credentials valid for profile: {self.profile_name}")
            return True

        except (ClientError, TokenRetrievalError) as e:
            print(f"⚠️  AWS credentials expired or invalid: {e}")
            return self._refresh_credentials()

    def _refresh_credentials(self) -> bool:
        """Refresh AWS SSO credentials via CLI.

        Returns:
            True if refresh is successful, False otherwise
        """
        print(f"🔄 Attempting to refresh AWS SSO credentials for profile: {self.profile_name}")

        try:
            # Run aws sso login command
            cmd = ["aws", "sso", "login", "--profile", self.profile_name]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                print(f"✅ AWS SSO login successful for profile: {self.profile_name}")
                self.last_check = time.time()
                return True
            else:
                print(f"❌ AWS SSO login failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ AWS SSO login timed out (5 minutes)")
            return False
        except FileNotFoundError:
            print("❌ AWS CLI not found. Please install AWS CLI: https://aws.amazon.com/cli/")
            return False
        except Exception as e:
            print(f"❌ Error during AWS SSO login: {e}")
            return False

    def get_boto3_session(self) -> boto3.Session:
        """Get a boto3 session with valid credentials.

        Returns:
            boto3.Session with valid credentials

        Raises:
            RuntimeError: If authentication fails
        """
        if not self.ensure_authenticated():
            raise RuntimeError(
                f"Failed to authenticate with AWS SSO (profile: {self.profile_name}). "
                f"Please run 'aws sso login --profile {self.profile_name}' manually."
            )

        return boto3.Session(profile_name=self.profile_name, region_name=self.region)

    def get_bedrock_client(self, service_name: str = "bedrock-runtime"):
        """Get a Bedrock client with valid credentials.

        Args:
            service_name: AWS service name (default: bedrock-runtime)

        Returns:
            Boto3 client for Bedrock

        Raises:
            RuntimeError: If authentication fails
        """
        session = self.get_boto3_session()
        return session.client(service_name, region_name=self.region)

    def force_refresh(self) -> bool:
        """Force a credential refresh regardless of check interval.

        Returns:
            True if refresh is successful, False otherwise
        """
        self.last_check = None
        return self._refresh_credentials()


@lru_cache(maxsize=1)
def get_sso_manager(
    profile_name: Optional[str] = None, region: Optional[str] = None
) -> AWSSSOManager:
    """Get the singleton AWS SSO Manager instance.

    Args:
        profile_name: AWS profile name (defaults to AWS_PROFILE env var)
        region: AWS region (defaults to AWS_REGION env var)

    Returns:
        AWSSSOManager instance
    """
    return AWSSSOManager(profile_name=profile_name, region=region)


def check_aws_credentials() -> bool:
    """Quick check if AWS credentials are available.

    Returns:
        True if credentials are available, False otherwise
    """
    try:
        sso_manager = get_sso_manager()
        return sso_manager.ensure_authenticated()
    except Exception as e:
        print(f"❌ AWS credentials check failed: {e}")
        return False
