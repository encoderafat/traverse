#!/bin/bash
# Script to run end-to-end tests with real APIs
# Usage: ./run_e2e_tests.sh [test_pattern]

set -e  # Exit on any error

echo "🔍 Running End-to-End Tests with Real APIs"
echo "⚠️  WARNING: This will make real API calls that may incur costs"
echo ""

# Check if required environment variables are set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY environment variable is not set"
    echo "Please set your API key before running these tests"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is not set"
    echo "Please set your database URL before running these tests"
    exit 1
fi

# Enable E2E tests
export RUN_E2E_TESTS=true

echo "🚀 Running E2E tests..."
echo ""

# Determine test pattern to run
TEST_PATTERN=${1:-"backend/tests/e2e/"}

# Run the tests
python -m pytest $TEST_PATTERN -v --tb=short

echo ""
echo "✅ E2E tests completed!"
echo "📊 Check the output above for test results"
echo ""
echo "💡 Tip: To run specific tests, use:"
echo "   ./run_e2e_tests.sh 'backend/tests/e2e/test_real_api_e2e.py::TestRealApiE2E::test_specific_test'"