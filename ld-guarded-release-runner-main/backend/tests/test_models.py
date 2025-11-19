import pytest
from pydantic import ValidationError
from app.models import LDConfig, SimulationStatus

def test_ld_config_valid():
    """Test that a valid LDConfig is accepted"""
    config = LDConfig(
        sdk_key="sdk-test",
        api_key="api-test",
        project_key="project-test",
        flag_key="flag-test",
        numeric_metric_1="latency",
        binary_metric_1="error-rate",
        numeric_metric_1_false_range=[50, 100],
        numeric_metric_1_true_range=[100, 200],
        binary_metric_1_false_converted=5,
        binary_metric_1_true_converted=15
    )
    
    assert config.sdk_key == "sdk-test"
    assert config.numeric_metric_1_false_range == [50, 100]

def test_ld_config_invalid_range():
    """Test that invalid ranges are rejected"""
    with pytest.raises(ValidationError):
        LDConfig(
            sdk_key="sdk-test",
            api_key="api-test",
            project_key="project-test",
            flag_key="flag-test",
            numeric_metric_1="latency",
            binary_metric_1="error-rate",
            numeric_metric_1_false_range=[100, 50],  # Invalid: first > second
            numeric_metric_1_true_range=[100, 200],
            binary_metric_1_false_converted=5,
            binary_metric_1_true_converted=15
        )

def test_ld_config_invalid_percentage():
    """Test that invalid percentages are rejected"""
    with pytest.raises(ValidationError):
        LDConfig(
            sdk_key="sdk-test",
            api_key="api-test",
            project_key="project-test",
            flag_key="flag-test",
            numeric_metric_1="latency",
            binary_metric_1="error-rate",
            numeric_metric_1_false_range=[50, 100],
            numeric_metric_1_true_range=[100, 200],
            binary_metric_1_false_converted=5,
            binary_metric_1_true_converted=150  # Invalid: > 100
        )

def test_simulation_status():
    """Test simulation status model"""
    status = SimulationStatus(running=False)
    
    assert status.running is False
    assert status.events_sent == 0
    assert status.last_error is None
    
    status.running = True
    status.events_sent = 100
    status.last_error = "Test error"
    
    assert status.running is True
    assert status.events_sent == 100
    assert status.last_error == "Test error"
