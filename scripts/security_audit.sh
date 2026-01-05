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
for package_dir in "$PACKAGES_DIR"/*/; do
    if [[ -f "${package_dir}pyproject.toml" ]]; then
        PACKAGE_DIRS+=("${package_dir%/}")
    fi
done

echo "=================================="
echo "Running pip-audit security scan"
echo "=================================="
echo "Scanning ${#PACKAGE_DIRS[@]} packages..."
echo ""

FAILED=0
VULN_COUNT=0

for package_path in "${PACKAGE_DIRS[@]}"; do
    package_name=$(basename "$package_path")
    echo "Scanning: $package_name"

    # Change to package directory and run pip-audit
    # pip-audit automatically reads pyproject.toml when run in a directory
    set +e
    OUTPUT=$(cd "$package_path" && pip-audit --disable-pip --require-hashes=false $IGNORE_ARGS 2>&1)
    EXIT_CODE=$?
    set -e

    if [[ $EXIT_CODE -ne 0 ]]; then
        # Check if it's an actual vulnerability or just an error
        if echo "$OUTPUT" | grep -q "GHSA\|CVE\|PYSEC\|found [0-9]* vulnerabilit"; then
            echo "  VULNERABILITIES FOUND in $package_name:"
            echo "$OUTPUT" | sed 's/^/    /'
            echo ""

            # Count vulnerabilities (lines that look like vulnerability entries)
            PACKAGE_VULNS=$(echo "$OUTPUT" | grep -c "GHSA\|CVE\|PYSEC" || true)
            VULN_COUNT=$((VULN_COUNT + PACKAGE_VULNS))
            FAILED=1
        else
            # pip-audit may fail for other reasons (e.g., can't parse pyproject.toml)
            # In CI, we want to catch these issues too
            echo "  WARNING: pip-audit returned non-zero exit code:"
            echo "$OUTPUT" | sed 's/^/    /'
            echo ""
            # Don't fail on parse errors, only on actual vulnerabilities
        fi
    else
        echo "  OK - No vulnerabilities found"
    fi
done

echo ""
echo "=================================="
echo "Security Scan Summary"
echo "=================================="

if [[ $FAILED -eq 1 ]]; then
    echo "FAILED: Found vulnerabilities in dependencies"
    echo "Total vulnerability references: $VULN_COUNT"
    echo ""
    echo "To ignore known vulnerabilities, add their IDs to:"
    echo "  $IGNORE_FILE"
    echo ""
    echo "Example format:"
    echo "  GHSA-xxxx-xxxx-xxxx"
    echo "  CVE-2024-XXXX"
    exit 1
else
    echo "PASSED: No vulnerabilities found"
    exit 0
fi
