#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PACKAGES=("job-scrapper-contracts" "scrapper-messaging" "telemetry")

echo "Uninstalling all packages..."
for package in "${PACKAGES[@]}"; do
    pip uninstall -y "$package" 2>/dev/null || echo "  $package (not installed)"
done

echo ""
echo "Installing all packages in editable mode..."
for package in "${PACKAGES[@]}"; do
    echo "  Installing $package..."
    pip install -e "$PROJECT_ROOT/packages/$package[dev]"
done

echo ""
echo "Installing root project dev dependencies..."
pip install -e "$PROJECT_ROOT[dev]"

echo ""
echo "All packages installed successfully!"
