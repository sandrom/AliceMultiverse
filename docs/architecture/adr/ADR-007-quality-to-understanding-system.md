# ADR-007: Transition from Quality Assessment to Understanding System

**Status**: Accepted  
**Date**: 2025-01-31  
**Context**: Quality scoring proved too subjective for AI-generated content

## Context

The original system used BRISQUE quality assessment and star ratings to organize AI-generated images. However, this approach had several limitations:

1. **Subjectivity**: BRISQUE was designed for natural photographs, not AI-generated art
2. **Limited Value**: Quality scores didn't help users find specific content
3. **User Feedback**: Users wanted semantic search, not quality-based organization
4. **Technical Debt**: The quality system added complexity without proportional value

Users consistently requested features like "find all cyberpunk images" or "show me portraits with blue lighting" rather than "show me 5-star images."

## Decision

Replace the quality assessment system with a comprehensive understanding system that:
- Uses multiple AI providers (OpenAI, Anthropic, Google) for image analysis
- Generates semantic tags for content discovery
- Embeds tags directly in file metadata for portability
- Supports hierarchical tagging (e.g., art_style > cyberpunk > neon)
- Enables natural language search queries

## Rationale

### Why Understanding Over Quality

1. **User Value**: Semantic search directly addresses user needs
2. **Objectivity**: Tags describe content without subjective quality judgments
3. **Flexibility**: Multiple providers offer different perspectives and capabilities
4. **Future-Proof**: Understanding enables more advanced features (similarity search, recommendations)

### Alternatives Considered

1. **Hybrid Approach**: Keep quality scores alongside tags
   - Rejected: Added complexity without clear value
   
2. **Single Provider**: Use only one AI provider for analysis
   - Rejected: Different providers excel at different aspects
   
3. **Database-Only Tags**: Store tags only in database
   - Rejected: Violates portability principle

## Consequences

### Positive
- Users can find content using natural language
- Tags travel with files (embedded metadata)
- System is more objective and predictable
- Enables future features like cross-modal search
- Better alignment with AI-native architecture

### Negative
- Higher API costs for analysis
- Breaking change for existing users
- Need to migrate existing metadata
- More complex provider management

## Implementation Details

Key components:
- `alicemultiverse/understanding/` - Core understanding system
- `alicemultiverse/understanding/providers.py` - Multi-provider analysis
- `alicemultiverse/understanding/advanced_tagger.py` - Hierarchical tagging
- `alicemultiverse/metadata/embedder.py` - Metadata embedding

## References

- [Understanding System Documentation](../../developer/understanding-system.md)
- [Migration Guide](../../migration/quality-to-understanding.md)
- Issue #245: User feedback on quality system limitations
- PR #267: Understanding system implementation