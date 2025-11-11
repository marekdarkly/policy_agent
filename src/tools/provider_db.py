"""Provider database tools."""

import json
import os
from pathlib import Path
from typing import Any

# Network name mapping: User-facing names to database codes
NETWORK_MAPPING = {
    "Premier Network": ["TH-PPO-PREMIER", "TH-HMO-PREMIER"],
    "Select Network": ["TH-EPO-SELECT", "TH-HMO-SELECT"],
    "Core Network": ["TH-HDHP-CORE"],
    "Primary Network": ["TH-HMO-PRIMARY"],
}

# Load real provider database
_PROVIDER_DATABASE = None

def _load_provider_database():
    """Load the provider database from JSON file."""
    global _PROVIDER_DATABASE
    if _PROVIDER_DATABASE is None:
        # Get path to data directory
        current_dir = Path(__file__).parent.parent.parent
        db_path = current_dir / "data" / "togglehealth_provider_database.json"
        
        if db_path.exists():
            with open(db_path, 'r') as f:
                data = json.load(f)
                
                # The JSON is organized by provider type, flatten all into one list
                all_providers = []
                provider_types = [
                    "hospitals",
                    "primary_care_physicians", 
                    "specialists",
                    "mental_health_providers",
                    "urgent_care_centers",
                    "physical_therapy_centers",
                    "pharmacies",
                    "imaging_centers",
                    "specialty_centers",
                    "laboratory_services"
                ]
                
                for ptype in provider_types:
                    if ptype in data:
                        providers = data[ptype]
                        if isinstance(providers, list):
                            all_providers.extend(providers)
                
                _PROVIDER_DATABASE = all_providers
                print(f"  📋 Loaded {len(_PROVIDER_DATABASE)} providers from database")
        else:
            print(f"⚠️  Provider database not found at {db_path}")
            _PROVIDER_DATABASE = []
    
    return _PROVIDER_DATABASE

def _normalize_network_name(user_network: str) -> list[str]:
    """Convert user-facing network name to database codes.
    
    Args:
        user_network: User-facing network name (e.g., "Premier Network")
        
    Returns:
        List of database network codes
    """
    # Check mapping
    for user_name, db_codes in NETWORK_MAPPING.items():
        if user_name.lower() in user_network.lower():
            return db_codes
    
    # If no mapping, return as-is
    return [user_network]


def search_providers(
    specialty: str | None = None,
    location: str | None = None,
    network: str | None = None,
    accepting_new_patients: bool | None = None,
) -> list[dict[str, Any]]:
    """Search for healthcare providers.

    Args:
        specialty: Provider specialty to filter by
        location: City or zip code to search in
        network: Insurance network (e.g., "Premier Network")
        accepting_new_patients: Filter by whether accepting new patients

    Returns:
        List of matching providers
    """
    # Load database
    database = _load_provider_database()
    results = database.copy()
    
    print(f"  🔍 Searching {len(results)} providers in database")

    # Filter by specialty
    if specialty:
        specialty_lower = specialty.lower()
        results = [
            p
            for p in results
            if "specialty" in p and specialty_lower in p.get("specialty", "").lower()
        ]
        print(f"  🔍 After specialty filter ({specialty}): {len(results)} providers")

    # Filter by location
    if location:
        location_lower = location.lower()
        filtered = []
        for p in results:
            # Check both provider address and facility address
            addr = p.get("address", p.get("location", {}))
            if isinstance(addr, dict):
                city = addr.get("city", "").lower()
                state = addr.get("state", "").lower()
                zip_code = addr.get("zip", "")
                
                if (location_lower in city or 
                    location_lower in state or 
                    location_lower in str(zip_code)):
                    filtered.append(p)
        results = filtered
        print(f"  🔍 After location filter ({location}): {len(results)} providers")

    # Filter by network
    if network:
        # Convert user-facing network name to database codes
        network_codes = _normalize_network_name(network)
        print(f"  🔍 Searching for networks: {network_codes}")
        
        filtered = []
        for p in results:
            # Check network_affiliations list
            affiliations = p.get("network_affiliations", [])
            if any(code in affiliations for code in network_codes):
                filtered.append(p)
        results = filtered
        print(f"  🔍 After network filter ({network}): {len(results)} providers")

    # Filter by accepting new patients
    if accepting_new_patients is not None:
        results = [
            p
            for p in results
            if p.get("accepting_new_patients") == accepting_new_patients
        ]
        print(f"  🔍 After accepting filter: {len(results)} providers")

    return results


def get_provider_details(provider_id: str) -> dict[str, Any] | None:
    """Get detailed information about a specific provider.

    Args:
        provider_id: The provider ID

    Returns:
        Provider details or None if not found
    """
    database = _load_provider_database()
    for provider in database:
        if provider.get("provider_id") == provider_id:
            return provider
    return None
