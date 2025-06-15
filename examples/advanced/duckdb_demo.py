#!/usr/bin/env python3
"""
DuckDB Demo for AliceMultiverse

This demonstrates how DuckDB's columnar storage and analytical capabilities
are perfect for our media search and organization needs.
"""

import json
from datetime import datetime
from pathlib import Path

import duckdb

# Create in-memory database for demo
conn = duckdb.connect(':memory:')

# Create our schema
conn.execute("""
    -- Main assets table with nested structures
    CREATE TABLE assets (
        -- Identity
        content_hash VARCHAR PRIMARY KEY,
        
        -- File locations (array of structs)
        locations STRUCT(
            name VARCHAR,
            path VARCHAR,
            type VARCHAR,
            last_verified TIMESTAMP
        )[],
        
        -- Core metadata
        media_type VARCHAR,
        file_size BIGINT,
        created_at TIMESTAMP,
        project VARCHAR,
        
        -- Nested tags structure
        tags STRUCT(
            style VARCHAR[],
            mood VARCHAR[],
            subject VARCHAR[],
            color VARCHAR[],
            technical VARCHAR[],
            fashion VARCHAR[],
            setting VARCHAR[]
        ),
        
        -- AI Understanding results
        understanding STRUCT(
            description TEXT,
            generated_prompt TEXT,
            negative_prompt TEXT,
            provider VARCHAR,
            model VARCHAR,
            cost DECIMAL(10,6),
            analyzed_at TIMESTAMP
        ),
        
        -- Embeddings for similarity search
        embedding FLOAT[],
        
        -- Full metadata as JSON for flexibility
        metadata JSON
    );
    
    -- Indexes for common queries
    CREATE INDEX idx_created ON assets(created_at);
    CREATE INDEX idx_project ON assets(project);
    CREATE INDEX idx_media_type ON assets(media_type);
""")

# Insert sample data
sample_assets = [
    {
        "content_hash": "sha256:abc123",
        "locations": [
            {"name": "primary", "path": "/organized/2024-01-01/project1/flux/image1.png", "type": "local", "last_verified": datetime.now()},
            {"name": "backup", "path": "s3://bucket/images/image1.png", "type": "s3", "last_verified": datetime.now()}
        ],
        "media_type": "image",
        "file_size": 2048000,
        "created_at": datetime.now(),
        "project": "cyberpunk-portraits",
        "tags": {
            "style": ["cyberpunk", "neon", "futuristic"],
            "mood": ["dramatic", "mysterious", "intense"],
            "subject": ["woman", "portrait", "close-up"],
            "color": ["blue", "purple", "neon"],
            "technical": ["high-contrast", "bokeh", "studio-lighting"],
            "fashion": ["leather-jacket", "sunglasses"],
            "setting": ["night", "urban", "rain"]
        },
        "understanding": {
            "description": "A dramatic cyberpunk portrait of a woman",
            "generated_prompt": "cyberpunk woman portrait, neon lights, dramatic lighting",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet",
            "cost": 0.003,
            "analyzed_at": datetime.now()
        }
    },
    {
        "content_hash": "sha256:def456",
        "locations": [
            {"name": "primary", "path": "/organized/2024-01-02/landscapes/midjourney/sunset.jpg", "type": "local", "last_verified": datetime.now()}
        ],
        "media_type": "image",
        "file_size": 3072000,
        "created_at": datetime.now(),
        "project": "landscapes",
        "tags": {
            "style": ["photorealistic", "cinematic", "golden-hour"],
            "mood": ["peaceful", "serene", "warm"],
            "subject": ["landscape", "mountains", "sunset"],
            "color": ["orange", "gold", "purple"],
            "technical": ["wide-angle", "hdr"],
            "setting": ["outdoor", "mountain", "sunset"]
        },
        "understanding": {
            "description": "A serene mountain landscape at sunset",
            "generated_prompt": "mountain landscape at golden hour, cinematic",
            "provider": "openai",
            "model": "gpt-4o",
            "cost": 0.001,
            "analyzed_at": datetime.now()
        }
    }
]

# Insert data
for asset in sample_assets:
    conn.execute("""
        INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        asset["content_hash"],
        asset["locations"],
        asset["media_type"],
        asset["file_size"],
        asset["created_at"],
        asset["project"],
        asset["tags"],
        asset["understanding"],
        None,  # embedding
        json.dumps(asset)  # full metadata
    ])

print("=== DuckDB Demo for AliceMultiverse ===\n")

# 1. Tag Search - Show how arrays work
print("1. Search for cyberpunk style images:")
result = conn.execute("""
    SELECT 
        content_hash,
        understanding.description,
        tags.style
    FROM assets
    WHERE list_contains(tags.style, 'cyberpunk')
""").fetchall()
for row in result:
    print(f"  - {row[0]}: {row[1]}")

# 2. Multi-tag search with OR
print("\n2. Search for dramatic OR mysterious mood:")
result = conn.execute("""
    SELECT 
        content_hash,
        tags.mood
    FROM assets
    WHERE list_contains(tags.mood, 'dramatic') 
       OR list_contains(tags.mood, 'mysterious')
""").fetchall()
for row in result:
    print(f"  - {row[0]}: {row[1]}")

# 3. Complex nested query
print("\n3. Find images with woman subject AND neon colors:")
result = conn.execute("""
    SELECT 
        content_hash,
        understanding.generated_prompt
    FROM assets
    WHERE list_contains(tags.subject, 'woman')
      AND list_contains(tags.color, 'neon')
""").fetchall()
for row in result:
    print(f"  - {row[0]}: {row[1]}")

# 4. Aggregation - cost by provider
print("\n4. Total cost by AI provider:")
result = conn.execute("""
    SELECT 
        understanding.provider,
        COUNT(*) as count,
        SUM(understanding.cost) as total_cost
    FROM assets
    GROUP BY understanding.provider
""").fetchall()
for row in result:
    print(f"  - {row[0]}: {row[1]} images, ${row[2]:.3f}")

# 5. Find files across locations
print("\n5. Files available in S3:")
result = conn.execute("""
    SELECT 
        content_hash,
        location.path
    FROM assets,
         UNNEST(locations) as location
    WHERE location.type = 's3'
""").fetchall()
for row in result:
    print(f"  - {row[0]}: {row[1]}")

# 6. Export to Parquet (for archival/sharing)
print("\n6. Export to Parquet:")
conn.execute("""
    COPY assets TO 'assets_export.parquet' (FORMAT PARQUET)
""")
print("  - Exported to assets_export.parquet")

# 7. Show how to query Parquet directly
print("\n7. Query Parquet file directly (no import needed):")
# This would work with real Parquet files
print("  - SELECT * FROM read_parquet('assets_export.parquet') WHERE ...")

# 8. Performance comparison
print("\n8. Why DuckDB is faster for our queries:")
print("  - Columnar storage: Only reads needed columns")
print("  - Native array support: No JSON parsing needed")
print("  - Vectorized execution: Processes data in batches")
print("  - Zero serialization: Direct memory access")

# 9. Future: Vector similarity search
print("\n9. Future vector search capability:")
print("  - Install: conn.install_extension('vss')")
print("  - Usage: ORDER BY array_distance(embedding, query_embedding)")

print("\n=== Key Benefits for AliceMultiverse ===")
print("- 10-100x faster tag searches than PostgreSQL")
print("- Can query S3/Parquet files directly")
print("- Single file deployment (or in-memory)")
print("- Perfect for read-heavy analytical workloads")
print("- Native support for our nested data structures")

# Cleanup
Path("assets_export.parquet").unlink(missing_ok=True)
