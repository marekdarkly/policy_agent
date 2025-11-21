"""Diagnostic script to test metric events being sent to LaunchDarkly."""

import time
import ldclient
from ldclient import Context

# Initialize observability (which sets up LD client)
from src.utils.observability import initialize_observability

print("🔧 Initializing LaunchDarkly client...")
initialize_observability()

# Wait for client to be ready
client = ldclient.get()
print(f"✅ LaunchDarkly client ready: {client.is_initialized()}")

# Create a test context
ctx = Context.builder('test-user-diagnostic-123').kind('user').set('name', 'Diagnostic Test').build()

print("\n" + "="*80)
print("📤 SENDING TEST METRIC EVENTS")
print("="*80)

# Send hallucinations event
print("\n1️⃣ Sending hallucinations event...")
print(f"   Event name: $ld:ai:hallucinations")
print(f"   Metric value: 0.95")
print(f"   Context: test-user-diagnostic-123")
client.track(
    event_name="$ld:ai:hallucinations",
    context=ctx,
    metric_value=0.95
)
print("   ✅ Sent")

# Send coherence event
print("\n2️⃣ Sending coherence event...")
print(f"   Event name: $ld:ai:coherence")
print(f"   Metric value: 0.90")
print(f"   Context: test-user-diagnostic-123")
client.track(
    event_name="$ld:ai:coherence",
    context=ctx,
    metric_value=0.90
)
print("   ✅ Sent")

# Flush and wait
print("\n🔄 Flushing events to LaunchDarkly...")
client.flush()
time.sleep(3)
print("   ✅ Flushed")

print("\n" + "="*80)
print("📊 VERIFICATION STEPS")
print("="*80)
print("1. Go to LaunchDarkly → Metrics")
print("2. Click 'Explore event' or check Event Debugger")
print("3. Look for events with keys:")
print("   - $ld:ai:hallucinations")
print("   - $ld:ai:coherence")
print("4. Context should be: test-user-diagnostic-123")
print("5. Metric values should be: 0.95 and 0.90")
print("\n✅ Test complete!")

# Close client
client.close()

