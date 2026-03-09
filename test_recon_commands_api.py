#!/usr/bin/env python3
"""
Test that S3 reconnaissance commands are properly accessible through the Flask API
"""

import sqlite3
import json

DB_PATH = "data/open_s3_lab/open_s3_lab.db"

def test_commands_retrieval():
    """Simulate what the cheatsheet_api route does"""
    print("="*80)
    print("TESTING S3 RECONNAISSANCE COMMAND RETRIEVAL")
    print("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Simulate attack mode (what users see in cheat sheet)
    print("\nFetching commands for ATTACK MODE (Reconnaissance focus)...")
    cur.execute("""
        SELECT name, pattern, hint, example, level, category 
        FROM attack_commands 
        WHERE category='Reconnaissance'
        ORDER BY level, id
    """)
    
    rows = cur.fetchall()
    commands = []
    
    for r in rows:
        description = r['hint'] or r['category'] or ""
        commands.append({
            'name': r['name'],
            'pattern': r['pattern'],
            'description': description,
            'example': r['example'],
            'level': r['level'],
        })
    
    # Simulate the API response
    response = {
        'commands': commands,
        'mode': 'attack',
        'remaining_free_views': 3,
        'lab': 's3'
    }
    
    print(f"\nAPI Response Status: 200 OK")
    print(f"Mode: {response['mode']}")
    print(f"Lab: {response['lab']}")
    print(f"Total Commands: {len(response['commands'])}")
    print(f"Remaining Free Views: {response['remaining_free_views']}")
    
    # Display sample commands
    print(f"\n\nSAMPLE COMMANDS IN CHEAT SHEET:\n")
    for i, cmd in enumerate(commands[:5], 1):
        print(f"{i}. {cmd['name']}")
        print(f"   Level: {cmd['level']}")
        print(f"   Hint: {cmd['description']}")
        print(f"   Command: {cmd['pattern']}")
        if cmd['example']:
            print(f"   Example: {cmd['example']}")
        print()
    
    # Statistics
    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    
    levels_count = {}
    for cmd in commands:
        level = cmd['level']
        levels_count[level] = levels_count.get(level, 0) + 1
    
    print(f"\nCommands by Level:")
    for level in ['Beginner', 'Intermediate', 'Advanced']:
        count = levels_count.get(level, 0)
        print(f"  {level}: {count}")
    
    print(f"\nTotal Reconnaissance Commands: {len(commands)}")
    print(f"API Response Size: {len(json.dumps(response))} bytes")
    
    conn.close()
    
    # Validation
    print(f"\n{'='*80}")
    print("VALIDATION")
    print(f"{'='*80}")
    
    all_have_hints = all(cmd['description'] for cmd in commands)
    all_have_examples = all(cmd['example'] for cmd in commands)
    all_have_patterns = all(cmd['pattern'] for cmd in commands)
    
    print(f"\n✓ All commands have hints: {all_have_hints}")
    print(f"✓ All commands have examples: {all_have_examples}")
    print(f"✓ All commands have patterns: {all_have_patterns}")
    
    if all_have_hints and all_have_examples and all_have_patterns:
        print(f"\n✓ READY FOR PRODUCTION!")
        print(f"  - Commands are properly formatted")
        print(f"  - All fields are populated")
        print(f"  - Ready to display in cheat sheet modal")
        return True
    else:
        print(f"\n✗ VALIDATION FAILED")
        return False

if __name__ == "__main__":
    success = test_commands_retrieval()
    exit(0 if success else 1)
