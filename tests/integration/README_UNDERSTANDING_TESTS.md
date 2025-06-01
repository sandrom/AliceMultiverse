# Understanding System Integration Tests

This document describes the integration test scenarios for the AliceMultiverse understanding system.

## Test Categories

### 1. Multi-Provider Analysis Tests
Tests the ability to analyze images using multiple AI providers simultaneously.

**Scenarios:**
- **Single Provider Analysis**: Verify that a single provider can analyze an image correctly
- **Multi-Provider Analysis**: Test concurrent analysis with multiple providers
- **Provider Failure Handling**: Ensure graceful handling when one provider fails
- **Consensus Building**: Test combining results from multiple providers to build consensus

**Key Assertions:**
- Each provider returns valid analysis results
- Failed providers don't break the entire analysis
- Results contain expected fields (description, tags, style, mood, etc.)
- Consensus combines tags without duplicates

### 2. Metadata Embedding Tests
Tests the ability to embed and extract metadata from image files.

**Scenarios:**
- **Embed and Extract**: Embed metadata in an image and extract it back
- **Persistence Across Copies**: Verify metadata survives file copying
- **UnifiedCache Integration**: Test that UnifiedCache properly embeds metadata when saving

**Key Assertions:**
- Embedded metadata can be extracted accurately
- Metadata persists when files are copied or moved
- All key fields are preserved (description, tags, provider info)
- Integration with UnifiedCache works seamlessly

### 3. Tag Search Functionality Tests
Tests the tag-based search capabilities of the system.

**Scenarios:**
- **Search by Tags**: Find images containing specific tags
- **Multi-Tag Search**: Search with multiple tags (AND operation)
- **Search with Exclusions**: Find images while excluding certain tags
- **Batch Analysis and Search**: Analyze multiple images then search them

**Key Assertions:**
- Search returns correct images based on tags
- Multiple tags work as AND operation
- Exclusion filters work correctly
- Batch-analyzed images are searchable

### 4. End-to-End Workflow Test
Tests the complete workflow from analysis to search and retrieval.

**Workflow Steps:**
1. Initialize system components (cache, embedder)
2. Analyze image (mocked in tests, real in production)
3. Save analysis with metadata embedding
4. Verify embedded metadata
5. Load from cache
6. Move/rename file
7. Load from new location using embedded metadata

**Key Assertions:**
- Complete workflow executes without errors
- Metadata persists through file operations
- Cache and embedded metadata stay in sync
- System handles file moves gracefully

## Running the Tests

```bash
# Run all understanding system integration tests
pytest tests/integration/test_understanding_system.py -v

# Run specific test categories
pytest tests/integration/test_understanding_system.py::TestMultiProviderAnalysis -v
pytest tests/integration/test_understanding_system.py::TestMetadataEmbedding -v
pytest tests/integration/test_understanding_system.py::TestTagSearchFunctionality -v

# Run with coverage
pytest tests/integration/test_understanding_system.py --cov=alicemultiverse.understanding --cov-report=html
```

## Mock Strategies

The tests use mocks to avoid requiring actual API keys:
- **Provider Mocks**: AsyncMock objects simulate AI provider responses
- **Analysis Results**: Mock `ImageAnalysisResult` objects with realistic data
- **Batch Processing**: Mocked to test concurrent operations without API calls

## Test Data

- **Sample Images**: Created using PIL with basic colors
- **Mock Tags**: Realistic tag sets (e.g., ["sunset", "landscape", "nature"])
- **Mock Descriptions**: Human-like descriptions of test images
- **Mock Metadata**: Complete metadata structures with all expected fields

## Future Test Scenarios

1. **Similarity Search**: Test finding visually similar images
2. **Performance Tests**: Measure search speed with large datasets
3. **Cache Invalidation**: Test metadata updates and cache consistency
4. **Provider Cost Optimization**: Test cheapest provider selection
5. **Custom Instructions**: Test analysis with custom prompts
6. **Error Recovery**: Test handling of corrupted metadata or missing files

## Integration Points

The understanding system integrates with:
- **UnifiedCache**: For metadata storage and retrieval
- **MetadataEmbedder**: For embedding data in image files
- **DuckDB**: For efficient tag searches (when available)
- **AI Providers**: Anthropic, OpenAI, Google AI, DeepSeek

## Known Limitations

- Tests use mocks instead of real AI providers
- Search functionality is basic (no fuzzy matching yet)
- Consensus building is simplified in tests
- No visual similarity search implemented yet