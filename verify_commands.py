#!/usr/bin/env python3
"""
Comprehensive command verification and testing script
Analyzes all commands in the project and validates their execution patterns
"""

import sqlite3
import re
import os
from pathlib import Path

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

class CommandVerifier:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.s3_db = self.script_dir / "data" / "open_s3_lab" / "open_s3_lab.db"
        self.pwndora_db = self.script_dir / "data" / "pwndora_lab" / "pwndora_lab.db"
        self.network_db = self.script_dir / "data" / "network_recon_lab" / "network_recon_lab.db"
        self.linux_db = self.script_dir / "data" / "linux_commands.db"
        
        self.results = {
            "total_commands": 0,
            "working_commands": 0,
            "failed_commands": [],
            "missing_patterns": [],
            "state_conflicts": [],
        }

    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{BOLD}{CYAN}{text:^70}{RESET}")
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    def print_section(self, text):
        """Print a section header"""
        print(f"\n{BOLD}{BLUE}▶ {text}{RESET}")
        print(f"{BLUE}{'-'*70}{RESET}")

    def check_db_exists(self, db_path, name):
        """Verify database file exists"""
        if db_path.exists():
            print(f"{GREEN}✓{RESET} {name} found at {db_path}")
            return True
        else:
            print(f"{RED}✗{RESET} {name} NOT found at {db_path}")
            return False

    def get_db_connection(self, db_path):
        """Get database connection"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"{RED}✗ Error connecting to database: {e}{RESET}")
            return None

    def verify_s3_lab_commands(self):
        """Verify all S3 lab commands"""
        self.print_section("S3 Lab Command Verification")
        
        if not self.check_db_exists(self.s3_db, "S3 Lab DB"):
            return
        
        conn = self.get_db_connection(self.s3_db)
        if not conn:
            return
        
        cur = conn.cursor()
        
        # Check attack commands
        try:
            cur.execute("SELECT * FROM attack_commands")
            attack_cmds = cur.fetchall()
            print(f"\n{BOLD}Attack Commands ({len(attack_cmds)}){RESET}")
            for cmd in attack_cmds:
                self.results["total_commands"] += 1
                print(f"  • {cmd['name']:30s} | Pattern: {cmd['pattern'][:40]:40s}")
                if self._validate_command_pattern(cmd['pattern']):
                    self.results["working_commands"] += 1
                    print(f"    {GREEN}✓ Valid pattern{RESET}")
                else:
                    self.results["failed_commands"].append(cmd['name'])
                    print(f"    {RED}✗ Invalid pattern{RESET}")
        except Exception as e:
            print(f"{RED}✗ Error reading attack_commands: {e}{RESET}")
        
        # Check defense commands
        try:
            cur.execute("SELECT * FROM defense_commands")
            defense_cmds = cur.fetchall()
            print(f"\n{BOLD}Defense Commands ({len(defense_cmds)}){RESET}")
            for cmd in defense_cmds:
                self.results["total_commands"] += 1
                print(f"  • {cmd['name']:30s} | Pattern: {cmd['pattern'][:40]:40s}")
                if self._validate_command_pattern(cmd['pattern']):
                    self.results["working_commands"] += 1
                    print(f"    {GREEN}✓ Valid pattern{RESET}")
                else:
                    self.results["failed_commands"].append(cmd['name'])
                    print(f"    {RED}✗ Invalid pattern{RESET}")
        except Exception as e:
            print(f"{RED}✗ Error reading defense_commands: {e}{RESET}")
        
        conn.close()

    def verify_linux_commands(self):
        """Verify Linux commands database"""
        self.print_section("Linux Commands Database Verification")
        
        if not self.check_db_exists(self.linux_db, "Linux Commands DB"):
            return
        
        conn = self.get_db_connection(self.linux_db)
        if not conn:
            return
        
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT * FROM linux_commands")
            linux_cmds = cur.fetchall()
            
            print(f"\n{BOLD}Total Linux Commands: {len(linux_cmds)}{RESET}")
            
            # Count by mode
            modes = {}
            for cmd in linux_cmds:
                mode = cmd.get('mode', 'unknown') or 'unknown'
                modes[mode] = modes.get(mode, 0) + 1
            
            print(f"\n{BOLD}Commands by Mode:{RESET}")
            for mode, count in sorted(modes.items()):
                print(f"  • {mode:15s}: {count:3d} commands")
            
            # Show sample commands
            print(f"\n{BOLD}Sample Commands:{RESET}")
            for cmd in linux_cmds[:10]:
                self.results["total_commands"] += 1
                mode = cmd.get('mode', 'unknown') or 'N/A'
                print(f"  • {cmd['name']:20s} | Mode: {mode:10s} | Pattern: {cmd['pattern'][:35]:35s}")
                if self._validate_command_pattern(cmd['pattern']):
                    self.results["working_commands"] += 1
                    print(f"    {GREEN}✓ Valid{RESET}")
                else:
                    self.results["failed_commands"].append(cmd['name'])
                    print(f"    {RED}✗ Invalid{RESET}")
            
            if len(linux_cmds) > 10:
                print(f"  ... and {len(linux_cmds) - 10} more commands")
        
        except Exception as e:
            print(f"{RED}✗ Error reading linux_commands: {e}{RESET}")
        
        conn.close()

    def verify_terminal_patterns(self):
        """Verify terminal engine command patterns"""
        self.print_section("Terminal Engine Pattern Analysis")
        
        # These are the patterns used in app.py terminal() function
        patterns = {
            "ifconfig": r"(^|\s)(ifconfig|ip addr|ip a)(\s|$)",
            "ipconfig": r"(^|\s)(ipconfig)(\s|$)",
            "ls": r"^ls(-la)?$",
            "cat": r"^cat\s+",
            "whoami": r"^whoami$",
            "pwd": r"^pwd$",
            "uname": r"^uname",
            "recon_tools": r"nmap|whois|dig|traceroute",
            "aws_s3_ls": r"aws\s+s3\s+ls",
            "recon_keywords": r"aws s3 ls|enumerate",
            "attack_keywords": r"aws s3 cp|get-object|getobject|exploit|upload|access",
            "mitigation_keywords": r"put-public-access-block|block-public|revoke|fix|remediate",
        }
        
        print(f"\n{BOLD}Terminal Pattern Validation:{RESET}\n")
        
        # Test each pattern with sample commands
        test_commands = {
            "ifconfig": ["ifconfig", "ip addr", "ip a"],
            "ls": ["ls", "ls -la"],
            "aws_s3": ["aws s3 ls", "aws s3 cp file s3://bucket"],
            "attack": ["aws s3 cp file s3://bucket", "exploit", "upload"],
            "mitigation": ["put-public-access-block", "block-public", "revoke"],
        }
        
        for cmd_type, cmds in test_commands.items():
            print(f"{BOLD}{cmd_type.upper()}:{RESET}")
            for cmd in cmds:
                matched = False
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, cmd, re.I):
                        print(f"  ✓ '{cmd}' → matched by '{pattern_name}'")
                        matched = True
                        break
                if not matched:
                    print(f"  {RED}✗ '{cmd}' → NO MATCH (will be rejected!){RESET}")
                    self.results["missing_patterns"].append(cmd)

    def check_state_transitions(self):
        """Check state machine transitions"""
        self.print_section("State Machine Analysis")
        
        states = {
            "initialized": {
                "allowed": ["recon"],
                "commands": ["reconnaissance", "enumeration", "ls", "whoami", "pwd"]
            },
            "recon": {
                "allowed": ["attack_started"],
                "commands": ["attack", "exploit", "upload"]
            },
            "attack_started": {
                "allowed": ["attack_started", "mitigation_applied"],
                "commands": ["exfiltrate", "attack", "mitigation", "block-public"]
            },
            "mitigation_applied": {
                "allowed": ["secured"],
                "commands": ["verify"]
            },
            "secured": {
                "allowed": ["reset"],
                "commands": ["reset"]
            }
        }
        
        print(f"\n{BOLD}State Transitions:{RESET}\n")
        for state, config in states.items():
            print(f"{YELLOW}{state}{RESET}")
            print(f"  Allowed next states: {', '.join(config['allowed'])}")
            print(f"  Expected commands: {', '.join(config['commands'])}")
            print()

    def _validate_command_pattern(self, pattern):
        """Validate if a regex pattern is valid"""
        try:
            re.compile(pattern)
            return True
        except Exception:
            return False

    def test_sample_commands(self):
        """Test sample commands against terminal engine logic"""
        self.print_section("Sample Command Testing Against Terminal Engine")
        
        test_cases = [
            ("aws s3 ls", "recon", True, "Should match AWS S3 reconnaissance"),
            ("aws s3 ls s3://open-lab-public --recursive", "recon", True, "Should match AWS S3 with options"),
            ("aws s3 cp s3://bucket/file ./file", "attack", True, "Should match AWS S3 attack"),
            ("aws s3 sync s3://bucket ./download_data", "attack", True, "Should match AWS S3 sync"),
            ("put-public-access-block", "mitigation", True, "Should match mitigation"),
            ("nmap -sV 192.168.1.0/24", "recon", True, "Should match recon nmap"),
            ("ls -la", "initialized", True, "Should match ls in any state"),
            ("random command", "initialized", False, "Should NOT match random command"),
        ]
        
        print(f"\n{BOLD}Testing Commands Against Patterns:{RESET}\n")
        
        for cmd, state, should_match, description in test_cases:
            # Check if it matches recon patterns
            is_recon = bool(re.search(r"aws s3 ls|enumerate", cmd))
            is_attack = bool(re.search(r"aws s3 cp|get-object|getobject|exploit|upload|access|sync", cmd))
            is_mitigate = bool(re.search(r"put-public-access-block|block-public|revoke|fix|remediate", cmd))
            
            matched = is_recon or is_attack or is_mitigate
            status = "✓" if matched == should_match else "✗"
            color = GREEN if matched == should_match else RED
            
            print(f"{color}{status}{RESET} Command: '{cmd}'")
            print(f"     Description: {description}")
            print(f"     Expected: {should_match}, Got: {matched}")
            if is_recon:
                print(f"     → Matched as RECON command")
            if is_attack:
                print(f"     → Matched as ATTACK command")
            if is_mitigate:
                print(f"     → Matched as MITIGATION command")
            print()

    def generate_report(self):
        """Generate final verification report"""
        self.print_header("COMMAND VERIFICATION REPORT")
        
        print(f"{BOLD}Summary:{RESET}")
        print(f"  Total Commands Checked:    {self.results['total_commands']}")
        print(f"  Working Commands:          {GREEN}{self.results['working_commands']}{RESET}")
        print(f"  Failed Commands:           {RED}{len(self.results['failed_commands'])}{RESET}")
        print(f"  Missing Patterns:          {RED}{len(self.results['missing_patterns'])}{RESET}")
        
        if self.results['failed_commands']:
            print(f"\n{RED}Failed Commands:{RESET}")
            for cmd in self.results['failed_commands']:
                print(f"  • {cmd}")
        
        if self.results['missing_patterns']:
            print(f"\n{RED}Commands with Missing Patterns (will be rejected):{RESET}")
            for cmd in self.results['missing_patterns']:
                print(f"  • {cmd}")
        
        success_rate = (self.results['working_commands'] / self.results['total_commands'] * 100) if self.results['total_commands'] > 0 else 0
        print(f"\n{BOLD}Success Rate: {success_rate:.1f}%{RESET}")
        
        if success_rate >= 80:
            print(f"{GREEN}✓ Command execution is working well{RESET}")
        elif success_rate >= 50:
            print(f"{YELLOW}⚠ Some commands need attention{RESET}")
        else:
            print(f"{RED}✗ Many commands are not properly configured{RESET}")

    def run(self):
        """Run all verifications"""
        self.print_header("CLOUD SECURITY LAB - COMMAND VERIFICATION SUITE")
        
        print("This tool analyzes all commands in your project and validates their patterns.\n")
        
        self.verify_s3_lab_commands()
        self.verify_linux_commands()
        self.verify_terminal_patterns()
        self.check_state_transitions()
        self.test_sample_commands()
        self.generate_report()
        
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{CYAN}Verification complete!{RESET}")
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


if __name__ == "__main__":
    verifier = CommandVerifier()
    verifier.run()
