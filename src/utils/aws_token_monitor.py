"""
AWS SSO Token Monitor - Proactive expiration warnings.

Monitors AWS SSO token cache and provides warnings before expiration.
"""

import os
import json
import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any


class AWSTokenMonitor:
    """Monitors AWS SSO token expiration and provides warnings."""
    
    def __init__(self, profile_name: str = "marek"):
        """
        Initialize token monitor.
        
        Args:
            profile_name: AWS profile name (used to identify relevant cache files)
        """
        self.profile_name = profile_name
        self.sso_cache_dir = Path.home() / ".aws" / "sso" / "cache"
        self.last_warning_level = None
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Get current token status.
        
        Returns:
            Dict with:
                - valid: bool, whether token is valid
                - expires_at: ISO timestamp of expiration (if valid)
                - minutes_remaining: int, minutes until expiration (if valid)
                - warning_level: str, severity level (ok/warning/critical/expired)
                - message: str, user-facing message
        """
        try:
            # Find the most recent SSO token cache file
            token_data = self._get_latest_token()
            
            if not token_data:
                return {
                    "valid": False,
                    "warning_level": "expired",
                    "message": "No AWS SSO token found. Run: aws sso login --profile marek"
                }
            
            # Parse expiration time
            expires_at_str = token_data.get("expiresAt")
            if not expires_at_str:
                return {
                    "valid": False,
                    "warning_level": "expired",
                    "message": "Invalid token format. Run: aws sso login --profile marek"
                }
            
            # Convert to datetime (AWS uses ISO 8601 UTC)
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            
            # Calculate time remaining
            time_remaining = expires_at - now
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            
            # Determine warning level
            if minutes_remaining <= 0:
                warning_level = "expired"
                message = "⛔ AWS session expired! Run: aws sso login --profile marek"
                valid = False
            elif minutes_remaining <= 2:
                warning_level = "critical"
                message = f"🚨 AWS session expires in {minutes_remaining} minute(s)! Re-authenticate NOW!"
                valid = True
            elif minutes_remaining <= 5:
                warning_level = "warning"
                message = f"⚠️  AWS session expires in {minutes_remaining} minutes. Re-authenticate soon."
                valid = True
            elif minutes_remaining <= 10:
                warning_level = "info"
                message = f"ℹ️  AWS session expires in {minutes_remaining} minutes."
                valid = True
            else:
                warning_level = "ok"
                message = f"✅ AWS session valid ({minutes_remaining} minutes remaining)"
                valid = True
            
            return {
                "valid": valid,
                "expires_at": expires_at_str,
                "minutes_remaining": minutes_remaining,
                "warning_level": warning_level,
                "message": message
            }
            
        except Exception as e:
            return {
                "valid": False,
                "warning_level": "error",
                "message": f"⚠️  Error checking token: {e}"
            }
    
    def should_warn(self) -> bool:
        """
        Check if we should broadcast a warning (avoid spam).
        
        Returns:
            True if warning level has changed or is critical
        """
        status = self.get_token_status()
        current_level = status["warning_level"]
        
        # Always warn for critical/expired
        if current_level in ["critical", "expired"]:
            return True
        
        # Only warn if level changed
        if current_level != self.last_warning_level:
            self.last_warning_level = current_level
            return True
        
        return False
    
    def _get_latest_token(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent valid SSO token from cache.
        
        Returns:
            Token data dict or None if not found
        """
        if not self.sso_cache_dir.exists():
            return None
        
        # Get all cache files
        cache_files = glob.glob(str(self.sso_cache_dir / "*.json"))
        
        if not cache_files:
            return None
        
        # Find the most recently modified file (likely the active token)
        latest_file = max(cache_files, key=os.path.getmtime)
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                
                # Verify it has required fields
                if "accessToken" in data and "expiresAt" in data:
                    return data
        except (json.JSONDecodeError, IOError):
            pass
        
        return None

