# Alice Model Comparison System

A web-based tool for comparing AI-generated images using the Elo rating system. This allows blind A/B testing between different AI models to determine which produces better quality outputs.

## Features

- **Blind Comparison**: Images are shown without model information to ensure unbiased comparisons
- **Elo Rating System**: Uses chess-style Elo ratings to rank models based on head-to-head comparisons
- **Keyboard Shortcuts**: Fast comparison workflow with keyboard controls
- **Dark Theme**: Easy on the eyes for long comparison sessions
- **Persistent Storage**: Uses DuckDB to store comparisons and ratings

## Quick Start

1. Populate the system with images from your organized directory:
```bash
alice comparison populate-default --limit 100
```

2. Start the web server:
```bash
alice comparison server
```

3. Open http://localhost:8000 in your browser

4. Compare images:
   - Press **A** or **←** to select image A
   - Press **B** or **→** to select image B
   - Press **=** or **Space** for a tie
   - Use **1-4** to set comparison strength (slight/clear/strong/decisive)
   - Press **Enter** to submit

## CLI Commands

```bash
# Start the comparison web interface
alice comparison server [--host 0.0.0.0] [--port 8000]

# Populate with images from a specific directory
alice comparison populate /path/to/images --recursive --limit 500

# Populate from default organized directories
alice comparison populate-default --limit 1000

# View current model rankings
alice comparison stats

# Reset all comparison data
alice comparison reset
```

## How It Works

### Elo Rating System

The system uses the Elo rating algorithm (same as chess rankings):

- All models start at 1500 rating
- Winners gain rating points, losers lose points
- The amount gained/lost depends on:
  - Expected outcome (based on current ratings)
  - Actual outcome
  - Comparison strength (K-factor)

### Comparison Strength

When you select a winner, you can specify how strong the preference is:

- **Slight** (K=16): Small preference, minor rating change
- **Clear** (K=32): Clear winner, moderate rating change (default)
- **Strong** (K=64): Strong preference, larger rating change
- **Decisive** (K=128): One clearly superior, maximum rating change

### Smart Pairing

The system intelligently pairs images for comparison:
- Prioritizes models with similar ratings (more informative comparisons)
- Ensures variety by rotating through different model pairs
- Randomly selects images within each model

## Database Schema

Comparisons and ratings are stored in DuckDB at `~/.alice/comparisons.db`:

```sql
-- Comparison history
comparisons (
    id VARCHAR PRIMARY KEY,
    asset_a_id, asset_a_path, asset_a_model,
    asset_b_id, asset_b_path, asset_b_model,
    winner VARCHAR,  -- 'a', 'b', or 'tie'
    strength VARCHAR,  -- 'slight', 'clear', 'strong', 'decisive'
    timestamp TIMESTAMP
)

-- Model ratings
model_ratings (
    model VARCHAR PRIMARY KEY,
    rating DOUBLE,
    comparison_count INTEGER,
    win_count INTEGER,
    loss_count INTEGER,
    tie_count INTEGER
)

-- Available assets
assets (
    id VARCHAR PRIMARY KEY,
    path VARCHAR,
    model VARCHAR,
    metadata JSON
)
```

## Tips for Effective Comparisons

1. **Be Consistent**: Try to maintain consistent criteria across comparisons
2. **Focus on Quality**: Consider technical quality, aesthetic appeal, and prompt adherence
3. **Use Appropriate Strength**: 
   - Slight: Minor differences, could go either way
   - Clear: Definite preference but both are good
   - Strong: One is significantly better
   - Decisive: No contest, clear winner
4. **Take Breaks**: Comparison fatigue can affect judgment

## Integration with Alice

The comparison system integrates with Alice's existing infrastructure:
- Reads from organized directories
- Uses existing metadata when available
- Identifies models from directory structure
- Compatible with all supported image formats