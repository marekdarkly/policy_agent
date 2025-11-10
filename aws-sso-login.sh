#!/bin/bash
# Quick AWS SSO login for marek profile
# Usage: ./aws-sso-login.sh or bash aws-sso-login.sh

set -e

PROFILE="marek"

echo "🔐 Logging in to AWS SSO with profile: $PROFILE"
echo "This will open your browser for authentication..."
echo ""

aws sso login --profile "$PROFILE"

echo ""
echo "✅ AWS SSO login successful!"
echo ""
echo "🔍 Verifying credentials..."

aws sts get-caller-identity --profile "$PROFILE"

echo ""
echo "✅ Credentials verified!"

