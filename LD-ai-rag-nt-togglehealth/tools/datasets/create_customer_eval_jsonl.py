#!/usr/bin/env python3
"""
Create Customer Evaluation JSONL Dataset
Generates realistic customer service questions for RAG evaluation using cleaned customer profiles
"""
import os
import json
import random
from datetime import datetime

def load_customer_metadata():
    """Load the cleaned customer profile metadata"""
    metadata_file = "samples/cleaned_profiles/profile_metadata.json"
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_account_age(account_since):
    """Calculate how long someone has been a customer"""
    try:
        account_date = datetime.strptime(account_since, '%Y-%m-%d')
        current_date = datetime.now()
        years = (current_date - account_date).days / 365.25
        
        if years < 1:
            months = int((current_date - account_date).days / 30.44)
            return f"{months} months"
        else:
            return f"{years:.1f} years"
    except:
        return "unknown duration"

def format_balance_text(balance_range):
    """Convert balance range to readable text"""
    balance_map = {
        '<1k': 'less than $1,000',
        '1k-10k': 'between $1,000 and $10,000',
        '10k-50k': 'between $10,000 and $50,000', 
        '50k-100k': 'between $50,000 and $100,000',
        '>100k': 'more than $100,000'
    }
    return balance_map.get(balance_range, balance_range)

def format_channel_text(channel):
    """Convert channel to readable text"""
    channel_map = {
        'mobile': 'mobile app',
        'web': 'online banking',
        'phone': 'phone support',
        'branch': 'in-person at a branch'
    }
    return channel_map.get(channel, channel)

def format_language_text(lang_code):
    """Convert language code to readable text"""
    lang_map = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese'
    }
    return lang_map.get(lang_code, lang_code)

def generate_customer_questions(customers, num_questions=50):
    """Generate diverse customer service questions"""
    
    question_templates = [
        # Account tier questions
        {
            'template': "What is {name}'s account tier?",
            'response': "{name} has a {tier} tier account.",
            'fields': ['name', 'tier']
        },
        {
            'template': "What tier level does {name} have?", 
            'response': "{name} is a {tier} tier customer.",
            'fields': ['name', 'tier']
        },
        {
            'template': "Can you tell me {name}'s account status?",
            'response': "{name} has {tier} tier status with ToggleBank.",
            'fields': ['name', 'tier']
        },
        
        # Balance questions
        {
            'template': "What is {name}'s account balance range?",
            'response': "{name}'s average account balance is {balance_text}.",
            'fields': ['name', 'balance_text']
        },
        {
            'template': "Can you check {name}'s balance information?",
            'response': "{name} maintains an average balance of {balance_text}.",
            'fields': ['name', 'balance_text']
        },
        
        # Contact preference questions
        {
            'template': "What is {name}'s preferred contact method?",
            'response': "{name} prefers to be contacted through {channel_text}.",
            'fields': ['name', 'channel_text']
        },
        {
            'template': "How does {name} like to be contacted?",
            'response': "{name}'s preferred contact method is {channel_text}.",
            'fields': ['name', 'channel_text']
        },
        {
            'template': "What communication channel does {name} prefer?",
            'response': "{name} prefers using {channel_text} for banking services.",
            'fields': ['name', 'channel_text']
        },
        
        # Language preference questions
        {
            'template': "What language does {name} prefer for communication?",
            'response': "{name} prefers to communicate in {language_text}.",
            'fields': ['name', 'language_text']
        },
        {
            'template': "What is {name}'s language preference?",
            'response': "{name}'s preferred language for banking services is {language_text}.",
            'fields': ['name', 'language_text']
        },
        
        # Account history questions
        {
            'template': "When did {name} open their account?",
            'response': "{name} opened their account on {account_since}.",
            'fields': ['name', 'account_since']
        },
        {
            'template': "How long has {name} been a customer?",
            'response': "{name} has been a ToggleBank customer for {account_age}.",
            'fields': ['name', 'account_age']
        },
        {
            'template': "When did {name} become a customer?",
            'response': "{name} became a ToggleBank customer on {account_since}.",
            'fields': ['name', 'account_since']
        },
        
        # Last login questions
        {
            'template': "When did {name} last access their account?",
            'response': "{name} last logged in on {last_login}.",
            'fields': ['name', 'last_login']
        },
        {
            'template': "What was {name}'s last login date?",
            'response': "{name}'s most recent login was on {last_login}.",
            'fields': ['name', 'last_login']
        },
        
        # Rewards questions
        {
            'template': "How many rewards points does {name} have?",
            'response': "{name} currently has {rewards_points} rewards points.",
            'fields': ['name', 'rewards_points']
        },
        {
            'template': "What is {name}'s rewards balance?",
            'response': "{name} has accumulated {rewards_points} rewards points.",
            'fields': ['name', 'rewards_points']
        },
        {
            'template': "Can you check {name}'s loyalty points?",
            'response': "{name}'s current rewards point balance is {rewards_points}.",
            'fields': ['name', 'rewards_points']
        },
        
        # Location questions
        {
            'template': "What city does {name} live in?",
            'response': "{name} is located in {city}.",
            'fields': ['name', 'city']
        },
        {
            'template': "Where is {name} located?",
            'response': "{name} lives in {city}.",
            'fields': ['name', 'city']
        },
        {
            'template': "What is {name}'s address city?",
            'response': "{name} is based in {city}.",
            'fields': ['name', 'city']
        },
        
        # Comprehensive questions
        {
            'template': "Can you provide {name}'s account summary?",
            'response': "{name} is a {tier} tier customer located in {city}. They opened their account on {account_since} and last logged in on {last_login}. Their average balance is {balance_text} and they have {rewards_points} rewards points. They prefer {channel_text} and communicate in {language_text}.",
            'fields': ['name', 'tier', 'city', 'account_since', 'last_login', 'balance_text', 'rewards_points', 'channel_text', 'language_text']
        }
    ]
    
    questions = []
    used_combinations = set()
    
    # Ensure we get a good distribution of question types
    random.shuffle(customers)
    template_cycles = 0
    
    while len(questions) < num_questions and template_cycles < 10:
        for template in question_templates:
            if len(questions) >= num_questions:
                break
                
            # Pick a random customer
            customer = random.choice(customers)
            
            # Create unique combination key
            combo_key = (template['template'], customer['name'])
            if combo_key in used_combinations:
                continue
                
            used_combinations.add(combo_key)
            
            # Prepare data for template
            template_data = {
                'name': customer['name'],
                'tier': customer['account_tier'],
                'city': customer['city'], 
                'account_since': customer['account_since'],
                'last_login': customer['last_login'],
                'balance_text': format_balance_text(customer['average_balance']),
                'rewards_points': customer['rewards_points'],
                'channel_text': format_channel_text(customer['preferred_channel']),
                'language_text': format_language_text(customer['language_preference']),
                'account_age': calculate_account_age(customer['account_since'])
            }
            
            # Generate question and response
            question_text = template['template'].format(**template_data)
            response_text = template['response'].format(**template_data)
            
            questions.append({
                'question': question_text,
                'response': response_text,
                'customer_id': customer['id'],
                'customer_name': customer['name'],
                'template_type': template['template']
            })
        
        template_cycles += 1
    
    return questions

def create_customer_eval_jsonl():
    """Create customer evaluation JSONL dataset"""
    
    # Load customer data
    metadata = load_customer_metadata()
    customers = metadata['profiles']
    
    print(f"📊 Processing {len(customers)} customer profiles...")
    
    # Generate questions
    questions = generate_customer_questions(customers, num_questions=60)
    
    print(f"📋 Generated {len(questions)} customer service questions")
    
    # Create JSONL entries
    jsonl_entries = []
    
    for q in questions:
        jsonl_entry = {
            "conversationTurns": [
                {
                    "prompt": {
                        "content": [{"text": q['question']}]
                    },
                    "referenceResponses": [
                        {
                            "content": [{"text": q['response']}]
                        }
                    ]
                }
            ]
        }
        jsonl_entries.append(jsonl_entry)
    
    # Write JSONL file
    output_file = "samples/togglebank_customer_eval_dataset.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Created customer evaluation JSONL: {output_file}")
    print(f"📊 Dataset contains {len(jsonl_entries)} customer service Q&A pairs")
    
    # Generate statistics
    print(f"\n📈 DATASET STATISTICS:")
    
    # Question type distribution
    template_counts = {}
    customers_used = set()
    
    for q in questions:
        # Simplify template for counting
        template_key = q['template_type'].split('{')[0].strip()
        template_counts[template_key] = template_counts.get(template_key, 0) + 1
        customers_used.add(q['customer_name'])
    
    print(f"  • Unique customers referenced: {len(customers_used)}")
    print(f"  • Customer coverage: {len(customers_used)}/{len(customers)} ({(len(customers_used)/len(customers))*100:.1f}%)")
    
    print(f"\n📋 QUESTION TYPE DISTRIBUTION:")
    for template_type, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • {template_type}...: {count} questions")
    
    return jsonl_entries, questions

def validate_customer_dataset(jsonl_entries, questions):
    """Validate the customer evaluation dataset"""
    print(f"\n🔍 VALIDATING CUSTOMER DATASET:")
    
    validation_issues = []
    
    # Check JSONL format
    for i, entry in enumerate(jsonl_entries):
        try:
            if "conversationTurns" not in entry:
                validation_issues.append(f"Entry {i+1}: Missing conversationTurns")
                continue
                
            turn = entry["conversationTurns"][0]
            
            if "prompt" not in turn or "referenceResponses" not in turn:
                validation_issues.append(f"Entry {i+1}: Invalid structure")
                
        except Exception as e:
            validation_issues.append(f"Entry {i+1}: {e}")
    
    # Check question quality
    question_texts = [q['question'] for q in questions]
    unique_questions = len(set(question_texts))
    
    print(f"  • Total questions: {len(questions)}")
    print(f"  • Unique questions: {unique_questions}")
    print(f"  • Duplication rate: {((len(questions) - unique_questions) / len(questions)) * 100:.1f}%")
    
    # Check response quality
    avg_response_length = sum(len(q['response']) for q in questions) / len(questions)
    print(f"  • Average response length: {avg_response_length:.0f} characters")
    
    if validation_issues:
        print(f"  ❌ Found {len(validation_issues)} validation issues")
        for issue in validation_issues[:3]:
            print(f"    • {issue}")
    else:
        print(f"  ✅ All entries pass validation")
    
    return len(validation_issues) == 0

def show_sample_questions(questions):
    """Show sample questions for verification"""
    print(f"\n📋 SAMPLE CUSTOMER QUESTIONS:")
    
    # Show variety of question types
    sample_questions = random.sample(questions, min(5, len(questions)))
    
    for i, q in enumerate(sample_questions, 1):
        print(f"\n{i}. Question: {q['question']}")
        print(f"   Response: {q['response']}")
        print(f"   Customer: {q['customer_name']} ({q['customer_id']})")

if __name__ == "__main__":
    print("🔄 CREATING CUSTOMER EVALUATION JSONL DATASET")
    print("="*60)
    
    # Create the dataset
    jsonl_entries, questions = create_customer_eval_jsonl()
    
    # Validate
    is_valid = validate_customer_dataset(jsonl_entries, questions)
    
    # Show samples
    show_sample_questions(questions)
    
    if is_valid:
        print(f"\n🎉 SUCCESS: Customer evaluation dataset created!")
        print(f"📁 File: samples/togglebank_customer_eval_dataset.jsonl")
        print(f"📊 Ready for customer data RAG evaluation")
        print(f"🎯 Use this dataset to test customer information retrieval accuracy")
    else:
        print(f"\n❌ VALIDATION FAILED: Please check issues above") 