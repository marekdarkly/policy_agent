#!/usr/bin/env python3
import subprocess
import sys

def test_bot_capture():
    """Simple test to capture bot response"""
    print("Testing bot response capture...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "script.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send a simple question
        input_sequence = "How can I dispute an unauthorized transaction?\ny\nexit\n"
        print(f"Sending: {repr(input_sequence)}")
        
        # Get output
        stdout, stderr = process.communicate(input=input_sequence, timeout=90)
        
        print(f"Return code: {process.returncode}")
        print(f"STDERR: {stderr[:500]}...")
        print(f"STDOUT length: {len(stdout)}")
        print("=" * 50)
        print("STDOUT:")
        print(stdout)
        print("=" * 50)
        
        # Try to extract the assistant response
        lines = stdout.split('\n')
        in_assistant_box = False
        assistant_response = []
        
        for i, line in enumerate(lines):
            if "ASSISTANT" in line and "│" in line:
                print(f"Found ASSISTANT box at line {i}: {line}")
                in_assistant_box = True
                continue
            elif line.strip().startswith("└") and in_assistant_box:
                print(f"End of box at line {i}: {line}")
                break
            elif in_assistant_box and line.startswith("│"):
                clean_line = line[2:].rstrip() if len(line) > 2 else ""
                if clean_line:
                    assistant_response.append(clean_line)
                    print(f"  Line {i}: '{clean_line}'")
        
        if assistant_response:
            response_text = " ".join(assistant_response).strip()
            print(f"\n🤖 EXTRACTED RESPONSE: {response_text}")
        else:
            print("\n❌ Could not extract assistant response")
        
    except subprocess.TimeoutExpired:
        print("❌ Process timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_bot_capture() 