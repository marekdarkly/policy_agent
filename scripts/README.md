# Scripts

This directory contains utility scripts for setup, configuration, and LaunchDarkly integration.

## Scripts

### `upload_tools_to_launchdarkly.py`
Uploads the tool library to LaunchDarkly via the AI Tools API.

**Usage:**
```bash
make upload-tools

# or directly
python scripts/upload_tools_to_launchdarkly.py
```

**Requirements:**
- `LAUNCHDARKLY_API_KEY` in `.env`
- `LAUNCHDARKLY_PROJECT_KEY` in `.env`

**Tool Library:** `launchdarkly_tools_library.json`
- Contains 20 robust MCP tools across various categories
- Includes tools for Snowflake queries, calendar integration, AWS Comprehend, etc.
- Ready-to-use JSON schemas for LaunchDarkly AI Configs

## Tool Library

The `launchdarkly_tools_library.json` file contains pre-built tool definitions organized by category:

- **Data & Analytics**: Snowflake queries, data analysis
- **Scheduling & Calendar**: Google Calendar integration
- **NLP & AI**: AWS Comprehend, sentiment analysis
- **Healthcare**: Medical terminology lookup, drug interactions
- **Communication**: Email, notifications
- **File & Document**: PDF parsing, document search

## Adding New Tools

1. Add tool definition to `launchdarkly_tools_library.json`
2. Run `make upload-tools`
3. Tools will be created or updated in LaunchDarkly

The script handles both POST (new tools) and PATCH (existing tools) automatically.

