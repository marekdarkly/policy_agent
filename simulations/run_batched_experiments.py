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
    5. Logs detailed execution info to experiment_logs/ directory

Example:
    python run_batched_experiments.py --limit 2000
    -> Runs 100 batches of 20 exposures each (2000 total)
    -> Takes ~50 minutes (100 batches × 30 seconds)
    -> Creates log file: experiment_logs/batch_run_2000exposures_YYYYMMDD_HHMMSS.log

Log Files:
    - Console: Shows INFO level messages (progress, summaries)
    - File: Captures DEBUG level (detailed execution, stdout/stderr from batches)
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

BATCH_SIZE = 20                  # Number of exposures per batch
WAIT_BETWEEN_BATCHES = 30        # Seconds to wait between batches
SIMULATOR_SCRIPT = "simulate_policy_prompts.py"  # The main simulator script
LOG_DIR = Path("experiment_logs")  # Directory for log files


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(log_filename: str) -> logging.Logger:
    """
    Set up logging to both console and file with detailed formatting.
    
    Args:
        log_filename: Name of the log file
    
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)
    
    log_path = LOG_DIR / log_filename
    
    # Create logger
    logger = logging.getLogger('BatchRunner')
    logger.setLevel(logging.DEBUG)
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - summary logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_path


# =============================================================================
# BATCH RUNNER
# =============================================================================

def run_batch(batch_number: int, total_batches: int, batch_size: int, logger: logging.Logger) -> bool:
    """
    Run a single batch of exposures.
    
    Args:
        batch_number: Current batch number (1-indexed)
        total_batches: Total number of batches to run
        batch_size: Number of exposures in this batch
        logger: Logger instance for logging
    
    Returns:
        True if batch succeeded, False otherwise
    """
    batch_start = datetime.now()
    
    logger.info(f"\n{'='*100}")
    logger.info(f"📦 BATCH {batch_number}/{total_batches}")
    logger.info(f"{'='*100}")
    logger.info(f"⏰ Started at: {batch_start.strftime('%I:%M:%S %p')}")
    logger.info(f"📊 Running {batch_size} exposures...")
    logger.debug(f"Batch {batch_number} - Command: {sys.executable} {SIMULATOR_SCRIPT}")
    logger.debug(f"Batch {batch_number} - Environment: ITERATIONS={batch_size}")
    logger.info("")
    
    try:
        # Run the simulator with the specified batch size
        result = subprocess.run(
            [sys.executable, SIMULATOR_SCRIPT],
            env={**subprocess.os.environ, "ITERATIONS": str(batch_size)},
            capture_output=True,  # Capture for logging
            text=True,
            cwd="/Users/marek/Documents/policy_agent"
        )
        
        batch_end = datetime.now()
        batch_duration = (batch_end - batch_start).total_seconds()
        
        # Log subprocess output
        if result.stdout:
            logger.debug(f"Batch {batch_number} - STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"Batch {batch_number} - STDERR:\n{result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Batch {batch_number} FAILED with exit code {result.returncode}")
            logger.error(f"Batch {batch_number} - Duration: {batch_duration:.1f}s")
            return False
        
        logger.info(f"\n✅ Batch {batch_number} completed successfully")
        logger.debug(f"Batch {batch_number} - Duration: {batch_duration:.1f}s")
        logger.debug(f"Batch {batch_number} - Return code: {result.returncode}")
        return True
        
    except Exception as e:
        logger.error(f"Error running batch {batch_number}: {e}", exc_info=True)
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
    # SETUP LOGGING
    # =============================================================================
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"batch_run_{args.limit}exposures_{timestamp}.log"
    
    logger, log_path = setup_logging(log_filename)
    
    logger.info("="*100)
    logger.info("BATCHED EXPERIMENT RUNNER - LOG INITIALIZED")
    logger.info("="*100)
    logger.info(f"Log file: {log_path}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("")
    
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
    
    logger.debug(f"Arguments parsed: limit={total_exposures}, batch_size={batch_size}, wait={wait_time}")
    logger.debug(f"Calculated: total_batches={total_batches}, estimated_minutes={estimated_minutes:.1f}")
    
    # =============================================================================
    # DISPLAY RUN PLAN
    # =============================================================================
    
    logger.info("\n" + "="*100)
    logger.info("🚀 BATCHED EXPERIMENT RUNNER")
    logger.info("="*100)
    logger.info("")
    logger.info(f"📊 Configuration:")
    logger.info(f"   Total Exposures:       {total_exposures:,}")
    logger.info(f"   Batch Size:            {batch_size}")
    logger.info(f"   Wait Between Batches:  {wait_time} seconds")
    logger.info("")
    logger.info(f"📈 Execution Plan:")
    logger.info(f"   Total Batches:         {total_batches}")
    logger.info(f"   Estimated Duration:    ~{estimated_minutes:.1f} minutes")
    logger.info("")
    logger.info(f"⏰ Start Time:            {datetime.now().strftime('%I:%M:%S %p')}")
    logger.info(f"📋 Log File:              {log_path}")
    logger.info("="*100)
    
    # Ask for confirmation
    try:
        input("\n⏸️  Press ENTER to start, or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        logger.warning("\n\nCancelled by user")
        return 1
    
    # =============================================================================
    # RUN BATCHES
    # =============================================================================
    
    logger.info("\n" + "="*100)
    logger.info("STARTING BATCH EXECUTION")
    logger.info("="*100)
    logger.debug(f"Total batches to run: {total_batches}")
    
    start_time = time.time()
    successful_batches = 0
    failed_batches = 0
    total_exposures_sent = 0
    
    for batch_num in range(1, total_batches + 1):
        # Calculate batch size (might be smaller for last batch)
        remaining_exposures = total_exposures - total_exposures_sent
        current_batch_size = min(batch_size, remaining_exposures)
        
        logger.debug(f"Batch {batch_num}/{total_batches} - Size: {current_batch_size}, Remaining: {remaining_exposures}")
        
        # Run the batch
        success = run_batch(batch_num, total_batches, current_batch_size, logger)
        
        if success:
            successful_batches += 1
            total_exposures_sent += current_batch_size
            logger.debug(f"Batch {batch_num} succeeded - Total sent so far: {total_exposures_sent}")
        else:
            failed_batches += 1
            logger.warning(f"Batch {batch_num} failed, but continuing...")
        
        # Wait between batches (except after last batch)
        if batch_num < total_batches:
            progress_pct = (total_exposures_sent/total_exposures)*100
            logger.info(f"\n⏳ Waiting {wait_time} seconds before next batch...")
            logger.info(f"   Progress: {total_exposures_sent}/{total_exposures} exposures sent ({progress_pct:.1f}%)")
            logger.debug(f"Sleep for {wait_time}s starting at {datetime.now().strftime('%I:%M:%S %p')}")
            time.sleep(wait_time)
            logger.debug(f"Sleep completed at {datetime.now().strftime('%I:%M:%S %p')}")
    
    # =============================================================================
    # FINAL SUMMARY
    # =============================================================================
    
    duration_minutes = (time.time() - start_time) / 60
    end_time = datetime.now()
    
    logger.info("\n" + "="*100)
    logger.info("🏁 FINAL SUMMARY")
    logger.info("="*100)
    logger.info("")
    logger.info(f"✅ Successful Batches:     {successful_batches}/{total_batches}")
    if failed_batches > 0:
        logger.warning(f"❌ Failed Batches:         {failed_batches}/{total_batches}")
    logger.info(f"📊 Total Exposures Sent:   {total_exposures_sent:,}")
    logger.info(f"⏱️  Total Duration:         {duration_minutes:.1f} minutes")
    logger.info(f"⏰ Completed at:           {end_time.strftime('%I:%M:%S %p')}")
    logger.info("")
    logger.info("="*100)
    logger.info("")
    logger.info("⚠️  Note: LaunchDarkly may take 3-5 minutes to process all events.")
    logger.info("⚠️  Check your experiment dashboard and refresh if needed.")
    logger.info(f"📋 Full logs available at: {log_path}")
    logger.info("")
    
    logger.debug(f"Execution completed with exit code: {0 if failed_batches == 0 else 1}")
    
    return 0 if failed_batches == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)

