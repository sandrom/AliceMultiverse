# Provider Hierarchy Refactoring Plan

## Current State
- `Provider` (abstract base) - defines interface
- `BaseProvider` extends `Provider` - has common functionality but UNUSED
- Individual providers extend `Provider` directly - duplicate lots of code

## Problems
1. All providers reimplement:
   - Session management
   - Error handling (401, 429, etc.)
   - Parameter extraction
   - File download
   - Response handling

2. `BaseProvider` exists but is not used

## Proposed Solution

### Option 1: Use BaseProvider (Recommended)
Change all providers to extend `BaseProvider` instead of `Provider`:

```python
# Before
class OpenAIProvider(Provider):
    def __init__(self, api_key: str | None = None):
        # Duplicate session management
        self._session = None
        
# After  
class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str | None = None):
        super().__init__("openai", api_key)
        # Session management handled by BaseProvider
```

Benefits:
- Remove ~100 lines of duplicate code per provider
- Consistent error handling
- Easier to maintain

### Option 2: Merge BaseProvider into Provider
Move all BaseProvider functionality into Provider and make abstract methods optional.

Benefits:
- Simpler hierarchy
- No intermediate class

Drawbacks:
- Provider becomes larger
- Harder to see what's required vs optional

## Implementation Steps

1. Update each provider to extend BaseProvider
2. Remove duplicate code from each provider
3. Ensure tests still pass
4. Update any provider-specific error handling