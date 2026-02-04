# End-to-End Tests with Real APIs

This directory contains end-to-end tests that make real API calls to external services like Google's Gemini API and Opik. These tests are intended for internal testing only and should not be run in automated CI/CD pipelines.

## Purpose

- Test actual integration with real Gemini API
- Validate that the full learning path generation flow works with real AI calls
- Catch issues that might not appear in mocked unit tests
- Verify that the system behaves correctly with real API responses

## Prerequisites

Before running these tests, you need:

1. Valid Google API key for Gemini
2. Proper database configuration
3. Optional: Opik API key (if using Opik integration)

## Running the Tests

### 1. Set up your environment:

```bash
# Set your real API keys
export GOOGLE_API_KEY=your_actual_google_api_key
export GEMINI_MODEL=gemini-3-flash-preview  # or whatever model you prefer
export DATABASE_URL=postgresql://user:password@host:port/database_name
export SUPABASE_URL=your_supabase_url
export SUPABASE_JWT_SECRET=your_supabase_secret
export SUPABASE_ANON_KEY=your_supabase_anon_key

# Enable the E2E tests (this is required to run them)
export RUN_E2E_TESTS=true
```

### 2. Run the tests:

```bash
# Run all E2E tests
python -m pytest backend/tests/e2e/ -v

# Run specific test
python -m pytest backend/tests/e2e/test_real_api_e2e.py::TestRealApiE2E::test_full_learning_path_generation_with_real_gemini -v

# Run with detailed logging
python -m pytest backend/tests/e2e/ -v -s
```

## Important Notes

⚠️ **Cost Warning**: These tests make real API calls which may incur costs. Monitor your API usage!

⚠️ **Rate Limits**: Be mindful of API rate limits. Consider adding delays between tests if needed.

⚠️ **Data Persistence**: Tests may create real data in your database and external services.

⚠️ **Not for CI/CD**: These tests should only be run manually for internal testing.

## Test Structure

- Tests are marked with `@pytest.mark.skipif` to prevent accidental execution
- Tests require `RUN_E2E_TESTS=true` environment variable to run
- Each test validates the complete flow from API request to response
- Tests clean up after themselves where possible

## Troubleshooting

If tests fail:

1. Verify your API keys are valid and have sufficient quota
2. Check that your database is accessible
3. Ensure all required environment variables are set
4. Look for rate limiting errors from external APIs

## When to Run

- Before major releases
- When making changes to AI integration code
- When debugging issues that don't reproduce in unit tests
- Periodic validation of external API integrations