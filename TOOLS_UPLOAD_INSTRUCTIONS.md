# Upload Tools to LaunchDarkly

## Quick Start

Upload all 20 tools to LaunchDarkly with one command:

```bash
make upload-tools
```

Or run directly:

```bash
./venv/bin/python3 upload_tools_to_launchdarkly.py
```

## Prerequisites

### 1. LaunchDarkly API Key

Add to your `.env` file:

```bash
LAUNCHDARKLY_API_KEY=api-your-key-here
```

**How to get your API key:**
1. Go to LaunchDarkly → Account Settings
2. Click "Authorization" → "Personal API access tokens"
3. Click "Create token"
4. Required scopes: `createAccessToken`, `createProject`, `writeProject`
5. Copy the token

**Alternate variable names (script will check all):**
- `LD_API_KEY`
- `LAUNCHDARKLY_ACCESS_TOKEN`

### 2. Project Key

Add to your `.env` file (optional, defaults to `toggle-health-ai`):

```bash
LAUNCHDARKLY_PROJECT_KEY=your-project-key
```

**How to find your project key:**
1. Go to LaunchDarkly → Project Settings
2. Look for "Project key" under General settings

## What the Script Does

1. ✅ Reads all 20 tools from `launchdarkly_tools_library.json`
2. ✅ Validates API credentials
3. ✅ Uploads each tool to LaunchDarkly via API
4. ✅ If tool exists, updates it instead
5. ✅ Shows progress with color-coded output
6. ✅ Provides detailed summary at the end

## Expected Output

```
================================================================================
🚀 LaunchDarkly AI Tools Uploader
================================================================================

✅ Configuration validated
   API Key: api-123abc...xyz9
   Project Key: toggle-health-ai

✅ Loaded 20 tools from launchdarkly_tools_library.json

📤 Uploading tools to LaunchDarkly...

[1/20] query_snowflake_policy_data           ✅ Created
[2/20] query_aws_rds_coverage                ✅ Created
[3/20] calculate_out_of_pocket_costs         ✅ Created
...
[20/20] apply_brand_guidelines               ✅ Created

================================================================================
📊 Upload Summary
================================================================================

✅ Created: 20 tools
   - query_snowflake_policy_data
   - query_aws_rds_coverage
   ...

================================================================================
✨ Upload complete!
================================================================================
```

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists in project root
- Verify variable name: `LAUNCHDARKLY_API_KEY`
- Check the key starts with `api-`

### "401 Unauthorized"
- API key is invalid or expired
- Regenerate token in LaunchDarkly

### "403 Forbidden"
- API key doesn't have required scopes
- Add `createAccessToken`, `createProject`, `writeProject` scopes

### "409 Conflict - Tool already exists"
- Script automatically attempts to update
- If update fails, check tool schema validity

### "Rate limited"
- Script includes 0.5s delay between requests
- Wait a few minutes and try again

## Manual Verification

After upload, verify in LaunchDarkly:

1. Go to AI Configs → Tool Library
2. You should see 20 tools
3. Click each to verify schema loaded correctly

## Assigning Tools to AI Configs

After upload:

1. Open each AI Config (policy_agent, provider_agent, etc.)
2. Go to "Tools" tab
3. Click "Add tools"
4. Select relevant tools based on `TOOLS_LIBRARY_README.md` mapping
5. Save changes

## API Documentation

This script uses LaunchDarkly's Beta AI Tools API:

- **Endpoint**: `POST /api/v2/projects/{projectKey}/ai-tools`
- **API Version**: `beta` (via `LD-API-Version` header)
- **Authentication**: Bearer token in `Authorization` header

For more details:
https://apidocs.launchdarkly.com/

