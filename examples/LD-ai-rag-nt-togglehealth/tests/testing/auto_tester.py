#!/usr/bin/env python3
"""
Auto Tester for HallucinationTracker Chat Bot
Runs automated sessions with random questions and feedback
"""
import json
import logging
import random
import signal
import sys
import time
import uuid
from pathlib import Path
import pexpect
import re

class HallucinationTrackerAutoTester:
    def __init__(self):
        self.dataset_path = "samples/togglebank_eval_dataset_bedrock.jsonl"
        self.questions = []
        self.session_count = 0
        self.total_questions = 0
        self.positive_feedback_given = 0
        self.target_positive_rate = 0.95  # 95%
        self.session_interval = 5  # seconds (reduced for faster testing)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-7s | %(message)s",
            handlers=[
                logging.FileHandler("auto_tester.log"),
                logging.StreamHandler()
            ]
        )
        
        # Load dataset
        self.load_dataset()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logging.info("\n🛑 Received interrupt signal. Shutting down gracefully...")
        self.show_final_stats()
        sys.exit(0)
        
    def load_dataset(self):
        """Load questions from the evaluation dataset"""
        try:
            with open(self.dataset_path, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    # Handle both simple and bedrock formats
                    if 'conversationTurns' in data:
                        # Bedrock format
                        for turn in data['conversationTurns']:
                            if 'prompt' in turn:
                                content_list = turn['prompt'].get('content', [])
                                for content in content_list:
                                    if 'text' in content:
                                        self.questions.append(content['text'])
                    elif 'humanMessage' in data:
                        # Simple format
                        self.questions.append(data['humanMessage'])
            
            logging.info(f"Loaded {len(self.questions)} questions from dataset")
            
        except FileNotFoundError:
            logging.error(f"Dataset file not found: {self.dataset_path}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Error loading dataset: {e}")
            sys.exit(1)
    
    def get_random_question(self) -> str:
        """Get a random question from the dataset"""
        # Override for specific Rebecca Sato testing
        return "what does Rebecca Sato's account tier mean for her in terms of benefits?"
        # Original: return random.choice(self.questions)
    
    def should_give_positive_feedback(self) -> bool:
        """Determine if positive feedback should be given to maintain ~95% rate"""
        if self.total_questions == 0:
            return True
        
        current_rate = self.positive_feedback_given / self.total_questions
        target_rate = self.target_positive_rate
        
        # Dynamic adjustment to maintain target rate
        adjusted_rate = target_rate + (target_rate - current_rate) * 0.5
        return random.random() < adjusted_rate
    
    def extract_assistant_response(self, output: str) -> str:
        """Extract the assistant response from the chat output"""
        try:
            # Look for the ASSISTANT box in the output
            lines = output.split('\n')
            in_assistant_box = False
            response_lines = []
            
            for line in lines:
                if "ASSISTANT" in line and "│" in line:
                    in_assistant_box = True
                    continue
                elif line.strip().startswith("└") and in_assistant_box:
                    break
                elif in_assistant_box and "│" in line:
                    # Extract text between │ characters
                    content = line.split("│")
                    if len(content) >= 3:
                        text = content[1].strip()
                        if text:
                            response_lines.append(text)
            
            if response_lines:
                response = " ".join(response_lines)
                # Clean up formatting artifacts
                response = re.sub(r'\s+', ' ', response)
                return response[:300] + "..." if len(response) > 300 else response
            
            return "[Could not capture response]"
            
        except Exception as e:
            logging.error(f"Error extracting response: {e}")
            return "[Could not parse response]"
    
    def extract_metrics(self, output: str) -> dict:
        """Extract LaunchDarkly and guardrails metrics from output"""
        metrics = {}
        
        # Extract model information
        model_pattern = r"MLOps model: ([^\s]+)"
        model_match = re.search(model_pattern, output)
        if model_match:
            metrics['model'] = model_match.group(1)
        
        # Extract LaunchDarkly AI tracked metrics  
        ld_pattern = r"LaunchDarkly AI tracked metrics: (.+)"
        ld_match = re.search(ld_pattern, output)
        if ld_match:
            metrics['sdk_metrics'] = ld_match.group(1)
        
        # Extract accuracy metric
        accuracy_pattern = r"Sent accuracy metric to LaunchDarkly: ([\d.]+)%"
        accuracy_match = re.search(accuracy_pattern, output)
        if accuracy_match:
            metrics['accuracy'] = float(accuracy_match.group(1))
        
        # Extract relevance metric
        relevance_pattern = r"Sent relevance metric to LaunchDarkly: ([\d.]+)%"
        relevance_match = re.search(relevance_pattern, output)
        if relevance_match:
            metrics['relevance'] = float(relevance_match.group(1))
        
        # Extract final metrics summary
        metrics_summary_pattern = r"Accuracy: ([\d.]+|None) \| Relevance: ([\d.]+|None)"
        metrics_match = re.search(metrics_summary_pattern, output)
        if metrics_match:
            acc_str = metrics_match.group(1)
            rel_str = metrics_match.group(2)
            if acc_str != "None":
                metrics['accuracy_final'] = float(acc_str)
            if rel_str != "None":
                metrics['relevance_final'] = float(rel_str)
        
        return metrics
    
    def run_chat_session(self) -> bool:
        """
        Run a single chat session with the bot using pexpect
        Returns True if successful, False if error occurred
        """
        try:
            self.session_count += 1
            
            # Start the script with pexpect (capture both stdout and stderr together)
            # Use unbuffered python to ensure real-time output capture
            child = pexpect.spawn('python -u script.py', timeout=60, encoding='utf-8')
            child.logfile_read = sys.stdout  # Optionally log everything to console
            
            # Wait for the ready prompt and capture initial output with model info
            child.expect("You:")
            initial_output = child.before + child.after
            
            # Get a random question
            question = self.get_random_question()
            logging.info(f"Session {self.session_count}: Asking: {question}")
            
            # Send the question
            child.sendline(question)
            
            # Wait for the assistant response and feedback prompt
            child.expect("Your answer:")
            
            # Capture all output so far (includes bot response and should include metrics)
            output_before_feedback = child.before + child.after
            
            # Decide on feedback
            should_give_positive = self.should_give_positive_feedback()
            feedback = "y" if should_give_positive else "n"
            
            # Update stats
            self.total_questions += 1
            if should_give_positive:
                self.positive_feedback_given += 1
            
            current_rate = (self.positive_feedback_given / self.total_questions) * 100
            logging.info(f"Providing {'positive' if should_give_positive else 'negative'} feedback (running rate: {current_rate:.1f}%)")
            
            # Send feedback
            child.sendline(feedback)
            
            # Wait for the next prompt and capture any additional output including metrics
            try:
                child.expect("You:", timeout=30)
                feedback_output = child.before + child.after
            except pexpect.TIMEOUT:
                feedback_output = child.before
            
            # Send exit command 
            child.sendline("exit")
            
            # Wait longer for all final output including metrics logs
            try:
                child.expect(pexpect.EOF, timeout=30)
                final_output = child.before
            except pexpect.TIMEOUT:
                final_output = child.before
                logging.info("✅ Session completed, closing connection")
            
            # Combine all output for comprehensive metrics extraction
            full_output = initial_output + output_before_feedback + feedback_output + final_output
            
            # Extract and log the bot response first
            bot_response = self.extract_assistant_response(output_before_feedback)
            logging.info(f"🤖 Bot Response: {bot_response}")
            
            # Extract metrics from the FULL output (including all stderr logs)
            metrics = self.extract_metrics(full_output)
            
            # Log model information if available
            if 'model' in metrics:
                logging.info(f"🏗️  Model Used: {metrics['model']}")
            
            # Log SDK metrics if available
            if 'sdk_metrics' in metrics:
                logging.info(f"📊 SDK Metrics: {metrics['sdk_metrics']}")
            
            # Log accuracy if available (prefer final summary over intermediate)
            accuracy_val = metrics.get('accuracy_final', metrics.get('accuracy'))
            if accuracy_val is not None:
                logging.info(f"🎯 Accuracy Score: {accuracy_val:.2f}")
            else:
                logging.info("🎯 Accuracy Score: Not captured")
            
            # Log relevance if available (prefer final summary over intermediate)
            relevance_val = metrics.get('relevance_final', metrics.get('relevance'))
            if relevance_val is not None:
                logging.info(f"🔍 Relevance Score: {relevance_val:.2f}")  
            else:
                logging.info("🔍 Relevance Score: Not captured")
            
            # Debug: Save full output to file for inspection
            with open(f"debug_output_session_{self.session_count}.txt", "w") as f:
                f.write("=== FULL CAPTURED OUTPUT ===\n")
                f.write(full_output)
                f.write("\n=== EXTRACTED METRICS ===\n")
                f.write(str(metrics))
            
            # Close the child process
            child.logfile_read = None  # Stop logging to console
            child.close()
            
            logging.info(f"Session {self.session_count} completed successfully")
            logging.info("✅ New user context created for next session")
            
            return True
            
        except pexpect.TIMEOUT:
            logging.info("✅ Session completed, closing connection")
            try:
                child.close(force=True)
            except:
                pass
            return True  # Continue with next session
            
        except pexpect.EOF:
            logging.info("✅ Session completed successfully")
            try:
                child.close()
            except:
                pass
            return True  # Continue with next session
            
        except Exception as e:
            logging.error(f"Error in chat session: {e}")
            try:
                child.close(force=True)
            except:
                pass
            return True  # Continue with next session
    
    def show_final_stats(self):
        """Show final statistics"""
        if self.total_questions > 0:
            final_rate = (self.positive_feedback_given / self.total_questions) * 100
            logging.info("="*60)
            logging.info("📊 FINAL AUTO TESTER STATISTICS")
            logging.info("="*60)
            logging.info(f"Total sessions completed: {self.session_count}")
            logging.info(f"Total questions asked: {self.total_questions}")
            logging.info(f"Positive feedback given: {self.positive_feedback_given}")
            logging.info(f"Final positive rate: {final_rate:.1f}%")
            logging.info(f"Target positive rate: {self.target_positive_rate*100:.1f}%")
            logging.info("="*60)
    
    def run(self):
        """Main execution loop"""
        logging.info(f"🚀 Starting HallucinationTracker Auto Tester")
        logging.info(f"📊 Dataset: {len(self.questions)} questions loaded")
        logging.info(f"😊 Target positive rate: {self.target_positive_rate*100:.0f}%")
        logging.info(f"🔄 Running sessions every {self.session_interval} seconds...")
        logging.info("Press Ctrl+C to stop")
        logging.info("")
        
        try:
            while True:
                logging.info("="*60)
                logging.info(f"Starting session {self.session_count + 1}")
                
                success = self.run_chat_session()
                
                if not success:
                    logging.error("Session failed, stopping auto tester")
                    break
                
                logging.info(f"✅ Session {self.session_count} complete. Waiting {self.session_interval} seconds...")
                time.sleep(self.session_interval)
                
        except KeyboardInterrupt:
            logging.info("\n🛑 Received interrupt signal")
        finally:
            self.show_final_stats()

if __name__ == "__main__":
    tester = HallucinationTrackerAutoTester()
    tester.run() 