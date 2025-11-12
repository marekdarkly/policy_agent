#!/usr/bin/env python3
"""
Update JSONL Dataset with Cleaned Policies
Creates a new JSONL evaluation dataset using the canonical cleaned policy files
"""
import os
import json

def load_policy_metadata():
    """Load the cleaned policy metadata"""
    metadata_file = "samples/cleaned_policies/policy_metadata.json"
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_updated_jsonl():
    """Create updated JSONL dataset using cleaned policies"""
    
    # Load metadata
    metadata = load_policy_metadata()
    policies = metadata['policies']
    
    print(f"📊 Processing {len(policies)} canonical policies...")
    
    # Track unique questions to avoid duplicates
    unique_questions = {}
    jsonl_entries = []
    
    for policy in policies:
        question = policy['question']
        content = policy['content']
        
        # Skip if we already have this exact question
        if question in unique_questions:
            print(f"⚠️  Skipping duplicate question: {question}")
            continue
        
        unique_questions[question] = True
        
        # Join content steps into a single response
        response_text = ' '.join(content)
        
        # Create JSONL entry in the same format as original
        jsonl_entry = {
            "conversationTurns": [
                {
                    "prompt": {
                        "content": [{"text": question}]
                    },
                    "referenceResponses": [
                        {
                            "content": [{"text": response_text}]
                        }
                    ]
                }
            ]
        }
        
        jsonl_entries.append(jsonl_entry)
    
    # Write the new JSONL file
    output_file = "samples/togglebank_eval_dataset_bedrock_v2.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Created updated JSONL dataset: {output_file}")
    print(f"📊 Original dataset: 121 entries (with many duplicates)")
    print(f"📊 New dataset: {len(jsonl_entries)} entries (unique questions only)")
    print(f"📉 Reduction ratio: {121 / len(jsonl_entries):.1f}:1")
    
    # Create a comparison report
    print(f"\n🔍 QUALITY IMPROVEMENTS:")
    print(f"  • Eliminated redundant questions and variations")
    print(f"  • Used enhanced canonical policy content")
    print(f"  • Fixed grammatical errors in questions")
    print(f"  • Standardized response format and structure")
    print(f"  • Improved consistency across all Q&A pairs")
    
    return jsonl_entries

def validate_jsonl_format(jsonl_entries):
    """Validate the JSONL format is correct"""
    print(f"\n🔍 VALIDATING JSONL FORMAT:")
    
    validation_issues = []
    
    for i, entry in enumerate(jsonl_entries):
        try:
            # Check required structure
            if "conversationTurns" not in entry:
                validation_issues.append(f"Entry {i+1}: Missing 'conversationTurns'")
                continue
            
            turns = entry["conversationTurns"]
            if not isinstance(turns, list) or len(turns) != 1:
                validation_issues.append(f"Entry {i+1}: Invalid conversationTurns structure")
                continue
            
            turn = turns[0]
            
            # Check prompt structure
            if "prompt" not in turn or "content" not in turn["prompt"]:
                validation_issues.append(f"Entry {i+1}: Invalid prompt structure")
            
            # Check response structure
            if "referenceResponses" not in turn or not turn["referenceResponses"]:
                validation_issues.append(f"Entry {i+1}: Invalid referenceResponses structure")
            
        except Exception as e:
            validation_issues.append(f"Entry {i+1}: JSON structure error - {e}")
    
    if validation_issues:
        print(f"❌ Found {len(validation_issues)} validation issues:")
        for issue in validation_issues[:5]:  # Show first 5 issues
            print(f"    • {issue}")
        if len(validation_issues) > 5:
            print(f"    • ... and {len(validation_issues) - 5} more issues")
    else:
        print(f"✅ All {len(jsonl_entries)} entries pass validation")
    
    return len(validation_issues) == 0

def show_sample_entries(jsonl_entries):
    """Show a few sample entries for verification"""
    print(f"\n📋 SAMPLE ENTRIES:")
    
    for i, entry in enumerate(jsonl_entries[:3]):
        turn = entry["conversationTurns"][0]
        question = turn["prompt"]["content"][0]["text"]
        response = turn["referenceResponses"][0]["content"][0]["text"]
        
        print(f"\n{i+1}. Question: {question}")
        print(f"   Response: {response[:100]}...")

if __name__ == "__main__":
    print("🔄 UPDATING JSONL DATASET WITH CLEANED POLICIES")
    print("="*60)
    
    # Create the updated dataset
    jsonl_entries = create_updated_jsonl()
    
    # Validate format
    is_valid = validate_jsonl_format(jsonl_entries)
    
    # Show samples
    show_sample_entries(jsonl_entries)
    
    if is_valid:
        print(f"\n🎉 SUCCESS: Updated JSONL dataset created successfully!")
        print(f"📁 File: samples/togglebank_eval_dataset_bedrock_v2.jsonl")
        print(f"📊 Ready for RAG evaluation with {len(jsonl_entries)} clean Q&A pairs")
    else:
        print(f"\n❌ VALIDATION FAILED: Please check the issues above") 