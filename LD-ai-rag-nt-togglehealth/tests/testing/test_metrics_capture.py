#!/usr/bin/env python3
import subprocess
import sys
import time

def test_metrics_capture():
    """Test capturing metrics from script.py"""
    print("Testing metrics capture...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "script.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send a simple question and positive feedback
        input_sequence = "What are the daily ATM withdrawal limits?\ny\nexit\n"
        print(f"Sending: {repr(input_sequence)}")
        
        # Get output with timeout
        try:
            stdout, stderr = process.communicate(input=input_sequence, timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        
        print(f"Return code: {process.returncode}")
        
        print("\n=== STDOUT (first 500 chars) ===")
        print(stdout[:500])
        
        print("\n=== STDERR (full output) ===")
        print(stderr)
        
        # Parse metrics from stderr
        if stderr:
            lines = stderr.split('\n')
            print("\n=== EXTRACTED METRICS ===")
            for line in lines:
                if "LaunchDarkly AI tracked metrics:" in line:
                    print(f"📊 SDK Metrics: {line.split('LaunchDarkly AI tracked metrics: ')[1]}")
                elif "Sent accuracy metric to LaunchDarkly:" in line:
                    accuracy = line.split('Sent accuracy metric to LaunchDarkly: ')[1]
                    print(f"🎯 Accuracy: {accuracy}")
                elif "Sent relevance metric to LaunchDarkly:" in line:
                    relevance = line.split('Sent relevance metric to LaunchDarkly: ')[1]
                    print(f"🔍 Relevance: {relevance}")
        else:
            print("No stderr output captured!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_metrics_capture() 