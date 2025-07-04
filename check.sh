#!/bin/bash
# Combined code quality check script
# Runs formatting, linting, and type checking

set -e  # Exit on any error

echo "🔧 Running code formatting..."
uv run ruff format .

echo "🔧 Running biome formatting and linting..."
biome check --files-ignore-unknown=true --write

echo "🔍 Running linting..."
uv run ruff check . --fix

echo "🏗️  Running Python type checking..."
uv run pyright

echo "🏗️  Running TypeScript type checking..."
pnpm --dir ui typecheck

echo "🧪 Running Python tests..."
uv run pytest -v

echo "✅ All checks passed!"