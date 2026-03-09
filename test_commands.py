#!/usr/bin/env python3
"""
Comprehensive Command Testing Suite
Tests all commands against the updated terminal engine logic
"""

import re
import json
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


class CommandTester:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}{text:^80}{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

    def print_section(self, text):
        """Print section header"""
        print(f"\n{BOLD}{BLUE}▶ {text}{RESET}")
        print(f"{BLUE}{'-'*80}{RESET}")

    def test_command(self, cmd, state, expected_patterns, description):
        """Test if a command matches expected patterns"""
        # Improved pattern matching (from app.py)
        is_recon = bool(re.search(r"(aws\s+s3\s+ls|enumerate|nmap|whois|dig|traceroute|find|grep|locate)", cmd, re.I))
        is_attack = bool(re.search(r"(aws\s+s3\s+(cp|sync|mv)|get-object|getobject|exploit|upload|access|download|retrieve|exfiltrate)", cmd, re.I))
        is_mitigate = bool(re.search(r"(put-public-access-block|block-public|put-bucket|revoke|fix|remediate|disable|deny|restrict|encrypt|enable|protect)", cmd, re.I))
        
        # Basic commands
        is_basic = bool(re.search(r"^(ls|pwd|whoami|uname|ifconfig|ipconfig)", cmd, re.I))
        
        matched_patterns = []
        if is_recon:
            matched_patterns.append("RECON")
        if is_attack:
            matched_patterns.append("ATTACK")
        if is_mitigate:
            matched_patterns.append("MITIGATION")
        if is_basic:
            matched_patterns.append("BASIC")

        # Determine if test passed
        matched = any(p in expected_patterns for p in matched_patterns)
        
        status = "✓ PASS" if matched else "✗ FAIL"
        color = GREEN if matched else RED
        
        if matched:
            self.passed += 1
        else:
            self.failed += 1
            
        self.test_results.append({
            'cmd': cmd,
            'state': state,
            'expected': expected_patterns,
            'matched': matched_patterns,
            'passed': matched,
            'description': description
        })
        
        print(f"{color}{status}{RESET} [{state:15s}] {cmd:50s}")
        print(f"     Description: {description}")
        print(f"     Expected: {', '.join(expected_patterns)}")
        if matched_patterns:
            print(f"     Matched:  {', '.join(matched_patterns)}")
        else:
            print(f"     {RED}No patterns matched!{RESET}")

    def test_recon_commands(self):
        """Test reconnaissance commands"""
        self.print_section("Reconnaissance Commands (Initial State)")
        
        recon_tests = [
            ("aws s3 ls", "initialized", ["RECON"], "List S3 buckets"),
            ("aws s3 ls s3://open-lab-public --recursive", "initialized", ["RECON"], "List bucket contents recursively"),
            ("aws s3 ls s3://bucket", "initialized", ["RECON"], "List specific bucket"),
            ("enumerate", "initialized", ["RECON"], "Enumerate resources"),
            ("nmap -sV 192.168.1.0/24", "initialized", ["RECON"], "Network scan with service detection"),
            ("nmap -A target.com", "initialized", ["RECON"], "Aggressive nmap scan"),
            ("whois example.com", "initialized", ["RECON"], "WHOIS lookup"),
            ("dig example.com", "initialized", ["RECON"], "DNS lookup"),
            ("traceroute example.com", "initialized", ["RECON"], "Traceroute to host"),
            ("find / -type f -name '*.config'", "initialized", ["RECON"], "Find configuration files"),
            ("grep -r 'password' /var/", "initialized", ["RECON"], "Search for sensitive patterns"),
            ("locate sensitive_file", "initialized", ["RECON"], "Locate files by name"),
            ("ls -la", "initialized", ["BASIC"], "List directory contents"),
            ("pwd", "initialized", ["BASIC"], "Print working directory"),
            ("whoami", "initialized", ["BASIC"], "Show current user"),
        ]
        
        for cmd, state, expected, desc in recon_tests:
            self.test_command(cmd, state, expected, desc)

    def test_attack_commands(self):
        """Test attack commands"""
        self.print_section("Attack Commands (After Reconnaissance)")
        
        attack_tests = [
            ("aws s3 cp s3://bucket/file ./file", "recon", ["ATTACK"], "Download single file from S3"),
            ("aws s3 cp s3://bucket/sensitive.txt ./", "recon", ["ATTACK"], "Copy sensitive data"),
            ("aws s3 sync s3://bucket ./download_data", "recon", ["ATTACK"], "Bulk download from S3"),
            ("aws s3 sync s3://backup-vault /tmp", "recon", ["ATTACK"], "Sync entire backup bucket"),
            ("get-object --bucket mybucket --key mykey", "recon", ["ATTACK"], "Get object from S3"),
            ("getobject bucket/key", "recon", ["ATTACK"], "Alternative get-object syntax"),
            ("exploit", "recon", ["ATTACK"], "Execute exploit"),
            ("upload malware.exe s3://bucket/", "recon", ["ATTACK"], "Upload malicious file"),
            ("access admin panel", "recon", ["ATTACK"], "Gain unauthorized access"),
            ("download sensitive_data.zip", "recon", ["ATTACK"], "Download sensitive data"),
            ("retrieve credentials", "recon", ["ATTACK"], "Retrieve credentials"),
            ("exfiltrate database", "recon", ["ATTACK"], "Exfiltrate data"),
        ]
        
        for cmd, state, expected, desc in attack_tests:
            self.test_command(cmd, state, expected, desc)

    def test_mitigation_commands(self):
        """Test mitigation/defense commands"""
        self.print_section("Mitigation Commands (Defense Phase)")
        
        mitigation_tests = [
            ("put-public-access-block --bucket mybucket", "attack_started", ["MITIGATION"], "Block public access"),
            ("aws s3api put-public-access-block --bucket secure-bucket", "attack_started", ["MITIGATION"], "AWS API public access block"),
            ("block-public", "attack_started", ["MITIGATION"], "Block public access (short form)"),
            ("put-bucket-policy --bucket secure --policy policy.json", "attack_started", ["MITIGATION"], "Set bucket policy"),
            ("revoke admin --from user", "attack_started", ["MITIGATION"], "Revoke permissions"),
            ("fix security", "attack_started", ["MITIGATION"], "Fix security issues"),
            ("remediate", "attack_started", ["MITIGATION"], "Apply remediation"),
            ("disable public-access", "attack_started", ["MITIGATION"], "Disable public access"),
            ("deny GetObject", "attack_started", ["MITIGATION"], "Deny object access"),
            ("restrict *", "attack_started", ["MITIGATION"], "Restrict all access"),
            ("encrypt --algorithm AES256", "attack_started", ["MITIGATION"], "Enable encryption"),
            ("enable logging", "attack_started", ["MITIGATION"], "Enable logging"),
            ("protect bucket", "attack_started", ["MITIGATION"], "Protect bucket"),
        ]
        
        for cmd, state, expected, desc in mitigation_tests:
            self.test_command(cmd, state, expected, desc)

    def test_basic_commands(self):
        """Test basic system commands"""
        self.print_section("Basic System Commands (All States)")
        
        basic_tests = [
            ("ls", "initialized", ["BASIC"], "List files (no options)"),
            ("ls -la", "initialized", ["BASIC"], "List files (long format)"),
            ("ls -l", "initialized", ["BASIC"], "List files (long)"),
            ("ls -a", "initialized", ["BASIC"], "List all files"),
            ("pwd", "initialized", ["BASIC"], "Print working directory"),
            ("whoami", "initialized", ["BASIC"], "Show current user"),
            ("uname -a", "initialized", ["BASIC"], "System information"),
            ("ifconfig", "recon", ["BASIC"], "Show network configuration"),
            ("ip addr", "recon", ["BASIC"], "Show IP addresses"),
            ("ipconfig", "attack_started", ["BASIC"], "Windows IP config"),
        ]
        
        for cmd, state, expected, desc in basic_tests:
            self.test_command(cmd, state, expected, desc)

    def test_invalid_commands(self):
        """Test that invalid commands are properly rejected"""
        self.print_section("Invalid Commands (Should Fail)")
        
        invalid_tests = [
            ("invalid command", "initialized", [], "Random invalid command"),
            ("xyz123", "recon", [], "Gibberish input"),
            ("rm -rf /", "attack_started", [], "Dangerous command not in patterns"),
        ]
        
        for cmd, state, expected, desc in invalid_tests:
            self.test_command(cmd, state, expected, desc)

    def test_command_variants(self):
        """Test command variations"""
        self.print_section("Command Variations (Case Sensitivity & Options)")
        
        variant_tests = [
            ("AWS S3 LS", "initialized", ["RECON"], "Uppercase command"),
            ("Aws S3 Ls", "initialized", ["RECON"], "Mixed case command"),
            ("aws s3 ls --profile default", "initialized", ["RECON"], "Command with options"),
            ("AWS S3 CP s3://bucket/file .", "recon", ["ATTACK"], "Uppercase attack command"),
            ("Put-Public-Access-Block", "attack_started", ["MITIGATION"], "Uppercase mitigation"),
        ]
        
        for cmd, state, expected, desc in variant_tests:
            self.test_command(cmd, state, expected, desc)

    def generate_report(self):
        """Generate test report"""
        self.print_header("TEST RESULTS SUMMARY")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"{BOLD}Results:{RESET}")
        print(f"  Total Tests:     {total}")
        print(f"  {GREEN}Passed:       {self.passed}{RESET}")
        print(f"  {RED}Failed:       {self.failed}{RESET}")
        print(f"  Success Rate:    {pass_rate:.1f}%\n")
        
        if self.failed > 0:
            print(f"{RED}Failed Tests:{RESET}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  • {result['cmd']}")
                    print(f"    Expected: {', '.join(result['expected'])}")
                    print(f"    Got: {', '.join(result['matched']) if result['matched'] else 'NO MATCH'}")
                    print()
        
        if pass_rate >= 90:
            print(f"{GREEN}✓ Command execution is working excellently!{RESET}")
        elif pass_rate >= 70:
            print(f"{YELLOW}⚠ Command execution is mostly working. Some edge cases need attention.{RESET}")
        else:
            print(f"{RED}✗ Many commands are not properly configured. Significant work needed.{RESET}")
        
        # Save results to JSON
        results_file = Path(__file__).parent / "test_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'passed': self.passed,
                    'failed': self.failed,
                    'total': total,
                    'pass_rate': pass_rate,
                    'results': self.test_results
                }, f, indent=2)
            print(f"\n{CYAN}Results saved to: {results_file}{RESET}")
        except Exception as e:
            print(f"{YELLOW}Warning: Could not save results: {e}{RESET}")

    def run(self):
        """Run all tests"""
        self.print_header("COMMAND EXECUTION TEST SUITE")
        print("Testing all command patterns against terminal engine logic\n")
        
        self.test_recon_commands()
        self.test_attack_commands()
        self.test_mitigation_commands()
        self.test_basic_commands()
        self.test_invalid_commands()
        self.test_command_variants()
        
        self.generate_report()
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}\n")


if __name__ == "__main__":
    tester = CommandTester()
    tester.run()
