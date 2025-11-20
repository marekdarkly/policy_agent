#!/usr/bin/env python3
"""
Upload AI tools to LaunchDarkly using the API.

This script reads the tools from launchdarkly_tools_library.json and uploads
each tool to LaunchDarkly using the AI Tools API.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
# Check multiple possible env var names for API key
LD_API_KEY = (
    os.getenv("LAUNCHDARKLY_API_KEY") or 
    os.getenv("LD_API_KEY") or 
    os.getenv("LAUNCHDARKLY_ACCESS_TOKEN")
)
LD_PROJECT_KEY = os.getenv("LAUNCHDARKLY_PROJECT_KEY", "toggle-health-ai")  # Default project key
LD_API_VERSION = "beta"
LD_BASE_URL = "https://app.launchdarkly.com/api/v2"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def validate_config():
    """Validate that required configuration is present."""
    if not LD_API_KEY:
        print(f"{RED}❌ Error: LaunchDarkly API key not found in .env file{RESET}")
        print(f"{YELLOW}   Please add one of these to your .env file:{RESET}")
        print(f"   - LAUNCHDARKLY_API_KEY=your_api_key")
        print(f"   - LD_API_KEY=your_api_key")
        print(f"   - LAUNCHDARKLY_ACCESS_TOKEN=your_api_key")
        print(f"\n{BLUE}   Get your API key from:{RESET}")
        print(f"   LaunchDarkly → Account Settings → Authorization → Personal API access tokens")
        print(f"   Required scopes: createAccessToken, createProject, writeProject")
        sys.exit(1)
    
    if not LD_PROJECT_KEY:
        print(f"{RED}❌ Error: LAUNCHDARKLY_PROJECT_KEY not found in .env file{RESET}")
        print(f"{YELLOW}Please add LAUNCHDARKLY_PROJECT_KEY=your_project_key to your .env file{RESET}")
        print(f"{BLUE}Or the default 'toggle-health-ai' will be used{RESET}")
    
    print(f"{GREEN}✅ Configuration validated{RESET}")
    print(f"   API Key: {LD_API_KEY[:10]}...{LD_API_KEY[-4:]}")
    print(f"   Project Key: {LD_PROJECT_KEY}")


def load_tools_from_file(filepath: str = "launchdarkly_tools_library.json") -> list:
    """Load tools from the JSON file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            tools = data.get("tools", [])
            print(f"{GREEN}✅ Loaded {len(tools)} tools from {filepath}{RESET}")
            return tools
    except FileNotFoundError:
        print(f"{RED}❌ Error: {filepath} not found{RESET}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{RED}❌ Error parsing JSON: {e}{RESET}")
        sys.exit(1)


def create_tool_in_launchdarkly(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a single tool in LaunchDarkly using the API.
    
    Args:
        tool: Tool definition with key, name, description, schema, etc.
    
    Returns:
        API response as dictionary
    """
    url = f"{LD_BASE_URL}/projects/{LD_PROJECT_KEY}/ai-tools"
    
    # Prepare payload according to API spec
    payload = {
        "key": tool["key"],
        "name": tool["name"],
        "description": tool["description"],
        "schema": tool["schema"]
    }
    
    # Optional fields
    if "maintainerId" in tool:
        payload["maintainerId"] = tool["maintainerId"]
    if "maintainerTeamKey" in tool:
        payload["maintainerTeamKey"] = tool["maintainerTeamKey"]
    
    headers = {
        "LD-API-Version": LD_API_VERSION,
        "Authorization": LD_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            return {
                "success": True,
                "message": "Tool created successfully",
                "data": response.json()
            }
        elif response.status_code == 409:
            # Tool already exists
            return {
                "success": False,
                "message": "Tool already exists",
                "status_code": 409,
                "error": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"API error: {response.status_code}",
                "status_code": response.status_code,
                "error": response.json() if response.content else None
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Request failed: {str(e)}",
            "error": str(e)
        }


def update_tool_in_launchdarkly(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing tool in LaunchDarkly using PATCH.
    
    Args:
        tool: Tool definition
    
    Returns:
        API response as dictionary
    """
    url = f"{LD_BASE_URL}/projects/{LD_PROJECT_KEY}/ai-tools/{tool['key']}"
    
    # JSON Patch operations to update tool
    operations = [
        {"op": "replace", "path": "/name", "value": tool["name"]},
        {"op": "replace", "path": "/description", "value": tool["description"]},
        {"op": "replace", "path": "/schema", "value": tool["schema"]}
    ]
    
    headers = {
        "LD-API-Version": LD_API_VERSION,
        "Authorization": LD_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.patch(url, json=operations, headers=headers)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Tool updated successfully",
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"API error: {response.status_code}",
                "status_code": response.status_code,
                "error": response.json() if response.content else None
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Request failed: {str(e)}",
            "error": str(e)
        }


def main():
    """Main execution function."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🚀 LaunchDarkly AI Tools Uploader{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    # Validate configuration
    validate_config()
    print()
    
    # Load tools
    tools = load_tools_from_file()
    print()
    
    # Upload each tool
    results = {
        "created": [],
        "updated": [],
        "failed": [],
        "skipped": []
    }
    
    print(f"{BLUE}📤 Uploading tools to LaunchDarkly...{RESET}\n")
    
    for i, tool in enumerate(tools, 1):
        tool_key = tool["key"]
        tool_name = tool["name"]
        
        print(f"{YELLOW}[{i}/{len(tools)}]{RESET} {tool_key:<40}", end=" ", flush=True)
        
        # Try to create the tool
        result = create_tool_in_launchdarkly(tool)
        
        if result["success"]:
            print(f"{GREEN}✅ Created{RESET}")
            results["created"].append(tool_key)
        elif result.get("status_code") == 409:
            # Tool exists, try to update it
            print(f"{YELLOW}⚠️  Exists, updating...{RESET}", end=" ", flush=True)
            update_result = update_tool_in_launchdarkly(tool)
            if update_result["success"]:
                print(f"{GREEN}✅ Updated{RESET}")
                results["updated"].append(tool_key)
            else:
                print(f"{RED}❌ Update failed{RESET}")
                print(f"   Error: {update_result['message']}")
                results["failed"].append({
                    "key": tool_key,
                    "error": update_result.get("error")
                })
        else:
            print(f"{RED}❌ Failed{RESET}")
            print(f"   Error: {result['message']}")
            if result.get("error"):
                print(f"   Details: {json.dumps(result['error'], indent=2)}")
            results["failed"].append({
                "key": tool_key,
                "error": result.get("error")
            })
        
        # Rate limiting: small delay between requests
        if i < len(tools):
            time.sleep(0.5)
    
    # Print summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}📊 Upload Summary{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    print(f"{GREEN}✅ Created:{RESET} {len(results['created'])} tools")
    if results['created']:
        for key in results['created']:
            print(f"   - {key}")
    
    print(f"\n{YELLOW}🔄 Updated:{RESET} {len(results['updated'])} tools")
    if results['updated']:
        for key in results['updated']:
            print(f"   - {key}")
    
    if results['failed']:
        print(f"\n{RED}❌ Failed:{RESET} {len(results['failed'])} tools")
        for item in results['failed']:
            print(f"   - {item['key']}")
            if item.get('error'):
                print(f"     Error: {item['error']}")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{GREEN}✨ Upload complete!{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    # Exit code based on results
    if results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

