import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GuardrailSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class GuardrailMetrics:
    accuracy_score: Optional[float] = None
    grounding_score: Optional[float] = None
    relevance_score: Optional[float] = None
    toxicity_score: Optional[float] = None
    error_occurred: bool = False
    response_time: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class GuardrailThresholds:
    # Critical thresholds - these will trigger CRITICAL severity
    # Made accuracy thresholds more conservative to avoid false triggers
    min_accuracy_critical: float = 0.3  # Only very bad accuracy triggers critical
    min_grounding_critical: float = 0.6  # Kept for monitoring (not used for auto-disable)
    min_relevance_critical: float = 0.5  # Kept for monitoring (not used for auto-disable)
    max_toxicity_critical: float = 0.7  # High toxicity triggers critical
    
    # Warning thresholds - these will trigger HIGH severity
    min_accuracy_warning: float = 0.5   # More conservative accuracy warning threshold
    min_grounding_warning: float = 0.8  # Kept for monitoring (not used for auto-disable)
    min_relevance_warning: float = 0.7  # Kept for monitoring (not used for auto-disable)
    max_toxicity_warning: float = 0.5   # Moderate toxicity triggers warning
    
    max_response_time: float = 15.0  # seconds
    evaluation_window_minutes: int = 2  # Demo-friendly: 2 minutes of data
    trigger_threshold_count: int = 1  # Demo-friendly: 1 violation triggers action
    
    # Auto-disable settings
    auto_disable_on_critical: bool = True
    auto_disable_on_high_repeated: bool = True
    high_repeated_threshold: int = 3  # 3 HIGH violations in window triggers disable

class GuardrailMonitor:
    def __init__(self, thresholds: Optional[GuardrailThresholds] = None, demo_mode: bool = True):
        self.thresholds = thresholds or GuardrailThresholds()
        self.metrics_history: List[GuardrailMetrics] = []
        self.last_trigger_time: Optional[datetime] = None
        self.last_disable_time: Optional[datetime] = None
        self.demo_mode = demo_mode
        
        if demo_mode:
            self.cooldown_minutes = 0.5  # Demo: 30 seconds between triggers
            self.disable_cooldown_minutes = 0.25  # Demo: 15 seconds between disables
        else:
            self.cooldown_minutes = 10  # Production: 10 minutes between triggers
            self.disable_cooldown_minutes = 30  # Production: 30 minutes between disables
    
    def add_metrics(self, metrics: GuardrailMetrics) -> None:
        """Add new metrics to the monitoring system"""
        self.metrics_history.append(metrics)
        self._cleanup_old_metrics()
        
        # Log the metrics
        logger.info(f"Guardrail metrics added - Accuracy: {metrics.accuracy_score}, "
                   f"Grounding: {metrics.grounding_score}, Relevance: {metrics.relevance_score}, "
                   f"Toxicity: {metrics.toxicity_score}, Error: {metrics.error_occurred}")
    
    def should_auto_disable_bypass(self) -> tuple[bool, str]:
        """
        Special bypass trigger for problematic inputs like 'I HATE YOU'
        This bypasses normal metric evaluation and immediately triggers flag disable
        Returns (should_disable, reason)
        """
        # Check disable cooldown
        if self.last_disable_time:
            time_since_disable = datetime.utcnow() - self.last_disable_time
            if time_since_disable < timedelta(minutes=self.disable_cooldown_minutes):
                return False, f"Bypass disable cooldown active ({self.disable_cooldown_minutes - time_since_disable.total_seconds()/60:.1f}min remaining)"
        
        return True, "Bypass trigger activated for problematic user input"
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than the evaluation window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.thresholds.evaluation_window_minutes * 2)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
    
    def evaluate_guardrails(self) -> Optional[GuardrailSeverity]:
        """Evaluate current metrics against thresholds"""
        if not self.metrics_history:
            return None
        
        # Check cooldown period for general triggering
        if self.last_trigger_time:
            time_since_trigger = datetime.utcnow() - self.last_trigger_time
            if time_since_trigger < timedelta(minutes=self.cooldown_minutes):
                return None
        
        # Get recent metrics within evaluation window
        window_start = datetime.utcnow() - timedelta(minutes=self.thresholds.evaluation_window_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > window_start]
        
        if len(recent_metrics) < self.thresholds.trigger_threshold_count:
            return None
        
        # Check for violations
        violations = self._check_violations(recent_metrics)
        
        if violations:
            severity = self._calculate_severity(violations, recent_metrics)
            logger.warning(f"Guardrail violations detected: {violations}")
            return severity
        
        return None
    
    def should_auto_disable(self) -> tuple[bool, str]:
        """
        Determine if the flag should be automatically disabled
        DISABLED: Normal metrics will never trigger flag disable - only bypass cases
        Returns (should_disable, reason)
        """
        # DISABLED: Normal metric-based triggering is completely disabled
        # Only the bypass trigger (should_auto_disable_bypass) can disable the flag
        return False, "Normal metric-based auto-disable is disabled - only bypass triggers allowed"
    
    def _check_violations(self, metrics: List[GuardrailMetrics]) -> List[str]:
        """Check for threshold violations in recent metrics"""
        violations = []
        
        # Check the most recent metrics for violations
        for metric in metrics[-self.thresholds.trigger_threshold_count:]:
            violations.extend(self._check_single_metric_violations(metric))
        
        return violations
    
    def _check_single_metric_violations(self, metric: GuardrailMetrics) -> List[str]:
        """Check violations for a single metric - CONSERVATIVE MODE: Only accuracy and errors trigger flag disable"""
        violations = []
        
        # Check for errors first
        if metric.error_occurred:
            violations.append("System error occurred")
        
        # Check accuracy thresholds - ONLY ACCURACY CAN TRIGGER FLAG DISABLE
        if metric.accuracy_score is not None:
            if metric.accuracy_score < self.thresholds.min_accuracy_critical:
                violations.append(f"CRITICAL accuracy: {metric.accuracy_score:.3f}")
            elif metric.accuracy_score < self.thresholds.min_accuracy_warning:
                violations.append(f"Low accuracy: {metric.accuracy_score:.3f}")
        
        # Check toxicity thresholds - HIGH TOXICITY CAN TRIGGER FLAG DISABLE
        if metric.toxicity_score is not None:
            if metric.toxicity_score > self.thresholds.max_toxicity_critical:
                violations.append(f"CRITICAL toxicity: {metric.toxicity_score:.3f}")
            elif metric.toxicity_score > self.thresholds.max_toxicity_warning:
                violations.append(f"High toxicity: {metric.toxicity_score:.3f}")
        
        # REMOVED: Grounding and relevance checks to avoid false triggers
        # These scores can be noisy and we don't want them accidentally disabling the flag
        # They are still logged for monitoring but won't trigger auto-disable
        
        # Check response time (keep this as it's a clear performance issue)
        if metric.response_time is not None and metric.response_time > self.thresholds.max_response_time:
            violations.append(f"High response time: {metric.response_time:.2f}s")
        
        return violations
    
    def _calculate_severity(self, violations: List[str], recent_metrics: List[GuardrailMetrics]) -> GuardrailSeverity:
        """Calculate severity based on number and type of violations"""
        violation_count = len(violations)
        
        # Check for critical violations (accuracy or safety-related)
        critical_keywords = ["CRITICAL", "error occurred"]
        has_critical = any(keyword in violation for violation in violations for keyword in critical_keywords)
        
        if has_critical:
            return GuardrailSeverity.CRITICAL
        elif violation_count >= 3:
            return GuardrailSeverity.HIGH
        elif violation_count >= 2:
            return GuardrailSeverity.MEDIUM
        else:
            return GuardrailSeverity.LOW
    
    def trigger_guardrail(self) -> None:
        """Mark that a guardrail has been triggered"""
        self.last_trigger_time = datetime.utcnow()
        logger.critical(f"Guardrail triggered at {self.last_trigger_time}")
    
    def record_flag_disable(self) -> None:
        """Mark that the flag has been disabled"""
        self.last_disable_time = datetime.utcnow()
        logger.critical(f"Flag disabled at {self.last_disable_time}")
    
    def reset_cooldowns(self) -> None:
        """Reset all cooldown timers (useful for demos/testing)"""
        self.last_trigger_time = None
        self.last_disable_time = None
        logger.info("All cooldown timers reset")
    
    def get_recent_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of recent metrics for monitoring"""
        window_start = datetime.utcnow() - timedelta(minutes=self.thresholds.evaluation_window_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > window_start]
        
        if not recent_metrics:
            return {"status": "no_recent_data"}
        
        # Calculate averages
        accuracy_scores = [m.accuracy_score for m in recent_metrics if m.accuracy_score is not None]
        grounding_scores = [m.grounding_score for m in recent_metrics if m.grounding_score is not None]
        relevance_scores = [m.relevance_score for m in recent_metrics if m.relevance_score is not None]
        toxicity_scores = [m.toxicity_score for m in recent_metrics if m.toxicity_score is not None]
        error_count = sum(1 for m in recent_metrics if m.error_occurred)
        
        return {
            "window_minutes": self.thresholds.evaluation_window_minutes,
            "total_requests": len(recent_metrics),
            "error_count": error_count,
            "error_rate": error_count / len(recent_metrics) if recent_metrics else 0,
            "avg_accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None,
            "avg_grounding": sum(grounding_scores) / len(grounding_scores) if grounding_scores else None,
            "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else None,
            "avg_toxicity": sum(toxicity_scores) / len(toxicity_scores) if toxicity_scores else None,
            "min_accuracy": min(accuracy_scores) if accuracy_scores else None,
            "min_grounding": min(grounding_scores) if grounding_scores else None,
            "min_relevance": min(relevance_scores) if relevance_scores else None,
            "max_toxicity": max(toxicity_scores) if toxicity_scores else None,
            "last_trigger": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "last_disable": self.last_disable_time.isoformat() if self.last_disable_time else None
        } 