# Understanding Module Test Requirements

This document outlines the test requirements and coverage for the AliceMultiverse understanding module.

## Module Overview

The understanding module provides AI-powered image analysis using multiple providers:
- Anthropic Claude (Claude 3 Haiku, Sonnet, Opus)
- OpenAI GPT-4 Vision (GPT-4o, GPT-4o-mini)
- Google AI Gemini (Gemini 1.5 Flash, Pro)
- DeepSeek (DeepSeek Reasoner)

## Test Coverage

### 1. Provider Tests (`test_understanding_providers.py`)
**Coverage**: 25 tests covering all 4 providers

#### Test Categories:
- **Initialization** (12 tests)
  - With explicit API key
  - From environment variable
  - Without API key (error handling)
  - Model selection

- **Cost Estimation** (5 tests)
  - Different models within same provider
  - Detailed vs simple analysis
  - Cost comparison across providers

- **Image Analysis** (5 tests)
  - Successful analysis with mocked API responses
  - API error handling (rate limits, auth failures)
  - Response parsing and validation

- **Provider Features** (3 tests)
  - Batch support flags
  - Consistent tag format across providers
  - Cost ordering verification

### 2. Integration Tests (`test_understanding_system.py`)
**Coverage**: 6 integration test classes

#### Test Categories:
- **Multi-Provider Analysis**
  - Single provider workflow
  - Multiple providers in parallel
  - Provider failure handling
  - Consensus building from multiple results

- **Metadata Embedding**
  - Embed and extract metadata from images
  - Persistence across file operations
  - Integration with UnifiedCache

- **Tag Search**
  - Search by single/multiple tags
  - OR logic for tag matching
  - Manual exclusion filtering

- **End-to-End Workflow**
  - Complete analysis to retrieval flow
  - File movement handling
  - Metadata persistence

## Test Requirements

### Unit Tests Must Cover:

1. **Provider Initialization**
   - All supported models for each provider
   - API key handling (explicit, env, missing)
   - Default model selection

2. **Cost Calculation**
   - Accurate pricing for each model
   - Token estimation logic
   - Detailed vs simple analysis costs

3. **API Communication**
   - Request formatting for each provider
   - Response parsing and error handling
   - Rate limit and auth error handling

4. **Result Consistency**
   - Tag format (Dict[str, List[str]])
   - Required fields in ImageAnalysisResult
   - Provider and model identification

### Integration Tests Must Cover:

1. **Multi-Provider Scenarios**
   - Parallel analysis with multiple providers
   - Failure isolation (one provider fails, others continue)
   - Result aggregation and consensus

2. **Metadata Lifecycle**
   - Embedding in supported image formats
   - Extraction after file operations
   - Cache and embedded metadata synchronization

3. **Search Functionality**
   - Tag-based search with OR logic
   - Category-specific tag search
   - Performance with large metadata sets

## Mocking Strategy

### Unit Tests:
- Mock `aiohttp.ClientSession` for API calls
- Use proper async context managers for session mocks
- Return realistic API responses for each provider

### Integration Tests:
- Mock provider analyze methods directly
- Use temporary directories for file operations
- Create realistic ImageAnalysisResult objects

## Running Tests

```bash
# Run all understanding tests
pytest tests/unit/test_understanding_providers.py tests/integration/test_understanding_system.py -v

# Run with coverage
pytest tests/unit/test_understanding_providers.py --cov=alicemultiverse.understanding --cov-report=html

# Run specific provider tests
pytest tests/unit/test_understanding_providers.py::TestAnthropicImageAnalyzer -v
```

## Future Test Scenarios

1. **Streaming Responses** - Test providers that support streaming
2. **Batch Analysis** - Test batch endpoints when available
3. **Custom Instructions** - Test provider-specific prompting
4. **Rate Limiting** - Test exponential backoff and retry logic
5. **Token Counting** - Verify accurate token usage tracking
6. **Provider Selection** - Test automatic cheapest provider selection
7. **Caching** - Test result caching to avoid duplicate API calls
8. **Timeout Handling** - Test long-running analysis timeouts

## Maintenance Notes

- Update cost assertions when providers change pricing
- Add new models as providers release them
- Verify mock responses match actual API formats
- Keep tag categories aligned with provider capabilities