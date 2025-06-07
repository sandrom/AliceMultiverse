# Provider Refactoring Example

This document shows how the new `BaseProvider` class simplifies provider implementations.

## Code Reduction Analysis

### Original OpenAI Provider
- **Total Lines**: ~430 lines
- **Boilerplate Code**: ~200 lines
- **Provider-Specific Logic**: ~230 lines

### Refactored OpenAI Provider
- **Total Lines**: ~280 lines (35% reduction)
- **Boilerplate Code**: ~30 lines (85% reduction)
- **Provider-Specific Logic**: ~250 lines (mostly unchanged)

## Key Improvements

### 1. API Key Management
**Before:**
```python
api_key = api_key or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key is required")
```

**After:**
```python
self.api_key = self._get_api_key("OPENAI_API_KEY")
```

### 2. Session Management
**Before:**
```python
async def _get_session(self) -> aiohttp.ClientSession:
    if not self._session:
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )
    return self._session
```

**After:**
```python
def _get_headers(self) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
    }
# Session creation handled by base class
```

### 3. Error Handling
**Before:**
```python
if response.status == 401:
    raise AuthenticationError("openai", "Invalid API key")
elif response.status == 429:
    raise RateLimitError("Rate limit exceeded")
elif response.status >= 400:
    error_text = await response.text()
    error_data = json.loads(error_text) if error_text else {}
    error_message = error_data.get("error", {}).get("message", f"API error: {response.status}")
    raise GenerationError(error_message)
```

**After:**
```python
await self._handle_response_errors(response, f"DALL-E {model}")
```

### 4. File Download
**Before:**
```python
from ..core.file_operations import download_file
output_path = await download_file(
    image_data["url"],
    request.output_dir,
    f"dalle_{model}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{idx}.png"
)
```

**After:**
```python
output_path = await self._download_result(
    image_data["url"],
    request.output_dir,
    f"dalle_{model}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{idx}.png"
)
```

### 5. Model Validation
**Before:**
```python
model = request.model or "dall-e-3"
if model not in self.MODELS:
    raise ValueError(f"Unknown model: {model}")
```

**After:**
```python
model = self._validate_model(request.model, GenerationType.IMAGE)
```

## Benefits of Refactoring

### 1. **Reduced Duplication**
- Common patterns extracted to base class
- No need to implement session management in each provider
- Standardized error handling across all providers

### 2. **Improved Maintainability**
- Bug fixes in base class benefit all providers
- Consistent behavior across providers
- Easier to add new providers

### 3. **Better Error Messages**
- Standardized error format
- Context-aware error messages
- Proper error type classification

### 4. **Enhanced Features**
- Automatic retry with exponential backoff
- Progress callbacks for long-running operations
- Model alias resolution
- Case-insensitive model matching

### 5. **Cleaner Code**
- Focus on provider-specific logic
- Less boilerplate
- Better separation of concerns

## Migration Guide

To migrate a provider to use `BaseProvider`:

1. **Change inheritance**: `class MyProvider(BaseProvider):`
2. **Remove boilerplate**: Delete session management, common error handling
3. **Implement required methods**: `_get_headers()`, provider-specific logic
4. **Use base helpers**: Replace common patterns with base class methods
5. **Test thoroughly**: Ensure all functionality still works

## Example Providers to Refactor

Based on the analysis, these providers would benefit most from refactoring:

1. **Anthropic Provider** - Similar session and error handling patterns
2. **Google AI Provider** - Complex error handling that could be simplified
3. **Midjourney Provider** - Polling logic could use base class helper
4. **Leonardo Provider** - Async job handling would benefit from polling helper
5. **Kling Provider** - Rate limit handling could be standardized

## Estimated Time Savings

- **Initial refactoring**: 30-60 minutes per provider
- **Future maintenance**: 50% reduction in time
- **New provider creation**: 2-3 hours saved per provider
- **Bug fixes**: Applied once, benefit all providers

## Conclusion

The `BaseProvider` class significantly reduces code duplication and improves maintainability. While the initial refactoring requires some effort, the long-term benefits include:

- Cleaner, more focused provider implementations
- Consistent behavior across all providers
- Easier debugging and maintenance
- Faster development of new providers

The 35% code reduction shown in the OpenAI example is typical, with some providers potentially seeing even greater reductions.