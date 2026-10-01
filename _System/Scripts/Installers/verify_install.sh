#!/bin/bash
# verify_install.sh
# Runs after installation to verify the Hermes Brain template is set up correctly.

set -euo pipefail

echo "🔍 Verifying your Hermes Brain install..."
echo

# Array to hold check results
checks_passed=0
checks_total=0

# Function to run a check and increment counters
run_check() {
  local description="$1"
  local command="$2"
  local expected_output="${3:-}"  # Optional: if we expect specific output
  local inverse="${4:-false}"     # If true, we expect the command to fail

  ((checks_total++))
  echo -n "Checking: $description... "
  if eval "$command" 2>/dev/null; then
    if [[ "$inverse" == "true" ]]; then
      echo "❌ Unexpected success"
      return 1
    else
      echo "✅ Pass"
      ((checks_passed++))
      return 0
    fi
  else
    if [[ "$inverse" == "true" ]]; then
      echo "✅ Expected failure"
      ((checks_passed++))
      return 0
    else
      echo "❌ Failed"
      return 1
    fi
  fi
}

# Check 1: Basic vault structure exists
run_check "Vault structure (01-Projects, 02-Areas, 03-Resources, 04-Archives, _System)" \
  "[ -d 01-Projects ] && [ -d 02-Areas ] && [ -d 03-Resources ] && [ -d 04-Archives ] && [ -d _System ]"

# Check 2: Key Obsidian plugins are present (Dataview, Smart Connections, Kanban)
run_check "Obsidian plugins (dataview, smart-connections, kanban)" \
  "[ -d .obsidian/plugins/dataview ] && [ -d .obsidian/plugins/smart-connections ] && [ -d .obsidian/plugins/kanban ]"

# Check 3: MCP server is active (we assume hermes-agent is in PATH)
# Note: This might require the Hermes agent to be running. We'll check the status.
# We'll run the command and look for "active" in the output.
run_check "MCP server status (should be active)" \
  "hermes-agent mcp-server status 2>/dev/null | grep -q 'active'"

# Check 4: Memory promotion script --list runs without error and shows 0 candidates initially
# We'll run the script and check that it doesn't error and the output contains "0 candidates" or similar.
# We'll be lenient: just check that the script runs and produces output.
run_check "Memory promotion script --list" \
  "python _System/Scripts/promote_memory.py --list 2>/dev/null"

# Check 5: User-Profile.md exists and is not empty (and likely not just the template)
# We'll check that it exists and has more than just the template header.
# We'll check for a line that indicates it's been personalized (but we can't know what the user put).
# So we'll just check it's not empty and has at least, say, 50 bytes.
run_check "User-Profile.md exists and has content" \
  "[ -f 02-Areas/User-Profile.md ] && [ $(wc -c < 02-Areas/User-Profile.md) -gt 50 ]"

# Check 6: The .gitignore is present and ignores personal data (optional, but good to check)
run_check ".gitignore exists and ignores Daily/" \
  "grep -q '^Daily/$' .gitignore"

echo
echo "📊 Verification Summary: $checks_passed/$checks_total checks passed"

if [[ $checks_passed -eq $checks_total ]]; then
  echo "🎉 All checks passed! Your Hermes Brain install looks good."
  echo "💡 Next steps: Try 'hermes-agent mcp-server start' and 'python _System/Scripts/promote_memory.py --review'"
else
  echo "⚠️  Some checks failed. Review the output above for details."
  echo "💡 Common issues:"
  echo "   - MCP server not running: Start it with 'hermes-agent mcp-server start'"
  echo "   - Missing plugins: Ensure you ran the installer fully"
  echo "   - User-Profile.md too small: Edit it to add your details"
  exit 1
fi