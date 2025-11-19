from pydantic import BaseModel, validator, field_validator
from typing import List, Optional, Union, Dict, Any
import json
import time

class LogEntry(BaseModel):
    """A single log entry with timestamp and message"""
    timestamp: float  # Unix timestamp
    message: str
    user_key: Optional[str] = None  # Added field for user key from context
    
    def to_dict(self):
        result = {
            "timestamp": self.timestamp,
            "formatted_time": time.strftime('%H:%M:%S', time.localtime(self.timestamp)),
            "message": self.message,
        }
        
        # Only include user_key if it has a value
        if self.user_key is not None:
            result["user_key"] = self.user_key
            
        return result

class MetricStats(BaseModel):
    count: int = 0
    sum: int = 0
    avg: float = 0.0

class VariationStats(BaseModel):
    error_rate: MetricStats = MetricStats()
    latency: MetricStats = MetricStats()
    business: MetricStats = MetricStats()
    evaluations: int = 0  # Total flag evaluations
    in_experiment: int = 0  # Flag evaluations that were in experiment

class SimulationStats(BaseModel):
    control: VariationStats = VariationStats()
    treatment: VariationStats = VariationStats()
    last_updated: float = 0.0
    last_updated_flag_evaluations: int = 0  # Timestamp of last flag evaluation update
    last_updated_flag_evaluations_in_experiment: int = 0  # Flag evaluations in experiment at last update

class LDConfig(BaseModel):
    sdk_key: str
    api_key: str
    project_key: str
    flag_key: str
    environment_key: Optional[str] = None  # Added field to store env key associated with SDK key
    latency_metric_1: str
    error_metric_1: str
    business_metric_1: str
    latency_metric_1_false_range: List[int]
    latency_metric_1_true_range: List[int]
    error_metric_1_false_converted: int
    error_metric_1_true_converted: int
    business_metric_1_false_converted: int
    business_metric_1_true_converted: int
    error_metric_enabled: bool = True
    latency_metric_enabled: bool = True
    business_metric_enabled: bool = True
    evaluations_per_second: float = 20.0  # Rate of flag evaluations (default: 20/sec)
    session_id: str  # Add session ID to track simulations per client
    
    @field_validator('latency_metric_1_false_range', 'latency_metric_1_true_range')
    def validate_range(cls, v):
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError('Range must be a list of two integers with first value <= second value')
        return v
        
    @field_validator('error_metric_1_false_converted', 'error_metric_1_true_converted', 'business_metric_1_false_converted', 'business_metric_1_true_converted')
    def validate_percentage(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Conversion rate must be between 0 and 100')
        return v
        
    @field_validator('error_metric_enabled', 'latency_metric_enabled', 'business_metric_enabled')
    def validate_toggle(cls, v):
        # Ensure toggle values are strictly boolean
        if v is True or v == 'true' or v == 1:
            return True
        return False
    
    @field_validator('evaluations_per_second')
    def validate_evaluations_rate(cls, v):
        # Enforce min/max bounds for evaluation rate
        if v < 0.1 or v > 100:
            raise ValueError('Evaluations per second must be between 0.1 and 100')
        return v

class SimulationStatus(BaseModel):
    session_id: str  # Add session ID to identify unique client sessions
    running: bool
    events_sent: int = 0
    last_error: Optional[str] = None
    stats: SimulationStats = SimulationStats()
    guarded_rollout_active: bool = False
    first_event_time: Optional[float] = None  # Timestamp when first event was sent
    end_time: Optional[float] = None  # Timestamp when simulation stopped
    stored_logs: List[LogEntry] = []  # Store logs for post-simulation review
    max_logs: int = 50000  # Maximum number of logs to store (50,000 by default)
    total_logs_generated: int = 0  # Count of all logs, even if not all are stored

class SessionRequest(BaseModel):
    session_id: str

class LogsResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total_count: int
    has_more: bool
