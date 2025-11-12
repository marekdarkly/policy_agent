"""
LaunchDarkly AI Observability Setup with OpenLLMetry

CRITICAL: This module must be imported FIRST before any LLM-related imports.
Import order matters for proper span capture and parent-child relationships.

Order of operations:
1. Initialize Traceloop SDK (OpenLLMetry) with LaunchDarkly config
2. Register framework instrumentations (LangChain, etc.)
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
    environment: Optional[str] = None
) -> bool:
    """
    Initialize LaunchDarkly AI Observability with OpenLLMetry.
    
    Must be called BEFORE importing any LLM modules.
    
    Args:
        ld_sdk_key: LaunchDarkly SDK key (defaults to LAUNCHDARKLY_SDK_KEY env var)
        service_name: Name of the service for span attribution
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
        
        logger.info("🔧 Initializing LaunchDarkly AI Observability with OpenLLMetry...")
        
        # Initialize Traceloop SDK (OpenLLMetry)
        # This automatically sets up OpenTelemetry and instruments supported frameworks
        try:
            from traceloop.sdk import Traceloop
            
            # Check if LaunchDarkly observability endpoint is configured
            ld_obs_endpoint = os.getenv("LD_OBSERVABILITY_ENDPOINT")
            
            if ld_obs_endpoint:
                # Export to LaunchDarkly observability
                logger.info(f"   Exporting spans to: {ld_obs_endpoint}")
                Traceloop.init(
                    app_name=service_name,
                    api_endpoint=ld_obs_endpoint,
                    headers={
                        "Authorization": sdk_key,
                        "LD-Application-ID": os.getenv("LD_APPLICATION_ID", service_name)
                    },
                    disable_batch=False,
                    resource_attributes={
                        "service.name": service_name,
                        "deployment.environment": environment,
                    }
                )
            else:
                # Local-only instrumentation (no export)
                logger.warning("⚠️  LD_OBSERVABILITY_ENDPOINT not set. Spans will be instrumented but NOT exported.")
                logger.warning("   To export to LaunchDarkly, set LD_OBSERVABILITY_ENDPOINT in .env")
                Traceloop.init(
                    app_name=service_name,
                    disable_batch=True,  # Don't try to export
                    resource_attributes={
                        "service.name": service_name,
                        "deployment.environment": environment,
                    }
                )
            
            logger.info("✅ Traceloop SDK (OpenLLMetry) initialized")
            logger.info(f"   Service: {service_name}")
            logger.info(f"   Environment: {environment}")
            
        except ImportError:
            logger.error("❌ Traceloop SDK not installed")
            logger.error("   Install: pip install traceloop-sdk")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Traceloop SDK: {e}")
            logger.warning(f"   Continuing without observability...")
            return False
        
        # Register OpenTelemetry instrumentations for frameworks
        # These must be registered AFTER Traceloop.init() but BEFORE importing frameworks
        
        # LangChain instrumentation (if available)
        try:
            from opentelemetry.instrumentation.langchain import LangChainInstrumentor
            
            LangChainInstrumentor().instrument()
            logger.info("✅ LangChain instrumentation registered")
            
        except ImportError:
            logger.info("ℹ️  LangChain instrumentation not available (install: pip install opentelemetry-instrumentation-langchain)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to instrument LangChain: {e}")
        
        # AWS Bedrock instrumentation (if available)
        try:
            from opentelemetry.instrumentation.bedrock import BedrockInstrumentor
            
            BedrockInstrumentor().instrument()
            logger.info("✅ Bedrock instrumentation registered")
            
        except ImportError:
            logger.info("ℹ️  Bedrock instrumentation not available (install: pip install opentelemetry-instrumentation-bedrock)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to instrument Bedrock: {e}")
        
        # Mark as initialized
        _observability_initialized = True
        
        logger.info("🎉 AI Observability fully initialized!")
        logger.info("   📊 Spans will appear in LaunchDarkly > Monitor > Traces")
        logger.info("   🔍 LLM spans marked with green LLM symbol")
        
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
