"""
LaunchDarkly AI Observability Setup

CRITICAL: This module must be imported FIRST before any LLM-related imports.
Import order matters for proper span capture and parent-child relationships.

Order of operations:
1. Initialize LaunchDarkly SDK with ObservabilityPlugin
2. Register framework instrumentations (via ldobserve)
3. Import LLM modules (LangChain, Bedrock, etc.)

Usage:
    from src.utils.observability import initialize_observability
    initialize_observability()  # Call before any LLM imports
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Track if observability has been initialized
_observability_initialized = False


def initialize_observability(
    ld_sdk_key: Optional[str] = None,
    service_name: str = "togglehealth-policy-agent",
    service_version: str = "1.0.0",
    environment: Optional[str] = None
) -> bool:
    """
    Initialize LaunchDarkly AI Observability using ldobserve.
    
    Must be called BEFORE importing any LLM modules.
    
    Args:
        ld_sdk_key: LaunchDarkly SDK key (defaults to LAUNCHDARKLY_SDK_KEY env var)
        service_name: Name of the service for span attribution
        service_version: Version of the service
        environment: Environment name (e.g., 'production', 'development')
        
    Returns:
        True if successfully initialized, False otherwise
    """
    global _observability_initialized
    
    if _observability_initialized:
        logger.info("✅ Observability already initialized")
        return True
    
    try:
        # Get SDK key from env if not provided
        sdk_key = ld_sdk_key or os.getenv("LAUNCHDARKLY_SDK_KEY")
        if not sdk_key:
            logger.warning("⚠️  No LaunchDarkly SDK key found. Observability disabled.")
            return False
        
        # Get environment from env var if not provided
        if environment is None:
            environment = os.getenv("ENVIRONMENT", "development")
        
        logger.info("🔧 Initializing LaunchDarkly AI Observability with ldobserve...")
        
        # Import LaunchDarkly observability components
        try:
            import ldclient
            from ldclient.config import Config
            from ldobserve import ObservabilityConfig, ObservabilityPlugin
            
        except ImportError as e:
            logger.error(f"❌ LaunchDarkly observability packages not installed: {e}")
            logger.error("   Install: pip install launchdarkly-observability")
            return False
        
        # Configure LaunchDarkly with observability plugin
        try:
            config = Config(
                sdk_key,
                plugins=[
                    ObservabilityPlugin(
                        ObservabilityConfig(
                            service_name=service_name,
                            service_version=service_version,
                        )
                    )
                ]
            )
            
            # Initialize LaunchDarkly client
            ldclient.set_config(config)
            
            # Wait for initialization
            import time
            for _ in range(10):
                if ldclient.get().is_initialized():
                    break
                time.sleep(0.1)
            
            if ldclient.get().is_initialized():
                logger.info("✅ LaunchDarkly SDK initialized with observability plugin")
                logger.info(f"   Service: {service_name}")
                logger.info(f"   Version: {service_version}")
                logger.info(f"   Environment: {environment}")
            else:
                logger.warning("⚠️  LaunchDarkly SDK not fully initialized yet")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LaunchDarkly with observability: {e}")
            return False
        
        # Register OpenTelemetry instrumentations
        # The ldobserve package includes instrumentations for LangChain, Bedrock, etc.
        try:
            # LangChain instrumentation
            from opentelemetry.instrumentation.langchain import LangChainInstrumentor
            LangChainInstrumentor().instrument()
            logger.info("✅ LangChain instrumentation registered")
            
        except ImportError:
            logger.info("ℹ️  LangChain instrumentation not available")
        except Exception as e:
            logger.warning(f"⚠️  Failed to instrument LangChain: {e}")
        
        try:
            # Bedrock instrumentation
            from opentelemetry.instrumentation.bedrock import BedrockInstrumentor
            BedrockInstrumentor().instrument()
            logger.info("✅ Bedrock instrumentation registered")
            
        except ImportError:
            logger.info("ℹ️  Bedrock instrumentation not available")
        except Exception as e:
            logger.warning(f"⚠️  Failed to instrument Bedrock: {e}")
        
        # Mark as initialized
        _observability_initialized = True
        
        logger.info("🎉 AI Observability fully initialized!")
        logger.info("   📊 Spans will appear in LaunchDarkly > Monitor > Traces")
        logger.info("   🟢 LLM spans marked with green LLM symbol")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Observability initialization failed: {e}")
        logger.warning("   Continuing without observability...")
        return False


def is_observability_enabled() -> bool:
    """Check if observability has been successfully initialized."""
    return _observability_initialized


# Auto-initialize if this module is imported and SDK key is available
# This ensures observability is set up before any LLM imports
if not _observability_initialized and os.getenv("LAUNCHDARKLY_SDK_KEY"):
    logger.info("🚀 Auto-initializing observability on module import...")
    initialize_observability()
