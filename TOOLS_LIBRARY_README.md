# LaunchDarkly AI Tools Library

## Overview

This tool library contains **20 robust MCP tools** designed for the ToggleHealth multi-agent system. Each tool is production-ready with complete JSON schemas compatible with LaunchDarkly's AI Config tool library.

## Tool Categories

### 📊 Database & Analytics (5 tools)
- **query_snowflake_policy_data** - Query Snowflake data warehouse for policy information
- **query_aws_rds_coverage** - Real-time coverage data from AWS RDS PostgreSQL
- **query_athena_claims_history** - Claims analytics via AWS Athena/S3
- **search_snowflake_provider_directory** - Comprehensive provider directory search
- **search_medical_knowledge_base** - Internal medical KB and clinical guidelines

### 📅 Calendar & Scheduling (5 tools)
- **check_google_calendar_availability** - Provider availability via Google Calendar MCP
- **book_calendly_appointment** - Appointment booking through Calendly MCP
- **send_twilio_appointment_reminder** - SMS/voice reminders via Twilio
- **get_provider_schedule_details** - Detailed provider schedule and booking rules
- **cancel_or_reschedule_appointment** - Appointment management

### ✅ Verification & Validation (3 tools)
- **verify_prior_authorization** - Authorization requirements and status
- **verify_network_status** - Real-time network participation verification
- **check_accessibility_requirements** - WCAG 2.1 AA accessibility checks

### 💰 Calculation & Analysis (1 tool)
- **calculate_out_of_pocket_costs** - Real-time cost estimation

### 🤖 NLP & AI (4 tools)
- **classify_query_intent_aws_comprehend** - Intent classification and entity extraction
- **assess_urgency_level** - Query urgency assessment
- **translate_text_aws_translate** - Multi-language translation (75+ languages)
- **analyze_sentiment_aws_comprehend** - Sentiment analysis

### 📝 Content & Formatting (2 tools)
- **apply_brand_guidelines** - Brand voice and compliance validation
- **get_provider_ratings_reviews** - Provider ratings and quality metrics

## Agent-Tool Mapping

### Triage Agent (6 tools)
- query_snowflake_policy_data
- search_snowflake_provider_directory
- classify_query_intent_aws_comprehend
- assess_urgency_level
- translate_text_aws_translate
- analyze_sentiment_aws_comprehend
- search_medical_knowledge_base

### Policy Specialist Agent (8 tools)
- query_snowflake_policy_data
- query_aws_rds_coverage
- calculate_out_of_pocket_costs
- query_athena_claims_history
- verify_prior_authorization
- verify_network_status
- search_medical_knowledge_base

### Provider Specialist Agent (7 tools)
- search_snowflake_provider_directory
- check_google_calendar_availability
- get_provider_ratings_reviews
- verify_network_status
- verify_prior_authorization
- get_provider_schedule_details

### Scheduler Specialist Agent (6 tools)
- check_google_calendar_availability
- book_calendly_appointment
- send_twilio_appointment_reminder
- get_provider_schedule_details
- cancel_or_reschedule_appointment

### Brand Voice Agent (5 tools)
- translate_text_aws_translate
- analyze_sentiment_aws_comprehend
- check_accessibility_requirements
- apply_brand_guidelines

## How to Import into LaunchDarkly

### Method 1: Individual Tool Import
1. Go to LaunchDarkly → AI Configs → Tool Library
2. Click "Create tool"
3. Copy the schema from `launchdarkly_tools_library.json` for the desired tool
4. Fill in:
   - **Key**: Tool identifier (e.g., `query_snowflake_policy_data`)
   - **Name**: Human-readable name
   - **Description**: Tool purpose and functionality
   - **Schema**: Paste the JSON schema from `properties` field
5. Click "Save"

### Method 2: Bulk Import (if supported)
1. Use LaunchDarkly's API or CLI to bulk import all tools
2. Reference the `launchdarkly_tools_library.json` file

## Assigning Tools to AI Configs

Once tools are in the tool library:

1. Open your AI Config (e.g., `policy_agent`, `provider_agent`)
2. Navigate to "Tools" section
3. Click "Add tools"
4. Select relevant tools based on the agent mapping above
5. Save changes

## Tool Integration Notes

### MCP (Model Context Protocol) Tools
Tools marked as "MCP" are designed to integrate with external services:
- **Google Calendar MCP** - Requires OAuth setup and calendar API credentials
- **Calendly MCP** - Requires Calendly API token and webhook configuration
- **Twilio** - Requires Twilio account SID and auth token

### AWS Services
AWS tools require:
- IAM role with appropriate permissions
- VPC configuration for RDS access
- S3/Athena setup for claims data lake
- Comprehend and Translate API access

### Database Connections
- **Snowflake**: JDBC connection with service account credentials
- **AWS RDS**: PostgreSQL connection string and security group rules
- **Knowledge Base**: Internal ElasticSearch or vector database

## Example Tool Usage

### Query Snowflake Policy Data
```json
{
  "policy_id": "TH-HMO-GOLD-2024",
  "query_type": "coverage_details",
  "coverage_category": "prescription"
}
```

### Book Calendly Appointment
```json
{
  "event_type_uuid": "abc-123-def-456",
  "start_time": "2024-11-20T14:00:00Z",
  "invitee_email": "patient@example.com",
  "invitee_name": "John Doe",
  "timezone": "America/Los_Angeles"
}
```

### Calculate Out-of-Pocket Costs
```json
{
  "policy_id": "TH-HMO-GOLD-2024",
  "service_code": "99213",
  "estimated_charge": 250.00,
  "in_network": true
}
```

## Testing Tools

Each tool should be tested with:
1. **Valid inputs** - Verify expected responses
2. **Invalid inputs** - Verify error handling
3. **Edge cases** - Empty results, missing data
4. **Performance** - Response time under load

## Monitoring & Observability

Monitor tool usage through:
- LaunchDarkly AI Config monitoring dashboard
- Tool invocation metrics
- Error rates and latency
- Cost tracking (for paid APIs like AWS, Twilio)

## Demo Configuration

For demo purposes:
- Tools can return simulated/stubbed responses
- No actual API calls required for initial testing
- Gradual integration with real services as needed

## Next Steps

1. ✅ Import tools into LaunchDarkly tool library
2. ✅ Assign tools to each AI Config
3. ⬜ Configure MCP server connections
4. ⬜ Set up AWS service integrations
5. ⬜ Test tool invocations in development
6. ⬜ Monitor tool performance and errors
7. ⬜ Iterate based on agent performance

---

**Total Tools**: 20  
**Categories**: 6  
**Agents Covered**: 5  
**Integration Types**: MCP, AWS, Database, REST APIs

