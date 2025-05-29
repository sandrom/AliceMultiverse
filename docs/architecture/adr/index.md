# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the AliceMultiverse project. ADRs document significant architectural decisions and the reasoning behind them.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences. ADRs help future developers understand why certain decisions were made and what trade-offs were considered.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-event-driven-architecture.md) | Event-Driven Architecture | Accepted | 2024-01-15 |
| [ADR-002](ADR-002-redis-event-persistence.md) | Redis Streams for Event Persistence | Accepted | 2024-01-16 |
| [ADR-003](ADR-003-monorepo-structure.md) | Monorepo for Service Evolution | Accepted | 2024-01-20 |
| [ADR-004](ADR-004-alice-sole-orchestrator.md) | Alice as Sole Orchestrator | Accepted | 2024-01-26 |
| [ADR-005](ADR-005-code-quality-security-tooling.md) | Code Quality and Security Tooling | Accepted | 2025-01-27 |
| [ADR-006](ADR-006-simplification-over-abstraction.md) | Simplification Over Abstraction | Accepted | 2025-01-29 |

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR-XXX: [Short Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]  
**Date**: YYYY-MM-DD  
**Context**: [Brief context]

## Context

[Describe the issue or problem that needs to be addressed]

## Decision

[Describe the decision that was made]

## Rationale

[Explain why this decision was made, including alternatives considered]

## Consequences

### Positive
- [List positive outcomes]

### Negative
- [List negative outcomes or trade-offs]

## References

- [Links to related documentation]
```

## Contributing

When making significant architectural changes:
1. Create a new ADR with the next available number
2. Use the template above
3. Link to the ADR in relevant documentation
4. Update this index