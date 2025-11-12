#!/usr/bin/env python3
"""
User Service Module for ToggleBank RAG System

Provides user context and profile information. Currently simulated but designed
to be easily replaced with real authentication/session management later.
"""
import uuid
import logging
from typing import Dict, Any, Optional
from ldclient import Context

class UserService:
    """
    User service that provides user context and profile information.
    Currently simulated but designed for easy extension to real auth systems.
    """
    
    def __init__(self):
        # Simulated user database - in production this would be a real database/API
        self.simulated_users = {
            "catherine_liu": {
                "user_id": "user_001",
                "name": "Catherine Liu",
                "location": "Boston, MA",
                "tier": "Silver",
                "userName": "Catherine Liu",
                "email": "catherine.liu@example.com",
                "account_since": "2020-09-10",
                "average_balance": "<1k",
                "preferred_channel": "phone",
                "language": "en"
            },
            "ingrid_zhou": {
                "user_id": "user_002", 
                "name": "Ingrid Zhou",
                "location": "Jacksonville, FL",
                "tier": "Diamond",
                "userName": "Ingrid Zhou",
                "email": "ingrid.zhou@example.com",
                "account_since": "2022-08-06",
                "average_balance": "50k-100k",
                "preferred_channel": "branch",
                "language": "de"
            },
            "demo_user": {
                "user_id": "user_demo",
                "name": "Demo User",
                "location": "San Francisco, CA",
                "tier": "Gold",
                "userName": "Demo User",
                "email": "demo@example.com",
                "account_since": "2023-01-01",
                "average_balance": "10k-25k",
                "preferred_channel": "mobile",
                "language": "en"
            },
            "kai_al_rashid": {
                "user_id": "user_kai_al_rashid",
                "name": "Kai Al-Rashid",
                "location": "Omaha, NE",
                "tier": "Platinum",
                "userName": "Kai Al-Rashid",
                "email": "kai.alrashid@example.com",
                "account_since": "2016-09-23",
                "average_balance": "50k-100k",
                "preferred_channel": "phone",
                "language": "de"
            }
        }
        
        # Default user for demo purposes – switched to a tier/balance-consistent profile
        self.current_user_key = "kai_al_rashid"
        
    def get_current_user_profile(self) -> Dict[str, Any]:
        """
        Get the current user's profile information.
        In production, this would get the user from session/token.
        """
        return self.simulated_users.get(self.current_user_key, self.simulated_users["demo_user"])
    
    def get_user_context_for_launchdarkly(self) -> Context:
        """
        Create a LaunchDarkly Context object for the current user.
        This includes user attributes for feature flag targeting and AI personalization.
        """
        profile = self.get_current_user_profile()
        unique_user_key = f"user-{uuid.uuid4().hex[:8]}"
        
        context_builder = Context.builder(unique_user_key).kind("user").name(profile["name"])
        
        # Add all user attributes to the context
        for key, value in profile.items():
            if key != "name":  # name is already set
                context_builder = context_builder.set(key, value)
        
        # Note: Industry will be added dynamically when the context is used
        # by evaluating the nt-toggle-rag-demo flag
                
        return context_builder.build()
    
    def set_current_user(self, user_key: str) -> bool:
        """
        Switch to a different user (for testing/demo purposes).
        In production, this would be handled by authentication.
        
        Args:
            user_key: Key identifying the user (e.g., "catherine_liu", "ingrid_zhou")
            
        Returns:
            bool: True if user exists and was set, False otherwise
        """
        if user_key in self.simulated_users:
            self.current_user_key = user_key
            logging.info(f"Switched to user: {self.simulated_users[user_key]['name']}")
            return True
        else:
            logging.warning(f"User key '{user_key}' not found in simulated users")
            return False
    
    def get_available_users(self) -> Dict[str, str]:
        """
        Get list of available users for demo/testing purposes.
        
        Returns:
            Dict mapping user_key to display name
        """
        return {key: user["name"] for key, user in self.simulated_users.items()}
    
    def authenticate_user(self, session_token: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Placeholder for future authentication logic.
        Currently returns the current demo user.
        
        Args:
            session_token: JWT or session token (for future implementation)
            user_id: User ID from authentication system (for future implementation)
            
        Returns:
            User profile dict if authenticated, None if not
        """
        # TODO: Implement real authentication here
        # For now, just return current user
        return self.get_current_user_profile()
    
    def get_user_context_for_prompt(self) -> Dict[str, Any]:
        """
        Get user context optimized for prompt generation.
        Returns a clean dict suitable for prompt templates.
        """
        profile = self.get_current_user_profile()
        
        # Return only the fields needed for prompt generation
        return {
            "name": profile["name"],
            "tier": profile["tier"],
            "location": profile["location"],
            "user_id": profile["user_id"]
        }

# Global user service instance
_user_service = UserService()

def get_user_service() -> UserService:
    """
    Get the global user service instance.
    This allows for easy dependency injection and testing.
    """
    return _user_service

# Convenience functions for common operations
def get_current_user_context() -> Context:
    """Get LaunchDarkly context for current user."""
    return get_user_service().get_user_context_for_launchdarkly()

def get_current_user_profile() -> Dict[str, Any]:
    """Get full profile for current user."""
    return get_user_service().get_current_user_profile()

def switch_demo_user(user_key: str) -> bool:
    """Switch to a different demo user."""
    return get_user_service().set_current_user(user_key) 