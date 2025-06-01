# Model Comparison & Rating System Design

## Overview

A human-in-the-loop system to compare and rate different AI models' image understanding capabilities. This helps identify which models work best for different types of images and improves model selection over time.

## Key Features

1. **Blind Comparison**: Models are anonymized during rating to prevent bias
2. **Side-by-Side View**: Compare 2+ model outputs for the same image
3. **Persistent Ratings**: Track performance over time to identify best models
4. **AI-First Workflow**: Initiated from AI assistant, completed in web UI
5. **Automatic Learning**: Use ratings to improve future model selection

## Architecture

### 1. Data Model

```python
# DuckDB schema for model comparisons
CREATE TABLE model_outputs (
    content_hash VARCHAR,
    model_id VARCHAR,  -- Anonymized during comparison
    provider VARCHAR,  -- Hidden during comparison
    model_name VARCHAR,  -- Hidden during comparison
    
    -- Raw outputs from model
    description TEXT,
    tags JSON,
    generated_prompt TEXT,
    negative_prompt TEXT,
    
    -- Metadata
    cost DECIMAL(10,6),
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    analyzed_at TIMESTAMP,
    
    PRIMARY KEY (content_hash, model_id)
);

CREATE TABLE comparison_sessions (
    session_id VARCHAR PRIMARY KEY,
    content_hash VARCHAR,
    models_compared VARCHAR[],  -- Array of model_ids
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    initiated_by VARCHAR  -- 'ai' or 'manual'
);

CREATE TABLE model_ratings (
    session_id VARCHAR,
    model_id VARCHAR,
    rating INTEGER CHECK (rating >= 0 AND rating <= 10),
    
    -- Detailed ratings (optional)
    accuracy_rating INTEGER,
    completeness_rating INTEGER,
    usefulness_rating INTEGER,
    
    -- Feedback
    notes TEXT,
    rated_at TIMESTAMP,
    
    PRIMARY KEY (session_id, model_id)
);

-- Aggregate performance view
CREATE VIEW model_performance AS
SELECT 
    mo.provider,
    mo.model_name,
    COUNT(DISTINCT mr.session_id) as total_ratings,
    AVG(mr.rating) as avg_rating,
    STDDEV(mr.rating) as rating_stddev,
    AVG(mo.cost) as avg_cost,
    AVG(mr.rating / NULLIF(mo.cost, 0)) as value_score  -- Rating per dollar
FROM model_outputs mo
JOIN model_ratings mr ON mo.model_id = mr.model_id
GROUP BY mo.provider, mo.model_name;
```

### 2. Web Interface Design

```html
<!-- Comparison Interface -->
<div class="comparison-container">
    <!-- Image Display -->
    <div class="image-panel">
        <img src="/api/image/{content_hash}" />
        <div class="image-metadata">
            <p>Project: {project_name}</p>
            <p>Created: {date}</p>
        </div>
    </div>
    
    <!-- Model Outputs (2-4 columns) -->
    <div class="models-grid">
        <!-- Model A (anonymized) -->
        <div class="model-output" data-model-id="xyz123">
            <h3>Model A</h3>
            
            <section class="description">
                <h4>Description</h4>
                <p>{description}</p>
            </section>
            
            <section class="tags">
                <h4>Tags</h4>
                <div class="tag-categories">
                    <div class="tag-category">
                        <h5>Style</h5>
                        <span class="tag">cyberpunk</span>
                        <span class="tag">neon</span>
                    </div>
                    <!-- More categories -->
                </div>
            </section>
            
            <section class="prompts">
                <h4>Generated Prompt</h4>
                <p class="prompt">{generated_prompt}</p>
            </section>
            
            <section class="rating">
                <h4>Rate This Analysis</h4>
                <input type="range" min="0" max="10" value="5" />
                <span class="rating-value">5</span>
                
                <!-- Optional detailed ratings -->
                <details>
                    <summary>Detailed Ratings</summary>
                    <label>Accuracy: <input type="range" min="0" max="10" /></label>
                    <label>Completeness: <input type="range" min="0" max="10" /></label>
                    <label>Usefulness: <input type="range" min="0" max="10" /></label>
                </details>
                
                <textarea placeholder="Notes (optional)"></textarea>
            </section>
        </div>
        
        <!-- Model B -->
        <div class="model-output" data-model-id="abc456">
            <!-- Same structure -->
        </div>
    </div>
    
    <!-- Submit -->
    <div class="actions">
        <button onclick="submitRatings()">Submit Ratings</button>
        <button onclick="skipImage()">Skip</button>
    </div>
</div>
```

### 3. Workflow

```python
# 1. AI initiates comparison
response = alice.compare_models(
    image_path="path/to/image.jpg",
    models=["anthropic", "openai", "deepseek"],  # Or "auto" for random selection
    blind=True  # Anonymize models
)

# Returns:
{
    "comparison_url": "http://localhost:8080/compare/session123",
    "session_id": "session123",
    "expires_in": 3600  # 1 hour to complete
}

# 2. User opens web interface
# Models are shown as "Model A", "Model B", etc.

# 3. User rates each model output

# 4. System stores ratings and reveals model identities

# 5. AI can query performance data
best_models = alice.get_model_rankings(
    image_type="portrait",  # Optional filtering
    min_ratings=10  # Minimum ratings for statistical significance
)
```

### 4. Implementation Components

#### A. Web Server (FastAPI)
```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import duckdb

app = FastAPI()

@app.get("/api/comparison/{session_id}")
async def get_comparison(session_id: str):
    """Get anonymized model outputs for comparison."""
    conn = duckdb.connect('alice.db')
    
    # Get session info
    session = conn.execute("""
        SELECT content_hash, models_compared 
        FROM comparison_sessions 
        WHERE session_id = ?
    """, [session_id]).fetchone()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Get model outputs (anonymized)
    outputs = conn.execute("""
        SELECT 
            model_id,
            description,
            tags,
            generated_prompt,
            negative_prompt
        FROM model_outputs
        WHERE content_hash = ?
        AND model_id = ANY(?)
    """, [session[0], session[1]]).fetchall()
    
    # Anonymize by shuffling and labeling as A, B, C...
    import random
    shuffled = list(outputs)
    random.shuffle(shuffled)
    
    return {
        "image_hash": session[0],
        "models": [
            {
                "label": chr(65 + i),  # A, B, C...
                "model_id": output[0],
                "description": output[1],
                "tags": json.loads(output[2]),
                "prompt": output[3],
                "negative": output[4]
            }
            for i, output in enumerate(shuffled)
        ]
    }

@app.post("/api/comparison/{session_id}/rate")
async def submit_ratings(session_id: str, ratings: dict):
    """Submit ratings for models."""
    # Store ratings and reveal true model identities
    pass
```

#### B. Model Selection Algorithm
```python
class SmartModelSelector:
    """Select models based on performance history."""
    
    def select_models(
        self, 
        image_path: Path,
        num_models: int = 2,
        strategy: str = "balanced"
    ) -> List[str]:
        """
        Select models for comparison based on strategy:
        - 'balanced': Mix of proven and experimental
        - 'explore': Try less-tested models
        - 'exploit': Use best-performing models
        - 'cost_optimized': Balance performance vs cost
        """
        
        # Get image characteristics
        media_type = self.detect_media_type(image_path)
        
        # Query historical performance
        conn = duckdb.connect('alice.db')
        
        if strategy == "balanced":
            # Get 1 top performer + 1 random/new model
            best = conn.execute("""
                SELECT provider || ':' || model_name as model
                FROM model_performance
                WHERE total_ratings >= 10
                ORDER BY avg_rating DESC
                LIMIT 1
            """).fetchone()[0]
            
            others = self.get_available_models()
            others.remove(best)
            random_model = random.choice(others)
            
            return [best, random_model]
            
        elif strategy == "cost_optimized":
            # Best value score (rating per dollar)
            return conn.execute("""
                SELECT provider || ':' || model_name as model
                FROM model_performance
                WHERE total_ratings >= 5
                ORDER BY value_score DESC
                LIMIT ?
            """, [num_models]).fetchall()
```

### 5. Benefits

1. **Data-Driven Model Selection**: Pick models based on actual performance
2. **Cost Optimization**: Identify models with best quality/cost ratio
3. **Continuous Improvement**: Models get better as more ratings accumulate
4. **Unbiased Comparison**: Blind testing prevents provider bias
5. **Domain-Specific Learning**: Learn which models excel at different image types

### 6. Future Enhancements

1. **Auto-Learning**: Automatically prefer high-rated models
2. **Category-Specific Rankings**: Best models for portraits vs landscapes
3. **Ensemble Decisions**: Combine outputs from top-rated models
4. **Active Learning**: Prioritize comparisons that maximize information gain
5. **Export Training Data**: Use ratings to fine-tune custom models

## Example Usage

```python
# From AI assistant
alice.compare_models(
    "cyberpunk-portrait.jpg",
    models=["auto"],  # Let system choose
    strategy="explore"  # Try newer models
)

# Returns link to web UI for rating

# Later, query performance
alice.show_model_rankings()
# Output:
# 1. Anthropic Claude 3.5: 8.7/10 (n=45, $0.003/image)
# 2. OpenAI GPT-4V: 8.2/10 (n=52, $0.001/image)  
# 3. DeepSeek: 7.9/10 (n=38, $0.0005/image) ← Best value!

# Auto-select best model for batch
alice.analyze_folder(
    "new_images/",
    model_selection="performance_based"
)