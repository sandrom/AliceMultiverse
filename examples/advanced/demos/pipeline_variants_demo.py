#!/usr/bin/env python3
"""Demonstrate the 4 pipeline variants."""

print("AliceMultiverse - 4 Pipeline Variants")
print("=" * 50)
print()

# Show the 4 main variants
variants = [
    ("brisque", "BRISQUE only", "$0.000", "Free local analysis"),
    ("brisque-sightengine", "BRISQUE + SightEngine", "$0.001", "Technical quality"),
    ("brisque-claude", "BRISQUE + Claude", "$0.002", "AI defect detection"),
    ("brisque-sightengine-claude", "BRISQUE + SightEngine + Claude", "$0.003", "Full analysis"),
]

print("The 4 Main Pipeline Variants:")
print("-" * 50)
for i, (cmd, name, cost, desc) in enumerate(variants, 1):
    print(f"{i}. {name:<30} {cost:<8} {desc}")
    print(f"   alice --pipeline {cmd}")
    print()

# Show aliases
print("\nConvenience Aliases:")
print("-" * 50)
aliases = [
    ("basic", "brisque"),
    ("standard", "brisque-sightengine"),
    ("premium", "brisque-sightengine-claude"),
    ("full", "brisque-sightengine-claude"),
]

for alias, actual in aliases:
    print(f"--pipeline {alias:<10} → --pipeline {actual}")

# Show cost breakdown
print("\n\nCost Breakdown Example (1000 images):")
print("-" * 50)
print("Typical quality distribution:")
print("  • 200 images (20%) = 1-2 stars")
print("  • 300 images (30%) = 3 stars")
print("  • 300 images (30%) = 4 stars")
print("  • 200 images (20%) = 5 stars")
print()

print("Pipeline costs:")
print("  1. brisque:                    $0.00  (all 1000 images)")
print("  2. brisque-sightengine:        $0.80  (800 images @ $0.001)")
print("  3. brisque-claude:             $1.00  (500 images @ $0.002)")
print("  4. brisque-sightengine-claude: $1.80  (800 @ $0.001 + 500 @ $0.002)")

# Command examples
print("\n\nExample Commands:")
print("-" * 50)

examples = [
    ("Test with free pipeline:", "alice inbox --pipeline brisque"),
    ("Add technical validation:", "alice inbox --pipeline brisque-sightengine"),
    ("Skip to AI defect detection:", "alice inbox --pipeline brisque-claude"),
    ("Full quality assessment:", "alice inbox --pipeline brisque-sightengine-claude"),
    ("With cost limit:", "alice inbox --pipeline brisque-sightengine-claude --cost-limit 10"),
    ("Dry run first:", "alice inbox --pipeline brisque-claude --dry-run"),
]

for desc, cmd in examples:
    print(f"{desc:<30} {cmd}")

print("\n✓ Use the pipeline that matches your quality needs and budget!")
