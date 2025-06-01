# Rating Systems Research: A/B vs 1-10 Scale

## Context
- Single person rating (not crowd-sourced)
- Complex outputs (descriptions, tags, prompts)
- Need to compare 2+ AI models
- Goal: Identify best performing models over time

## Option 1: Simple A/B Comparison

### How it works
```
┌─────────────┐     ┌─────────────┐
│   Model A   │     │   Model B   │
│             │     │             │
│ Description │     │ Description │
│    Tags     │     │    Tags     │
│   Prompt    │     │   Prompt    │
└─────────────┘     └─────────────┘
     
[A is Better] [Equal] [B is Better]
       ↑         ↑          ↑
    Press A   Press =    Press B
```

### Pros
- **Faster**: Single keystroke (A/B/=)
- **Less cognitive load**: Simple "which is better?"
- **Consistent**: No scale calibration issues
- **Natural**: Humans are good at comparisons

### Cons
- **Less granular**: Can't express "how much better"
- **No absolute quality**: Only relative comparison
- **Harder to compare 3+ models**: Need round-robin

### Research Support
- Elo rating systems (chess, gaming) use binary comparisons
- Microsoft's TrueSkill evolved from simple win/loss
- A/B testing in UX proven effective for preferences

## Option 2: 1-10 Rating Scale

### How it works
```
┌─────────────────────┐
│      Model A        │
│                     │
│ Description: ...    │
│ Tags: ...           │
│ Prompt: ...         │
│                     │
│ Rate: [1][2][3]...  │
│       ↑             │
│    Press 1-9,0      │
└─────────────────────┘
```

### Pros
- **Absolute quality measure**: Can say "this is objectively good/bad"
- **More information**: Captures strength of preference
- **Better for 3+ models**: Each rated independently
- **Tracks improvement**: See if models get better over time

### Cons
- **Scale calibration**: Your "7" today might be "8" tomorrow
- **Slower**: Need to think about exact number
- **Anchoring bias**: Previous ratings influence current ones
- **Central tendency**: People avoid extremes (mostly 5-8)

### Research Support
- Likert scales widely used in research
- Netflix moved FROM 5-star TO thumbs up/down
- Amazon reviews cluster at 1 and 5 stars

## Option 3: Hybrid Approach (Recommended)

### Progressive Rating System
```
Step 1: Quick A/B (Required)
┌───────┐ vs ┌───────┐
│   A   │    │   B   │
└───────┘    └───────┘
Press: [A] [=] [B]

Step 2: Strength (Optional)
How much better?
[Slightly] [Clearly] [Much]
Press: [1] [2] [3]

Result: A+2 (A is clearly better)
```

### Implementation
```python
# Keyboard shortcuts
'a' or '←' = A wins
'b' or '→' = B wins  
'=' or 'Space' = Equal
'Escape' = Skip

# If winner selected:
'1' = Slightly better
'2' = Clearly better
'3' = Much better
'Enter' = Confirm (default: slightly)
```

## Recommendation: Start with A/B, Add Scale Later

### Phase 1: Pure A/B Comparison
- Implement simple A/B with keyboard shortcuts
- Use Elo rating system to track model performance
- Collect data on comparison consistency

### Phase 2: Add Optional Strength
- After picking winner, optionally rate "how much better"
- Converts to: Win by 1 (slight), 2 (clear), 3 (much)
- More nuanced Elo updates

### Why This Works Best:
1. **Fast**: Usually just one keystroke
2. **Flexible**: Can add detail when it matters
3. **Statistically sound**: Elo works with sparse data
4. **Natural**: Comparison is easier than absolute rating
5. **Keyboard-friendly**: Arrow keys or letters

## Elo Rating Implementation

```python
class ModelEloRating:
    """Track model performance using Elo ratings."""
    
    def __init__(self, k_factor=32):
        self.ratings = {}  # model -> rating
        self.k_factor = k_factor
        
    def update_ratings(self, winner: str, loser: str, margin: int = 1):
        """
        Update Elo ratings after comparison.
        margin: 1 (slight), 2 (clear), 3 (much)
        """
        winner_rating = self.ratings.get(winner, 1500)
        loser_rating = self.ratings.get(loser, 1500)
        
        # Expected scores
        expected_winner = 1 / (1 + 10**((loser_rating - winner_rating) / 400))
        expected_loser = 1 - expected_winner
        
        # Actual scores (with margin)
        score_winner = 0.5 + (0.5 * margin / 3)  # 0.67, 0.83, 1.0
        score_loser = 1 - score_winner
        
        # Update ratings
        self.ratings[winner] = winner_rating + self.k_factor * (score_winner - expected_winner)
        self.ratings[loser] = loser_rating + self.k_factor * (score_loser - expected_loser)
```

## UI Design for A/B Comparison

```html
<div class="comparison-view">
    <!-- Image -->
    <div class="image-panel">
        <img src="..." />
    </div>
    
    <!-- Models side by side -->
    <div class="models-compare">
        <div class="model model-a" data-key="a">
            <h2>Model A</h2>
            <div class="content">...</div>
        </div>
        
        <div class="vs">VS</div>
        
        <div class="model model-b" data-key="b">
            <h2>Model B</h2>
            <div class="content">...</div>
        </div>
    </div>
    
    <!-- Quick actions -->
    <div class="actions">
        <div class="quick-compare">
            <button data-key="a">← A Better</button>
            <button data-key="=">=  Equal  =</button>
            <button data-key="b">B Better →</button>
        </div>
        
        <!-- Shows after selection -->
        <div class="strength-rating" style="display:none">
            <p>How much better?</p>
            <button data-key="1">Slightly (1)</button>
            <button data-key="2">Clearly (2)</button>
            <button data-key="3">Much (3)</button>
        </div>
    </div>
    
    <!-- Keyboard hints -->
    <div class="keyboard-hints">
        A/← = A wins | =/Space = Equal | B/→ = B wins | Esc = Skip
    </div>
</div>
```

## Conclusion

**Recommended: A/B Comparison with Optional Strength Rating**

This gives you:
- Speed of binary comparison (usually 1 keystroke)
- Option for more detail when needed
- Proven Elo system for rankings
- Natural keyboard flow
- Avoids slider friction and scale calibration issues

The 1-10 scale adds cognitive overhead without proportional benefit for a single rater comparing complex outputs.