import os
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LaunchDarklyAPIClient:
    def __init__(self):
        self.base_url = "https://app.launchdarkly.com/api/v2"
        self.api_token = os.getenv("LAUNCHDARKLY_API_TOKEN")  # Use LAUNCHDARKLY_API_TOKEN
        self.project_key = os.getenv("LAUNCHDARKLY_PROJECT_KEY", "aiconfigdemo-ld-demo")
        self.environment_key = os.getenv("LAUNCHDARKLY_ENVIRONMENT_KEY", "production")
        self.flag_key = "toggle-rag"
        
        if not self.api_token:
            logger.warning("LAUNCHDARKLY_API_TOKEN not found - flag auto-disable will not work")
            self.enabled = False
        else:
            self.enabled = True
    
    def _make_semantic_patch_request(self, endpoint: str, patch_data: Dict) -> Dict[str, Any]:
        """Make authenticated semantic patch request to LaunchDarkly API"""
        if not self.enabled:
            raise ValueError("LaunchDarkly API client not properly configured")
            
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json; domain-model=launchdarkly.semanticpatch",
            "LD-API-Version": "20240415"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.patch(url, headers=headers, json=patch_data)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"LaunchDarkly API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def _make_request(self, method: str, endpoint: str) -> Dict[str, Any]:
        """Make authenticated GET request to LaunchDarkly API"""
        if not self.enabled:
            raise ValueError("LaunchDarkly API client not properly configured")
            
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "LD-API-Version": "20240415"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"LaunchDarkly API request failed: {e}")
            raise
    
    def get_flag_status(self) -> Dict[str, Any]:
        """Get current flag status"""
        if not self.enabled:
            return {"error": "API client not configured"}
            
        endpoint = f"/flags/{self.project_key}/{self.flag_key}"
        return self._make_request("GET", endpoint)
    
    def disable_flag(self, comment: str = "Disabled by guardrail clamp") -> Dict[str, Any]:
        """Disable the feature flag in the specified environment"""
        if not self.enabled:
            logger.warning("Cannot disable flag - LaunchDarkly API client not configured")
            return {"error": "API client not configured"}
            
        endpoint = f"/flags/{self.project_key}/{self.flag_key}"
        
        patch_data = {
            "comment": f"{comment} - {datetime.utcnow().isoformat()}",
            "environmentKey": self.environment_key,
            "instructions": [
                {"kind": "turnFlagOff"}
            ]
        }
        
        try:
            result = self._make_semantic_patch_request(endpoint, patch_data)
            logger.critical(f"LaunchDarkly flag '{self.flag_key}' disabled in '{self.environment_key}': {comment}")
            return result
        except Exception as e:
            logger.error(f"Failed to disable LaunchDarkly flag: {e}")
            raise
    
    def enable_flag(self, comment: str = "Re-enabled after guardrail clamp") -> Dict[str, Any]:
        """Re-enable the feature flag (for recovery purposes)"""
        if not self.enabled:
            logger.warning("Cannot enable flag - LaunchDarkly API client not configured")
            return {"error": "API client not configured"}
            
        endpoint = f"/flags/{self.project_key}/{self.flag_key}"
        
        patch_data = {
            "comment": f"{comment} - {datetime.utcnow().isoformat()}",
            "environmentKey": self.environment_key,
            "instructions": [
                {"kind": "turnFlagOn"}
            ]
        }
        
        try:
            result = self._make_semantic_patch_request(endpoint, patch_data)
            logger.info(f"LaunchDarkly flag '{self.flag_key}' re-enabled in '{self.environment_key}': {comment}")
            return result
        except Exception as e:
            logger.error(f"Failed to enable LaunchDarkly flag: {e}")
            raise
    
    def is_flag_enabled(self) -> bool:
        """Check if the flag is currently enabled"""
        try:
            flag_status = self.get_flag_status()
            if "error" in flag_status:
                return True  # Default to enabled if we can't check
                
            env_config = flag_status.get("environments", {}).get(self.environment_key, {})
            return env_config.get("on", True)
        except Exception as e:
            logger.error(f"Failed to check flag status: {e}")
            return True  # Default to enabled on error 