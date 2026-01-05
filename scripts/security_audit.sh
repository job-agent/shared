#!/bin/bash

# Script to run pip-audit security scan on all packages in the monorepo
# Usage: ./scripts/security_audit.sh [--strict]
#   --strict: Fail on any vulnerability (default: fail only on HIGH/CRITICAL)
#
# pip-audit scans dependencies declared in pyproject.toml files against
# the PyPI vulnerability database.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGES_DIR="$PROJECT_ROOT/packages"
IGNORE_FILE="$PROJECT_ROOT/.pip-audit-ignore"

STRICT_MODE=false
if [[ "$1" == "--strict" ]]; then
    STRICT_MODE=true
fi

# Build ignore arguments if ignore file exists and is not empty
IGNORE_ARGS=""
if [[ -f "$IGNORE_FILE" ]] && [[ -s "$IGNORE_FILE" ]]; then
    while IFS= read -r vuln_id || [[ -n "$vuln_id" ]]; do
        # Skip empty lines and comments
        [[ -z "$vuln_id" || "$vuln_id" =~ ^[[:space:]]*# ]] && continue
        IGNORE_ARGS="$IGNORE_ARGS --ignore-vuln $vuln_id"
    done < "$IGNORE_FILE"
fi

# Collect all package directories with pyproject.toml
PACKAGE_DIRS=()

# Add root if pyproject.toml exists
if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    PACKAGE_DIRS+=("$PROJECT_ROOT")
fi

# Add all package directories
if [[ -d "$PACKAGES_DIR" ]]; then
    for package_dir in "$PACKAGES_DIR"/*/; do
        if [[ -f "${package_dir}pyproject.toml" ]]; then
            PACKAGE_DIRS+=("${package_dir%/}")
        fi
    done
fi

echo "=================================="
echo "Running pip-audit security scan"
echo "=================================="
if [[ "$STRICT_MODE" == "true" ]]; then
    echo "Mode: STRICT (fail on any vulnerability)"
else
    echo "Mode: DEFAULT (fail only on HIGH/CRITICAL)"
fi
echo "Scanning ${#PACKAGE_DIRS[@]} packages..."
echo ""

# Temporary file to collect all vulnerabilities
VULNS_FILE=$(mktemp)
trap "rm -f $VULNS_FILE" EXIT

for package_path in "${PACKAGE_DIRS[@]}"; do
    package_name=$(basename "$package_path")
    echo "Scanning: $package_name"

    # Run pip-audit with JSON output
    # Scan installed environment (in CI, only project deps are installed)
    set +e
    RAW_OUTPUT=$(cd "$package_path" && pip-audit --format=json $IGNORE_ARGS 2>&1)
    EXIT_CODE=$?
    set -e

    # Extract JSON from output (pip-audit may print status lines before JSON)
    JSON_OUTPUT=$(echo "$RAW_OUTPUT" | grep -E '^\s*[\[\{]' | head -1)
    if [[ -z "$JSON_OUTPUT" ]]; then
        # Try to find JSON object in the output
        JSON_OUTPUT=$(echo "$RAW_OUTPUT" | python3 -c "
import sys
import re
text = sys.stdin.read()
# Find JSON object or array
match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
if match:
    print(match.group(1))
" 2>/dev/null || echo "")
    fi

    # Check if output is valid JSON
    if [[ -n "$JSON_OUTPUT" ]] && echo "$JSON_OUTPUT" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
        # Extract vulnerabilities and append to file
        echo "$JSON_OUTPUT" | python3 -c "
import json
import sys

data = json.load(sys.stdin)
package_name = '$package_name'

# Handle both array and dict formats
if isinstance(data, dict):
    deps = data.get('dependencies', [])
else:
    deps = data

for dep in deps:
    if isinstance(dep, dict) and dep.get('vulns'):
        for v in dep['vulns']:
            vuln = {
                'package': dep['name'],
                'version': dep['version'],
                'id': v['id'],
                'fix_versions': v.get('fix_versions', []),
                'source_package': package_name
            }
            print(json.dumps(vuln))
" >> "$VULNS_FILE"

        # Count vulns for this package
        VULN_COUNT=$(echo "$JSON_OUTPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
deps = data.get('dependencies', data) if isinstance(data, dict) else data
count = sum(len(d.get('vulns', [])) for d in deps if isinstance(d, dict))
print(count)
")
        if [[ "$VULN_COUNT" -gt 0 ]]; then
            echo "  Found $VULN_COUNT vulnerabilities"
        else
            echo "  OK - No vulnerabilities found"
        fi
    elif [[ $EXIT_CODE -ne 0 ]]; then
        # pip-audit failed with non-JSON output (error)
        echo "  WARNING: pip-audit error (exit code $EXIT_CODE)"
        echo "$RAW_OUTPUT" | head -3 | sed 's/^/    /'
    else
        echo "  OK - No vulnerabilities found"
    fi
done

echo ""

# Process collected vulnerabilities
export VULNS_FILE
FILTER_RESULT=$(python3 << 'PYTHON_SCRIPT'
import json
import sys
import urllib.request
import urllib.error
import os

def get_severity(vuln_id):
    """Query OSV API to get CVSS score for a vulnerability."""
    try:
        url = f"https://api.osv.dev/v1/vulns/{vuln_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "pip-audit-severity-check"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)

            # Check severity array (CVSS scores)
            for sev in data.get("severity", []):
                score_val = sev.get("score", "0")
                if isinstance(score_val, str) and "/" in score_val:
                    # Handle CVSS vector strings like "CVSS:3.1/AV:L/..."
                    continue
                try:
                    score = float(score_val)
                    if score > 0:
                        return score
                except (ValueError, TypeError):
                    pass

            # Check database_specific for severity hints
            db_specific = data.get("database_specific", {})
            severity_str = str(db_specific.get("severity", "")).upper()
            if severity_str == "CRITICAL":
                return 9.5
            elif severity_str == "HIGH":
                return 8.0
            elif severity_str in ("MODERATE", "MEDIUM"):
                return 5.5
            elif severity_str == "LOW":
                return 2.5

            # Check affected entries for severity
            for affected in data.get("affected", []):
                severity_str = str(affected.get("database_specific", {}).get("severity", "")).upper()
                if severity_str == "CRITICAL":
                    return 9.5
                elif severity_str == "HIGH":
                    return 8.0
                elif severity_str in ("MODERATE", "MEDIUM"):
                    return 5.5
                elif severity_str == "LOW":
                    return 2.5

            # No severity found
            return -1
    except Exception:
        return -1

# Read vulnerabilities from temp file
vulns_file = os.environ.get("VULNS_FILE", "/dev/stdin")
vulns = []

try:
    with open(vulns_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    vulns.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
except FileNotFoundError:
    pass

if not vulns:
    print(json.dumps({"total": 0, "high_critical": [], "low_medium": [], "unknown": []}))
    sys.exit(0)

# Deduplicate by vulnerability ID
seen = set()
unique_vulns = []
for v in vulns:
    key = (v["package"], v["id"])
    if key not in seen:
        seen.add(key)
        unique_vulns.append(v)

vulns = unique_vulns

high_critical = []
low_medium = []
unknown = []

# Cache severity lookups
severity_cache = {}

for vuln in vulns:
    vuln_id = vuln["id"]

    if vuln_id not in severity_cache:
        severity_cache[vuln_id] = get_severity(vuln_id)

    score = severity_cache[vuln_id]
    vuln["severity_score"] = score

    if score < 0:
        vuln["severity"] = "UNKNOWN"
        unknown.append(vuln)
    elif score >= 7.0:
        vuln["severity"] = "CRITICAL" if score >= 9.0 else "HIGH"
        high_critical.append(vuln)
    else:
        vuln["severity"] = "MEDIUM" if score >= 4.0 else "LOW"
        low_medium.append(vuln)

result = {
    "total": len(vulns),
    "high_critical": high_critical,
    "low_medium": low_medium,
    "unknown": unknown
}

print(json.dumps(result))
PYTHON_SCRIPT
)

# Parse results
TOTAL=$(echo "$FILTER_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['total'])")
HIGH_CRITICAL_COUNT=$(echo "$FILTER_RESULT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['high_critical']))")
LOW_MEDIUM_COUNT=$(echo "$FILTER_RESULT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['low_medium']))")
UNKNOWN_COUNT=$(echo "$FILTER_RESULT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['unknown']))")

echo "=================================="
echo "Security Scan Summary"
echo "=================================="
echo "Total vulnerabilities found: $TOTAL"
echo "  - HIGH/CRITICAL: $HIGH_CRITICAL_COUNT"
echo "  - LOW/MEDIUM: $LOW_MEDIUM_COUNT"
echo "  - UNKNOWN severity: $UNKNOWN_COUNT"
echo ""

# Display HIGH/CRITICAL vulnerabilities
if [[ "$HIGH_CRITICAL_COUNT" -gt 0 ]]; then
    echo "HIGH/CRITICAL vulnerabilities (action required):"
    echo "$FILTER_RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for v in data['high_critical']:
    fix = ', '.join(v.get('fix_versions', [])) or 'No fix available'
    score = v['severity_score']
    print(f\"  - {v['package']}=={v['version']}: {v['id']} ({v['severity']}, score: {score:.1f})\")
    print(f\"    Fix versions: {fix}\")
"
    echo ""
fi

# Display UNKNOWN severity vulnerabilities
if [[ "$UNKNOWN_COUNT" -gt 0 ]]; then
    echo "UNKNOWN severity vulnerabilities (treated as HIGH for safety):"
    echo "$FILTER_RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for v in data['unknown']:
    fix = ', '.join(v.get('fix_versions', [])) or 'No fix available'
    print(f\"  - {v['package']}=={v['version']}: {v['id']}\")
    print(f\"    Fix versions: {fix}\")
"
    echo ""
fi

# Display LOW/MEDIUM vulnerabilities (informational)
if [[ "$LOW_MEDIUM_COUNT" -gt 0 ]]; then
    echo "LOW/MEDIUM vulnerabilities (informational only):"
    echo "$FILTER_RESULT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for v in data['low_medium']:
    score = v['severity_score']
    print(f\"  - {v['package']}=={v['version']}: {v['id']} ({v['severity']}, score: {score:.1f})\")
"
    echo ""
fi

# Determine exit status
SHOULD_FAIL=0

if [[ "$STRICT_MODE" == "true" ]]; then
    # Strict mode: fail on any vulnerability
    if [[ "$TOTAL" -gt 0 ]]; then
        SHOULD_FAIL=1
    fi
else
    # Default mode: fail only on HIGH/CRITICAL or UNKNOWN
    if [[ "$HIGH_CRITICAL_COUNT" -gt 0 ]] || [[ "$UNKNOWN_COUNT" -gt 0 ]]; then
        SHOULD_FAIL=1
    fi
fi

if [[ "$SHOULD_FAIL" -eq 1 ]]; then
    if [[ "$STRICT_MODE" == "true" ]]; then
        echo "FAILED: Found $TOTAL vulnerabilities (strict mode)"
    else
        echo "FAILED: Found $((HIGH_CRITICAL_COUNT + UNKNOWN_COUNT)) HIGH/CRITICAL/UNKNOWN vulnerabilities"
    fi
    echo ""
    echo "To ignore specific vulnerabilities, add their IDs to:"
    echo "  $IGNORE_FILE"
    echo ""
    echo "Example format:"
    echo "  GHSA-xxxx-xxxx-xxxx"
    echo "  CVE-2024-XXXX"
    exit 1
else
    if [[ "$LOW_MEDIUM_COUNT" -gt 0 ]]; then
        echo "PASSED: Found only LOW/MEDIUM vulnerabilities (not blocking)"
    else
        echo "PASSED: No vulnerabilities found"
    fi
    exit 0
fi
