#!/usr/bin/env python3
"""
Verify S3 reconnaissance commands are properly stored and accessible.
"""

import sqlite3
import json

DB_PATH = "open_s3_lab.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("="*80)
print("S3 RECONNAISSANCE COMMANDS VERIFICATION REPORT")
print("="*80)

# Get all reconnaissance commands
cur.execute("""
    SELECT id, name, pattern, hint, example, level, category, description
    FROM attack_commands 
    WHERE category='Reconnaissance'
    ORDER BY level, id
""")

commands = cur.fetchall()

print(f"\nTotal Reconnaissance Commands: {len(commands)}\n")

# Group by level
levels = {}
for cmd in commands:
    level = cmd['level']
    if level not in levels:
        levels[level] = []
    levels[level].append(cmd)

# Display by level
for level in ['Beginner', 'Intermediate', 'Advanced']:
    if level in levels:
        print(f"\n{level.upper()} LEVEL ({len(levels[level])} commands)")
        print("-" * 80)
        for i, cmd in enumerate(levels[level], 1):
            print(f"\n{i}. {cmd['name']}")
            print(f"   Pattern: {cmd['pattern']}")
            print(f"   Hint: {cmd['hint']}")
            if cmd['example']:
                print(f"   Example: {cmd['example']}")

# Verify data completeness
print(f"\n\n{'='*80}")
print("DATA COMPLETENESS CHECK")
print("="*80)

missing_hints = 0
missing_examples = 0
missing_descriptions = 0

for cmd in commands:
    if not cmd['hint']:
        missing_hints += 1
    if not cmd['example']:
        missing_examples += 1
    if not cmd['description']:
        missing_descriptions += 1

print(f"\nHints: {len(commands) - missing_hints}/{len(commands)} populated")
print(f"Examples: {len(commands) - missing_examples}/{len(commands)} populated")
print(f"Descriptions: {len(commands) - missing_descriptions}/{len(commands)} populated")

if missing_hints == 0 and missing_examples == 0 and missing_descriptions == 0:
    print("\n✓ All fields are properly populated!")
else:
    if missing_hints > 0:
        print(f"\n⊘ Warning: {missing_hints} commands missing hints")
    if missing_examples > 0:
        print(f"⊘ Warning: {missing_examples} commands missing examples")
    if missing_descriptions > 0:
        print(f"⊘ Warning: {missing_descriptions} commands missing descriptions")

# Statistics
print(f"\n\n{'='*80}")
print("COMMAND STATISTICS")
print("="*80)

cur.execute("SELECT category, COUNT(*) as count FROM attack_commands GROUP BY category ORDER BY count DESC")
categories = cur.fetchall()

print("\nCommands by Category:")
for cat in categories:
    print(f"  {cat['category']}: {cat['count']}")

print(f"\nTotal Attack Commands: {sum(cat['count'] for cat in categories)}")

conn.close()
print(f"\n✓ Verification complete!")
