import asyncio
import json
import ldclient
from ldclient.config import Config
import os
import random
import requests
import time
from typing import Dict, Any, List, Optional, Set, Deque
import uuid
from contextlib import asynccontextmanager
from collections import deque

from app.models import LDConfig, SimulationStatus, MetricStats, SimulationStats, LogEntry
from app.utils import create_multi_context, error_chance

# Constants for stats tracking
STATS_UPDATE_INTERVAL = 5.0  # Update stats every 5 seconds

# Global variables to track simulation state
# Replace single status with dict of session_id -> status
simulation_statuses: Dict[str, SimulationStatus] = {}
active_clients: Dict[str, Dict[str, Any]] = {}  # session_id -> client info
connected_websockets: Dict[str, Set] = {}  # session_id -> set of websockets

# Stats tracking - session-specific
session_stats: Dict[str, Dict[str, Any]] = {}

# Message deduplication - session-specific
last_messages: Dict[str, Deque[str]] = {}
last_message_times: Dict[str, float] = {}

def get_or_create_status(session_id: str) -> SimulationStatus:
    """Get or create a simulation status for a given session"""
    if session_id not in simulation_statuses:
        simulation_statuses[session_id] = SimulationStatus(
            session_id=session_id,
            running=False
        )
        # Initialize stats tracking for this session
        session_stats[session_id] = {
            "control_latency_values": [],
            "treatment_latency_values": [],
            "control_error_count": 0,
            "treatment_error_count": 0,
            "control_error_total": 0,
            "treatment_error_total": 0,
            "control_business_count": 0,
            "treatment_business_count": 0,
            "control_business_total": 0,
            "treatment_business_total": 0
        }
        # Initialize message deduplication for this session
        last_messages[session_id] = deque(maxlen=10)
        last_message_times[session_id] = 0.0
        # Initialize websockets set for this session
        connected_websockets[session_id] = set()
    
    return simulation_statuses[session_id]

async def send_log_to_clients(session_id: str, message: str, user_key: Optional[str] = None):
    """Send a log message to all connected WebSocket clients with deduplication and store in log history"""
    if session_id not in connected_websockets:
        return
    
    # Get the status to store logs
    status = get_or_create_status(session_id)
    
    # Deduplicate messages within a short time window
    current_time = time.time()
    
    # Skip identical messages sent within 1 second
    if (message in last_messages[session_id] and 
            current_time - last_message_times[session_id] < 1.0):
        return
    
    # Update tracking
    last_messages[session_id].append(message)
    last_message_times[session_id] = current_time
    
    # Create a log entry
    log_entry = LogEntry(timestamp=current_time, message=message, user_key=user_key)
    
    # Increment total logs counter
    status.total_logs_generated += 1
    
    # Store log if within limits
    if len(status.stored_logs) < status.max_logs:
        status.stored_logs.append(log_entry)
    
    # Send to WebSocket clients
    if connected_websockets[session_id]:
        await asyncio.gather(
            *[websocket.send_text(json.dumps({"type": "log", "message": message, "user_key": user_key})) 
              for websocket in connected_websockets[session_id]]
        )

async def send_status_to_clients(session_id: str):
    """Send current simulation status to all connected WebSocket clients"""
    if session_id not in connected_websockets or not connected_websockets[session_id]:
        return
        
    status = get_or_create_status(session_id)
    status_data = json.dumps({"type": "status", "data": status.model_dump()})
    
    await asyncio.gather(
        *[websocket.send_text(status_data) for websocket in connected_websockets[session_id]]
    )

def update_stats(session_id: str):
    """Update aggregated statistics for a specific session"""
    if session_id not in session_stats:
        return False
    
    status = get_or_create_status(session_id)
    stats = session_stats[session_id]
    
    current_time = time.time()
    
    # Only update if sufficient time has passed since last update
    if current_time - status.stats.last_updated < STATS_UPDATE_INTERVAL:
        return False
    
    # Update control statistics
    # Latency
    control_latency_values = stats["control_latency_values"]
    if control_latency_values:
        status.stats.control.latency.count = len(control_latency_values)
        status.stats.control.latency.sum = sum(control_latency_values)
        status.stats.control.latency.avg = status.stats.control.latency.sum / len(control_latency_values)
    
    # Error rate
    control_error_total = stats["control_error_total"]
    control_error_count = stats["control_error_count"]
    if control_error_total > 0:
        status.stats.control.error_rate.count = control_error_total
        status.stats.control.error_rate.sum = control_error_count
        status.stats.control.error_rate.avg = (control_error_count / control_error_total) * 100 if control_error_total > 0 else 0
    
    # Business metrics
    control_business_total = stats["control_business_total"]
    control_business_count = stats["control_business_count"]
    if control_business_total > 0:
        status.stats.control.business.count = control_business_total
        status.stats.control.business.sum = control_business_count
        status.stats.control.business.avg = (control_business_count / control_business_total) * 100 if control_business_total > 0 else 0
    
    # Update treatment statistics
    # Latency
    treatment_latency_values = stats["treatment_latency_values"]
    if treatment_latency_values:
        status.stats.treatment.latency.count = len(treatment_latency_values)
        status.stats.treatment.latency.sum = sum(treatment_latency_values)
        status.stats.treatment.latency.avg = status.stats.treatment.latency.sum / len(treatment_latency_values)
    
    # Error rate
    treatment_error_total = stats["treatment_error_total"]
    treatment_error_count = stats["treatment_error_count"]
    if treatment_error_total > 0:
        status.stats.treatment.error_rate.count = treatment_error_total
        status.stats.treatment.error_rate.sum = treatment_error_count
        status.stats.treatment.error_rate.avg = (treatment_error_count / treatment_error_total) * 100 if treatment_error_total > 0 else 0
    
    # Business metrics
    treatment_business_total = stats["treatment_business_total"]
    treatment_business_count = stats["treatment_business_count"]
    if treatment_business_total > 0:
        status.stats.treatment.business.count = treatment_business_total
        status.stats.treatment.business.sum = treatment_business_count
        status.stats.treatment.business.avg = (treatment_business_count / treatment_business_total) * 100 if treatment_business_total > 0 else 0
    
    # Update timestamp
    status.stats.last_updated = current_time
    
    return True

async def get_environment_key(session_id: str, config: LDConfig) -> str:
    """Determine the environment key for a given SDK key by making an API call to list environments"""
    try:
        url = f'https://app.launchdarkly.com/api/v2/projects/{config.project_key}/environments'
        headers = {'Authorization': config.api_key, 'Content-Type': 'application/json'}
        
        await send_log_to_clients(session_id, f"Getting environments for project {config.project_key}")
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        
        # Look for environment with matching SDK key
        for env in response_data.get('items', []):
            if env.get('apiKey') == config.sdk_key:
                env_key = env.get('key')
                await send_log_to_clients(session_id, f"Found environment: {env_key}")
                return env_key
        
        # If no match found, fall back to 'production' with a warning
        await send_log_to_clients(session_id, "Warning: Could not find matching environment for SDK key, falling back to 'production'")
        return 'production'
    
    except Exception as e:
        error_msg = f"Error getting environment key: {str(e)} - falling back to 'production'"
        await send_log_to_clients(session_id, error_msg)
        return 'production'

async def init_ld_client(session_id: str, config: LDConfig) -> bool:
    """Initialize the LaunchDarkly client for a specific session"""
    try:
        # Clean up any existing client for this session
        if session_id in active_clients and "client" in active_clients[session_id]:
            active_clients[session_id]["client"].close()
        
        # Initialize client data structure for this session if needed
        if session_id not in active_clients:
            active_clients[session_id] = {}
            
        # ALWAYS fetch the environment key fresh based on the SDK key
        # This ensures we don't use a stale environment_key from a previous SDK key
        config.environment_key = await get_environment_key(session_id, config)
            
        # Initialize new client with optimized event batching
        # Configure batch flushing to handle high throughput efficiently
        ld_config = Config(
            config.sdk_key,
            events_max_pending=10000,  # Buffer up to 10k events before forcing a flush
            flush_interval=1.0  # Auto-flush every 1 second
        )
        ldclient.set_config(ld_config)
        active_clients[session_id]["client"] = ldclient.get()
        active_clients[session_id]["config"] = config
        await send_log_to_clients(session_id, "LaunchDarkly client initialized")
        return True
    except Exception as e:
        error_msg = f"Error initializing LaunchDarkly client: {str(e)}"
        status = get_or_create_status(session_id)
        status.last_error = error_msg
        await send_log_to_clients(session_id, error_msg)
        return False

async def check_guarded_rollout(session_id: str) -> bool:
    """Check if the guarded rollout is active for a specific session"""
    status = get_or_create_status(session_id)
    
    if session_id not in active_clients or "config" not in active_clients[session_id]:
        await send_log_to_clients(session_id, "No configuration found")
        status.guarded_rollout_active = False
        return False
        
    config = active_clients[session_id]["config"]
        
    try:
        url = f'https://app.launchdarkly.com/api/v2/flags/{config.project_key}/{config.flag_key}'
        headers = {'Authorization': config.api_key, 'Content-Type': 'application/json'}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        
        # Get the environment key to use (determined during init based on SDK key)
        env_key = config.environment_key or 'production'
        
        # Safely access nested keys for the appropriate environment
        env_data = response_data.get('environments', {}).get(env_key, {})
        
        if not env_data:
            await send_log_to_clients(session_id, f"No data found for environment '{env_key}'")
            status.guarded_rollout_active = False
            return False
        
        # Function to check if a rollout has a measured/guarded rollout
        def has_measured_rollout(rollout_obj):
            """Check if a rollout object has experimentAllocation.type == 'measuredRollout'"""
            if not rollout_obj or not isinstance(rollout_obj, dict):
                return False
            experiment_allocation = rollout_obj.get('experimentAllocation', {})
            if experiment_allocation and isinstance(experiment_allocation, dict):
                return experiment_allocation.get('type') == 'measuredRollout'
            return False
        
        is_active = False
        
        # Check 1: Look for guarded rollout in fallthrough
        fallthrough = env_data.get('fallthrough', {})
        fallthrough_rollout = fallthrough.get('rollout')
        if fallthrough_rollout and has_measured_rollout(fallthrough_rollout):
            is_active = True
        
        # Check 2: Look for guarded rollout in any targeting rules
        rules = env_data.get('rules', [])
        for rule in rules:
            rule_rollout = rule.get('rollout')
            if rule_rollout and has_measured_rollout(rule_rollout):
                is_active = True
                break
        
        # Check if the rollout status changed from active to inactive
        if status.guarded_rollout_active and not is_active and status.running:
            # The rollout just became inactive, but the simulation is still running
            status.end_time = time.time()
            await send_log_to_clients(session_id, "Guarded rollout became inactive - recording end time")
        
        # Update the status
        status.guarded_rollout_active = is_active
        status_msg = f"Guarded Rollout is active in {env_key}" if is_active else f"Guarded Rollout is not active in {env_key}"
        await send_log_to_clients(session_id, status_msg)
        return is_active
    
    except requests.RequestException as e:
        error_msg = f"API request error: {str(e)}"
        status.last_error = error_msg
        status.guarded_rollout_active = False
        await send_log_to_clients(session_id, error_msg)
        return False
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing API response: {str(e)}"
        status.last_error = error_msg
        status.guarded_rollout_active = False
        await send_log_to_clients(session_id, error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error checking rollout: {str(e)}"
        status.last_error = error_msg
        status.guarded_rollout_active = False
        await send_log_to_clients(session_id, error_msg)
        return False

async def send_events(session_id: str, num_events: int = 1000):
    """Send events to LaunchDarkly for a specific session"""
    status = get_or_create_status(session_id)
    
    if session_id not in active_clients:
        await send_log_to_clients(session_id, "LaunchDarkly client not initialized")
        return
        
    client = active_clients[session_id].get("client")
    config = active_clients[session_id].get("config")
    
    if not client or not config:
        await send_log_to_clients(session_id, "LaunchDarkly client not initialized")
        return
    
    # Get session-specific stats tracking
    stats = session_stats[session_id]
    
    # Convert toggle values to explicitly ensure they're boolean
    latency_enabled = bool(config.latency_metric_enabled)
    error_enabled = bool(config.error_metric_enabled)
    business_enabled = bool(config.business_metric_enabled)
    
    events_sent = 0
    first_event_tracked = False
    
    for i in range(num_events):
        if not status.running:
            break
            
        try:
            context = create_multi_context()
            
            # Extract user key from context
            user_context = context.get_individual_context('user')
            user_key = user_context.key if user_context else 'unknown'
            
            flag_variation_detail = client.variation_detail(config.flag_key, context, False)
            flag_variation = flag_variation_detail.value
            
            # Check if this user is part of an experiment
            in_experiment = False
            reason = flag_variation_detail.reason
            if reason and isinstance(reason, dict) and reason.get('inExperiment') is True:
                in_experiment = True
            
            # Update evaluation counters
            if flag_variation:
                # Treatment group
                status.stats.treatment.evaluations += 1
                if in_experiment:
                    status.stats.treatment.in_experiment += 1
            else:
                # Control group
                status.stats.control.evaluations += 1
                if in_experiment:
                    status.stats.control.in_experiment += 1
                    
            # Flag evaluation log - Include user_key
            variation_str = "treatment" if flag_variation else "control"
            experiment_str = "in experiment" if in_experiment else "not in experiment"
            await send_log_to_clients(session_id, f"Executing {variation_str} ({experiment_str})", user_key)
            
            # Skip further processing if not in experiment (don't log this)
            if not in_experiment:
                continue
            
            # System log - No user_key
            if status.first_event_time is None:
                status.first_event_time = time.time()
                await send_log_to_clients(session_id, f"First event sent at: {time.strftime('%H:%M:%S', time.localtime(status.first_event_time))}")
                first_event_tracked = True
                
            if flag_variation:
                # Treatment (true variation)
                # Error metric tracking - only if enabled
                stats["treatment_error_total"] += 1
                
                if error_enabled and error_chance(config.error_metric_1_true_converted):
                    # Event tracking - Include user_key
                    client.track(config.error_metric_1, context)
                    stats["treatment_error_count"] += 1
                    await send_log_to_clients(session_id, f"Tracking {config.error_metric_1} for treatment", user_key)
                elif not error_enabled:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.error_metric_1} tracking (disabled)")
                
                # Business metric tracking - only if enabled
                stats["treatment_business_total"] += 1
                if business_enabled and error_chance(config.business_metric_1_true_converted):
                    # Event tracking - Include user_key
                    client.track(config.business_metric_1, context)
                    stats["treatment_business_count"] += 1
                    await send_log_to_clients(session_id, f"Tracking {config.business_metric_1} for treatment", user_key)
                elif not business_enabled:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.business_metric_1} tracking (disabled)")
                
                # Latency metric tracking - only if enabled
                if latency_enabled:
                    # Event tracking - Include user_key
                    latency_value = random.randint(config.latency_metric_1_true_range[0], config.latency_metric_1_true_range[1])
                    client.track(config.latency_metric_1, context, metric_value=latency_value)
                    stats["treatment_latency_values"].append(latency_value)
                    await send_log_to_clients(session_id, f"Tracking {config.latency_metric_1} with value {latency_value} for treatment", user_key)
                else:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.latency_metric_1} tracking (disabled)")
            else:
                # Control (false variation)
                # Error metric tracking - only if enabled
                stats["control_error_total"] += 1
                if error_enabled and error_chance(config.error_metric_1_false_converted):
                    # Event tracking - Include user_key
                    client.track(config.error_metric_1, context)
                    stats["control_error_count"] += 1
                    await send_log_to_clients(session_id, f"Tracking {config.error_metric_1} for control", user_key)
                elif not error_enabled:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.error_metric_1} tracking (disabled)")
                
                # Business metric tracking - only if enabled
                stats["control_business_total"] += 1
                if business_enabled and error_chance(config.business_metric_1_false_converted):
                    # Event tracking - Include user_key
                    client.track(config.business_metric_1, context)
                    stats["control_business_count"] += 1
                    await send_log_to_clients(session_id, f"Tracking {config.business_metric_1} for control", user_key)
                elif not business_enabled:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.business_metric_1} tracking (disabled)")
                
                # Latency metric tracking - only if enabled
                if latency_enabled:
                    # Event tracking - Include user_key
                    latency_value = random.randint(config.latency_metric_1_false_range[0], config.latency_metric_1_false_range[1])
                    client.track(config.latency_metric_1, context, metric_value=latency_value)
                    stats["control_latency_values"].append(latency_value)
                    await send_log_to_clients(session_id, f"Tracking {config.latency_metric_1} with value {latency_value} for control", user_key)
                else:
                    # Status log - No user_key
                    await send_log_to_clients(session_id, f"Skipping {config.latency_metric_1} tracking (disabled)")
            
            # SDK handles flushing automatically based on events_max_pending and flush_interval
            events_sent += 1
            status.events_sent += 1
            
            # Update statistics periodically
            if update_stats(session_id):
                await send_status_to_clients(session_id)
            # Update status periodically
            elif events_sent % 10 == 0:
                await send_status_to_clients(session_id)
                
            # Calculate sleep time based on configured evaluations per second
            sleep_time = 1.0 / config.evaluations_per_second
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            error_msg = f"Error during event sending: {str(e)}"
            status.last_error = error_msg
            await send_log_to_clients(session_id, error_msg)
            continue
    
    # Final update before exiting
    update_stats(session_id)
    await send_status_to_clients(session_id)

async def simulation_loop(session_id: str):
    """Main simulation loop for a specific session"""
    status = get_or_create_status(session_id)
    was_active = False
    
    while status.running:
        is_active = await check_guarded_rollout(session_id)
        
        # Check if rollout went from active to inactive
        if was_active and not is_active:
            await send_log_to_clients(session_id, "Guarded rollout became inactive - stopping simulation")
            await stop_simulation(session_id)
            break
            
        # Record current active state for next loop
        was_active = is_active
        
        if is_active:
            await send_events(session_id, 100)  # Send batches of 100 for better control
        else:
            await send_log_to_clients(session_id, "Waiting for guarded rollout to become active...")
            await asyncio.sleep(5)  # Check again in 5 seconds
            await send_status_to_clients(session_id)  # Send updated status with guarded_rollout_active flag

async def start_simulation(session_id: str, config: LDConfig):
    """Start the simulation for a specific session"""
    status = get_or_create_status(session_id)
    
    if status.running:
        await send_log_to_clients(session_id, "Simulation already running")
        return
        
    # Initialize client
    if not await init_ld_client(session_id, config):
        return
    
    # Reset statistics
    session_stats[session_id] = {
        "control_latency_values": [],
        "treatment_latency_values": [],
        "control_error_count": 0,
        "treatment_error_count": 0,
        "control_error_total": 0,
        "treatment_error_total": 0,
        "control_business_count": 0,
        "treatment_business_count": 0,
        "control_business_total": 0,
        "treatment_business_total": 0
    }
    
    # Reset status
    status.running = True
    status.events_sent = 0
    status.last_error = None
    status.guarded_rollout_active = False
    status.first_event_time = None
    status.end_time = None
    
    # Reset stored logs
    status.stored_logs = []
    status.total_logs_generated = 0
    
    # Reset stats properly by creating a new SimulationStats instance
    status.stats = SimulationStats()
    
    # Start simulation in background
    asyncio.create_task(simulation_loop(session_id))
    await send_status_to_clients(session_id)
    await send_log_to_clients(session_id, "Simulation started")

async def stop_simulation(session_id: str):
    """Stop the simulation for a specific session"""
    status = get_or_create_status(session_id)
    
    if not status.running:
        await send_log_to_clients(session_id, "No simulation running")
        return
    
    # Set end time only if not already set by the guarded rollout check
    if not status.end_time:
        status.end_time = time.time()
        await send_log_to_clients(session_id, f"Simulation ended at: {time.strftime('%H:%M:%S', time.localtime(status.end_time))}")
    else:
        await send_log_to_clients(session_id, f"Simulation already ended at: {time.strftime('%H:%M:%S', time.localtime(status.end_time))}")
    
    # Calculate run time if the simulation had events sent
    if status.first_event_time:
        run_time = status.end_time - status.first_event_time
        await send_log_to_clients(session_id, f"Simulation ran for {int(run_time)} seconds since first event")
        
    status.running = False
    await send_status_to_clients(session_id)
    await send_log_to_clients(session_id, "Simulation stopped")
    
    # Clean up
    if session_id in active_clients and "client" in active_clients[session_id]:
        try:
            active_clients[session_id]["client"].flush()
            active_clients[session_id]["client"].close()
        except Exception as e:
            await send_log_to_clients(session_id, f"Error during cleanup: {str(e)}")

def get_simulation_status(session_id: str) -> SimulationStatus:
    """Get current simulation status for a specific session"""
    return get_or_create_status(session_id)

def register_websocket(session_id: str, websocket: Any):
    """Register a websocket connection for a specific session"""
    if session_id not in connected_websockets:
        connected_websockets[session_id] = set()
    connected_websockets[session_id].add(websocket)

def unregister_websocket(session_id: str, websocket: Any):
    """Unregister a websocket connection for a specific session"""
    if session_id in connected_websockets:
        connected_websockets[session_id].discard(websocket)