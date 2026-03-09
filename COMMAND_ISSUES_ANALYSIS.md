# Command Execution Issues - Analysis & Solutions

## Problems Identified

### 1. **Pattern Matching Issues**
- ❌ `ls -la` is not recognized (only `ls` without arguments is recognized)
- ❌ `nmap -sV` with options not properly matched
- ⚠️ Need to update regex patterns to handle command options/flags

### 2. **State Machine Constraints**
The terminal engine enforces a strict state flow:
```
initialized → recon → attack_started → mitigation_applied → secured
```

Current behavior causes "Command not recognized" when:
- You try to run attack commands before reconnaissance
- Pattern doesn't match exactly due to missing flags in regex
- State validation is too strict

### 3. **Root Cause of "Command not recognized for current stage"**
Looking at line 1195 in app.py:
```python
else:
    append_output("Command not recognized for current stage. Try reconnaissance commands first.")
```

This happens when:
1. Command doesn't match any of the hardcoded patterns in the terminal engine
2. Command doesn't match attack/recon/mitigation keywords
3. The state machine rejects it

### 4. **Command Pattern Gaps**
- `aws s3 sync` - SHOULD match as attack but the keyword check is incomplete
- `ls -la` - NOT recognized in terminal engine (only plain `ls`)
- Long AWS commands with multiple options may not match

### 5. **Linux Commands Database Issue**
- 61 Linux commands stored but missing 'mode' column integration
- Some queries fail due to missing `.get()` method usage for Row objects

## Solutions to Implement

### A. Fix Terminal Engine Pattern Matching
✅ Enhance regex patterns to handle commands with options
✅ Improve keyword matching for AWS CLI commands
✅ Add missing command patterns

### B. Improve State Machine Flexibility
✅ Add mode to state transitions
✅ Allow some commands in multiple states
✅ Add debugging output

### C. Fix Database Integration
✅ Properly handle sqlite3.Row objects
✅ Add mode column to linux_commands if missing
✅ Improve error handling

### D. Create Testing Framework
✅ Verify each command pattern works
✅ Test state transitions
✅ Validate command execution flow

## Files Needing Changes
1. **app.py** - Terminal engine pattern matching and state handling
2. **templates/terminal.html** - Error message display improvements
3. **data/linux_commands.db** - Add mode column if missing

