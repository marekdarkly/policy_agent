#!/usr/bin/env python3
import pexpect
import sys

def test_metrics():
    """Test if accuracy/relevance metrics appear in script.py output"""
    
    # Start script.py
    child = pexpect.spawn('python script.py 2>&1', timeout=30, encoding='utf-8')

    try:
        # Wait for ready prompt
        child.expect('You:')
        
        # Send question
        child.sendline('What are the daily ATM withdrawal limits?')
        
        # Wait for feedback prompt
        child.expect('Your answer:')
        
        # Send positive feedback
        child.sendline('y')
        
        # Wait for next prompt
        child.expect('You:')
        
        # Send exit
        child.sendline('exit')
        
        # Wait for completion and capture all output
        try:
            child.expect(pexpect.EOF, timeout=15)
            final_output = child.before
        except:
            final_output = child.before
        
        print('=== SEARCHING FOR ACCURACY/RELEVANCE METRICS ===')
        lines = final_output.split('\n')
        found_metrics = False
        
        for i, line in enumerate(lines):
            if 'accuracy' in line.lower() or 'relevance' in line.lower() or 'metric' in line.lower():
                print(f'Line {i}: {line.strip()}')
                found_metrics = True
        
        if not found_metrics:
            print('❌ No accuracy/relevance metrics found in output')
            print('\n=== FULL OUTPUT (last 50 lines) ===')
            for line in lines[-50:]:
                if line.strip():
                    print(line)
        else:
            print('✅ Found metrics in output')
        
        child.close()
        
    except Exception as e:
        print(f'Error: {e}')
        child.close()

if __name__ == "__main__":
    test_metrics() 