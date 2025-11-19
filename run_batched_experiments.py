#!/usr/bin/env python3
"""
BATCHED EXPERIMENT RUNNER
=========================

This script runs the policy prompt experiment simulator in batches to ensure
reliable metric delivery to LaunchDarkly.

Usage:
    python run_batched_experiments.py --limit 2000

How it works:
    1. Runs batches of 20 exposures at a time
    2. Waits 30 seconds between batches for SDK to transmit events
    3. Continues until reaching the total exposure limit
    4. Each batch flushes and waits to ensure events are sent

Example:
    python run_batched_experiments.py --limit 2000
    -> Runs 100 batches of 20 exposures each (2000 total)
    -> Takes ~50 minutes (100 batches × 30 seconds)
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

BATCH_SIZE = 20                  # Number of exposures per batch
WAIT_BETWEEN_BATCHES = 30        # Seconds to wait between batches
SIMULATOR_SCRIPT = "simulate_policy_prompts.py"  # The main simulator script


# =============================================================================
# BATCH RUNNER
# =============================================================================

def run_batch(batch_number: int, total_batches: int, batch_size: int) -> bool:
    """
    Run a single batch of exposures.
    
    Args:
        batch_number: Current batch number (1-indexed)
        total_batches: Total number of batches to run
        batch_size: Number of exposures in this batch
    
    Returns:
        True if batch succeeded, False otherwise
    """
    print(f"\n{'='*100}")
    print(f"📦 BATCH {batch_number}/{total_batches}")
    print(f"{'='*100}")
    print(f"⏰ Started at: {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"📊 Running {batch_size} exposures...")
    print()
    
    try:
        # Run the simulator with the specified batch size
        result = subprocess.run(
            [sys.executable, SIMULATOR_SCRIPT],
            env={**subprocess.os.environ, "ITERATIONS": str(batch_size)},
            capture_output=False,  # Show output in real-time
            text=True,
            cwd="/Users/marek/Documents/policy_agent"
        )
        
        if result.returncode != 0:
            print(f"\n❌ Batch {batch_number} FAILED with exit code {result.returncode}")
            return False
        
        print(f"\n✅ Batch {batch_number} completed successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Error running batch {batch_number}: {e}")
        return False


def main():
    """
    Main entry point - parses arguments and runs batches.
    """
    # =============================================================================
    # PARSE COMMAND-LINE ARGUMENTS
    # =============================================================================
    
    parser = argparse.ArgumentParser(
        description="Run LaunchDarkly experiment simulator in batches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        required=True,
        help="Total number of exposures to generate (e.g., 2000)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Number of exposures per batch (default: {BATCH_SIZE})"
    )
    
    parser.add_argument(
        "--wait",
        type=int,
        default=WAIT_BETWEEN_BATCHES,
        help=f"Seconds to wait between batches (default: {WAIT_BETWEEN_BATCHES})"
    )
    
    args = parser.parse_args()
    
    # =============================================================================
    # CALCULATE BATCHES
    # =============================================================================
    
    total_exposures = args.limit
    batch_size = args.batch_size
    wait_time = args.wait
    
    # Calculate number of batches needed
    total_batches = (total_exposures + batch_size - 1) // batch_size  # Ceiling division
    
    # Calculate estimated time
    estimated_minutes = (total_batches * wait_time) / 60
    
    # =============================================================================
    # DISPLAY RUN PLAN
    # =============================================================================
    
    print("\n" + "="*100)
    print("🚀 BATCHED EXPERIMENT RUNNER")
    print("="*100)
    print()
    print(f"📊 Configuration:")
    print(f"   Total Exposures:       {total_exposures:,}")
    print(f"   Batch Size:            {batch_size}")
    print(f"   Wait Between Batches:  {wait_time} seconds")
    print()
    print(f"📈 Execution Plan:")
    print(f"   Total Batches:         {total_batches}")
    print(f"   Estimated Duration:    ~{estimated_minutes:.1f} minutes")
    print()
    print(f"⏰ Start Time:            {datetime.now().strftime('%I:%M:%S %p')}")
    print("="*100)
    
    # Ask for confirmation
    try:
        input("\n⏸️  Press ENTER to start, or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    
    # =============================================================================
    # RUN BATCHES
    # =============================================================================
    
    start_time = time.time()
    successful_batches = 0
    failed_batches = 0
    total_exposures_sent = 0
    
    for batch_num in range(1, total_batches + 1):
        # Calculate batch size (might be smaller for last batch)
        remaining_exposures = total_exposures - total_exposures_sent
        current_batch_size = min(batch_size, remaining_exposures)
        
        # Run the batch
        success = run_batch(batch_num, total_batches, current_batch_size)
        
        if success:
            successful_batches += 1
            total_exposures_sent += current_batch_size
        else:
            failed_batches += 1
            print(f"\n⚠️  Warning: Batch {batch_num} failed, but continuing...")
        
        # Wait between batches (except after last batch)
        if batch_num < total_batches:
            print(f"\n⏳ Waiting {wait_time} seconds before next batch...")
            print(f"   Progress: {total_exposures_sent}/{total_exposures} exposures sent ({(total_exposures_sent/total_exposures)*100:.1f}%)")
            time.sleep(wait_time)
    
    # =============================================================================
    # FINAL SUMMARY
    # =============================================================================
    
    duration_minutes = (time.time() - start_time) / 60
    
    print("\n" + "="*100)
    print("🏁 FINAL SUMMARY")
    print("="*100)
    print()
    print(f"✅ Successful Batches:     {successful_batches}/{total_batches}")
    if failed_batches > 0:
        print(f"❌ Failed Batches:         {failed_batches}/{total_batches}")
    print(f"📊 Total Exposures Sent:   {total_exposures_sent:,}")
    print(f"⏱️  Total Duration:         {duration_minutes:.1f} minutes")
    print(f"⏰ Completed at:           {datetime.now().strftime('%I:%M:%S %p')}")
    print()
    print("="*100)
    print()
    print("⚠️  Note: LaunchDarkly may take 3-5 minutes to process all events.")
    print("⚠️  Check your experiment dashboard and refresh if needed.")
    print()
    
    return 0 if failed_batches == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)

