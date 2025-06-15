# Outdated References Report

This report identifies outdated references found in documentation files that need to be updated.

## 1. MetadataCache References

**Issue**: Several documents still reference `MetadataCache` which should be `UnifiedCache` or `MetadataCacheAdapter`.

### Files with outdated references:

- **`/docs/architecture/caching-strategy.md`**
  - Line 13: References `MetadataCache` in the architecture diagram
  - Line 32-35: Shows relationship between UC and MC
  - This document actually describes UnifiedCache correctly but the diagram still shows the old MetadataCache component

- **`/docs/architecture/system-design.md`**
  - Line 19: Lists `MC[Metadata Cache]` in the architecture diagram
  - Line 54: Shows `MC --> CACHE` relationship
  - Line 76: `self.metadata_cache = MetadataCache(source_dir, force_reindex)`
  - Lines 120-138: Entire section titled "Metadata Cache" with old class definition

## 2. alice_events Module References

**Issue**: References to `alice_events` module which doesn't exist (found in test_monorepo.py).

### Files with outdated references:

- **`/docs/architecture/adr/ADR-003-monorepo-structure.md`**
  - Line 23: References `alice-events/` package in proposed structure
  - Line 121: `from alice_events import AssetProcessedEvent`
  - This is describing a proposed future structure, not current implementation

- **`/docs/developer/prometheus-metrics.md`**
  - Line 340: `from alicemultiverse.core.metrics import track_api_metrics`
  - The import path might be outdated

## 3. Quality Assessment / BRISQUE / Star Ratings

**Issue**: Many references to the deprecated quality assessment system that has been replaced with the understanding system.

### Files with extensive outdated references:

- **`/docs/architecture/system-design.md`**
  - Lines 23-29: Quality Pipeline section with BR[BRISQUE Scorer]
  - Lines 77: `self.quality_assessor = BRISQUEAssessor()`
  - Lines 95-117: Quality Assessment Pipeline section
  - Lines 209-217: Path construction with quality_stars
  - Lines 259-265: Cache entry with quality_score and quality_stars

- **`/docs/architecture/caching-strategy.md`**
  - Lines 139-143: Cache entry shows quality field with score, stars, and method
  - Line 16: References QS[QualityScorer] component

- **`/docs/getting-started/configuration.md`**
  - Lines 56: `quality: false` in processing options
  - Lines 73-98: Entire quality assessment configuration section with BRISQUE thresholds
  - Lines 158-165: Pipeline configurations referencing quality stages

- **`/docs/architecture/design-decisions.md`**
  - Lines 37-70: Section 2 "Progressive Quality Pipeline"
  - Lines 72-92: Section 3 "Star Rating Organization"
  - Lines 94-116: Section 4 "BRISQUE as Primary Quality Metric"

- **`/docs/developer/prometheus-metrics.md`**
  - Lines 207-221: `alice_asset_quality_score` metric documentation

## 4. Additional Outdated References

### Pipeline configurations
Many files still reference the multi-stage quality pipeline which has been replaced:
- Basic, standard, premium pipeline configurations
- Stage-specific settings for brisque, sightengine, claude

### Import paths
Some documentation shows imports that may no longer be valid after refactoring.

## Recommendations

1. **Update architecture diagrams** to show UnifiedCache instead of MetadataCache
2. **Remove quality assessment documentation** and replace with understanding system documentation
3. **Update configuration examples** to remove quality-related settings
4. **Update ADR-003** to clarify it's a proposed future structure, not current
5. **Review all code examples** in documentation for accuracy
6. **Add deprecation notices** to sections that describe removed features
7. **Update prometheus metrics** documentation to remove quality score metrics

## Note

Some of these references might be intentionally preserved for historical context or migration guidance. Each should be evaluated individually to determine if it should be updated, removed, or marked as deprecated/historical.