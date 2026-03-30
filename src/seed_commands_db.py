#!/usr/bin/env python3
"""
seed_commands_db.py
====================
Seeds all lab databases with structured command datasets:
  CMD001 - Linux Commands  (jeevanlal/linux-commands-dataset)
  CMD002 - Cyber Security  (thedevastator/cybersecurity-commands-dataset)
  CMD003 - Pentest/Kali    (sourabhshahane/penetration-testing-commands)
  CMD004 - AWS CLI         (prashant111/aws-cli-commands)

[WARN]  IMPORTANT: Commands are used ONLY for:
    [OK] terminal output / simulation
    [OK] hint generation
    [OK] AI analysis context
    [NO] NEVER for task completion (tasks only complete via /api/submit_task answer check)

Run:
    python src/seed_commands_db.py
"""
import sqlite3
import os
import sys

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S3_DB       = os.path.join(BASE_DIR, "data", "open_s3_lab",    "open_s3_lab.db")
NET_DB      = os.path.join(BASE_DIR, "data", "network_recon_lab", "network_recon_lab.db")
LINUX_DB    = os.path.join(BASE_DIR, "data", "linux_commands.db")

# -----------------------------------------------------------------------------
# CMD001: Linux Commands  (terminal simulation basics)
# -----------------------------------------------------------------------------
LINUX_COMMANDS = [
    # (name, category, pattern, description, example, level, source)
    ("ls",        "File",    "ls -lah [dir]",           "List directory contents with permissions", "ls -lah /home",       "Beginner",     "CMD001"),
    ("cat",       "File",    "cat [file]",               "Print file contents to terminal",          "cat /etc/passwd",     "Beginner",     "CMD001"),
    ("find",      "File",    "find [path] -name [pat]",  "Search files by name/pattern recursively", "find /var -name '*.log'","Intermediate","CMD001"),
    ("grep",      "File",    "grep -r [pattern] [path]", "Search text inside files",                 "grep -r 'admin' /etc","Intermediate", "CMD001"),
    ("chmod",     "Perms",   "chmod 755 [file]",         "Change file permissions",                  "chmod 644 config.txt","Intermediate", "CMD001"),
    ("chown",     "Perms",   "chown user:group [file]",  "Change file ownership",                    "chown www-data /var/www","Intermediate","CMD001"),
    ("ps",        "Process", "ps aux | grep [proc]",     "List running processes",                   "ps aux | grep nginx", "Intermediate", "CMD001"),
    ("kill",      "Process", "kill -9 [PID]",            "Terminate a process by PID",               "kill -9 1234",        "Intermediate", "CMD001"),
    ("netstat",   "Network", "netstat -tulpn",           "Show listening ports and connections",      "netstat -tulpn | grep LISTEN","Intermediate","CMD001"),
    ("lsof",      "Network", "lsof -i :[port]",          "List processes using a network port",       "lsof -i :443",        "Intermediate", "CMD001"),
    ("ssh",       "Network", "ssh -i [key] user@[host]", "Secure shell remote login",                "ssh -i id_rsa admin@192.168.1.1","Intermediate","CMD001"),
    ("scp",       "Network", "scp -r [src] [dst]",       "Secure copy files between hosts",          "scp user@host:/data .", "Intermediate","CMD001"),
    ("curl",      "Network", "curl -v [url]",            "Transfer data from/to a URL",              "curl -v https://api.example.com","Beginner","CMD001"),
    ("wget",      "Network", "wget -r [url]",            "Download files from the web",              "wget https://example.com/file","Beginner","CMD001"),
    ("whoami",    "System",  "whoami",                   "Print current user name",                  "whoami",              "Beginner",     "CMD001"),
    ("id",        "System",  "id [user]",                "Show user/group IDs and groups",           "id root",             "Beginner",     "CMD001"),
    ("uname",     "System",  "uname -a",                 "Print kernel and OS information",          "uname -a",            "Beginner",     "CMD001"),
    ("df",        "System",  "df -h",                    "Show disk usage of filesystems",           "df -h /",             "Beginner",     "CMD001"),
    ("free",      "System",  "free -h",                  "Display RAM and swap usage",               "free -h",             "Beginner",     "CMD001"),
    ("tail",      "Log",     "tail -f [file]",           "Follow log file in real-time",             "tail -f /var/log/syslog","Beginner",  "CMD001"),
    ("head",      "Log",     "head -n 20 [file]",        "Show first N lines of a file",             "head -n 50 /var/log/auth.log","Beginner","CMD001"),
    ("awk",       "Text",    "awk '{print $1}' [file]",  "Process and extract text columns",         "awk '{print $1}' access.log","Advanced","CMD001"),
    ("sed",       "Text",    "sed 's/old/new/g' [file]", "Stream editor for text replacement",       "sed 's/password/XXX/g' cfg","Advanced", "CMD001"),
    ("tar",       "Archive", "tar -czf [out] [dir]",     "Create compressed tar archive",            "tar -czf backup.tgz /home","Intermediate","CMD001"),
    ("sha256sum", "Security","sha256sum [file]",          "Compute SHA-256 hash of a file",           "sha256sum file.iso",  "Intermediate", "CMD001"),
    ("openssl",   "Security","openssl s_client -connect [h:p]","Test TLS/SSL connection",            "openssl s_client -connect example.com:443","Advanced","CMD001"),
    ("crontab",   "System",  "crontab -l",               "List scheduled cron jobs",                 "crontab -l",          "Intermediate", "CMD001"),
    ("journalctl","Log",     "journalctl -u [svc] -n 50","Query systemd journal logs",               "journalctl -u ssh -n 20","Intermediate","CMD001"),
    ("last",      "Log",     "last -n 20",               "Show recent login history",                "last -n 20",          "Beginner",     "CMD001"),
    ("env",       "System",  "env",                      "Print all environment variables",          "env | grep PATH",     "Beginner",     "CMD001"),
]

# -----------------------------------------------------------------------------
# CMD002: Cyber Security Commands
# -----------------------------------------------------------------------------
CYBER_ATTACK_CMDS = [
    # (name, pattern, hint, example, level, category, description, expected_output)
    ("nmap-sV",      "nmap -sV [target]",
     "Version scan: detects service versions on open ports",
     "nmap -sV 192.168.1.100",
     "Beginner", "Recon",
     "Identify services running on target (SSH, HTTP, MySQL, etc.)",
     "PORT STATE SERVICE VERSION\n22/tcp open ssh OpenSSH 8.2p1"),

    ("nmap-full",    "nmap -sC -sV -p- [target]",
     "Full port + script scan: finds all open ports with detailed info",
     "nmap -sC -sV -p- 192.168.1.100",
     "Intermediate", "Recon",
     "Comprehensive scan of all 65535 ports with version and default scripts",
     "Starting Nmap – 65535 ports scanned"),

    ("nmap-os",      "nmap -O [target]",
     "OS detection: fingerprints the target operating system",
     "nmap -O 192.168.1.100",
     "Intermediate", "Recon",
     "Detect the OS running on the target machine",
     "OS: Linux 5.x"),

    ("nmap-stealth", "nmap -sS [target]",
     "Stealth SYN scan: half-open connections to avoid detection",
     "nmap -sS 192.168.1.0/24",
     "Advanced", "Recon",
     "Perform stealthy port scan without completing TCP handshake",
     "Host is up – ports discovered"),

    ("sqlmap-basic", "sqlmap -u [url] --dbs",
     "Auto SQL injection: discovers databases on vulnerable URL",
     "sqlmap -u 'http://target/page?id=1' --dbs",
     "Intermediate", "Exploit",
     "Automatically detect and exploit SQL injection vulnerabilities",
     "available databases: [information_schema, webapp_db]"),

    ("nikto",        "nikto -h [target]",
     "Web vulnerability scanner: checks for common web server misconfigs",
     "nikto -h http://192.168.1.100",
     "Beginner", "Recon",
     "Scan web server for known vulnerabilities and misconfigurations",
     "Server: Apache/2.4.41 – CGI dirs found"),

    ("hydra-ssh",    "hydra -l [user] -P [wordlist] ssh://[target]",
     "Brute-force SSH: tries passwords from a wordlist",
     "hydra -l admin -P rockyou.txt ssh://192.168.1.100",
     "Advanced", "Exploit",
     "Brute-force SSH credentials using a password list",
     "[22][ssh] host: 192.168.1.100 login: admin password: password123"),

    ("hydra-http",   "hydra -l [user] -P [wordlist] http-post-form '[url]'",
     "Brute-force HTTP login form",
     "hydra -l admin -P list.txt http-post-form '/login:user=^USER^&pass=^PASS^:Invalid'",
     "Advanced", "Exploit",
     "Crack web application login credentials",
     "[80][http-post-form] login found"),

    ("john",         "john --wordlist=[wordlist] [hashfile]",
     "John the Ripper: crack password hashes",
     "john --wordlist=rockyou.txt hashes.txt",
     "Intermediate", "Exploit",
     "Crack password hashes using dictionary attacks",
     "password123 (admin)"),

    ("tcpdump",      "tcpdump -i [iface] -w [file.pcap]",
     "Capture network packets to a file for later analysis",
     "tcpdump -i eth0 -w capture.pcap",
     "Intermediate", "Recon",
     "Sniff and record all network traffic on an interface",
     "Capturing on eth0 – packets captured"),

    ("metasploit",   "msfconsole",
     "Launch Metasploit Framework for exploit development and execution",
     "msfconsole -q",
     "Advanced", "Exploit",
     "Open the Metasploit penetration testing framework",
     "msf6 >"),

    ("msfvenom",     "msfvenom -p [payload] LHOST=[ip] LPORT=[port] -f [format]",
     "Generate malicious payloads for exploitation",
     "msfvenom -p linux/x86/shell_reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f elf",
     "Advanced", "Exploit",
     "Create custom shellcode or executable payloads",
     "Payload size: 68 bytes"),

    ("netcat-listen","nc -lvp [port]",
     "Start a Netcat listener to receive reverse shell connections",
     "nc -lvp 4444",
     "Intermediate", "Exploit",
     "Open a listening port to catch reverse shell connections",
     "Listening on 0.0.0.0 4444"),

    ("gobuster",     "gobuster dir -u [url] -w [wordlist]",
     "Directory bruteforce: discover hidden directories and files",
     "gobuster dir -u http://192.168.1.100 -w /usr/share/wordlists/dirb/common.txt",
     "Intermediate", "Recon",
     "Find hidden paths on web servers",
     "/admin (Status: 200) /login (Status: 200)"),

    ("wfuzz",        "wfuzz -c -z file,[wordlist] [url]/FUZZ",
     "Web fuzzer: discover hidden endpoints by brute-force",
     "wfuzz -c -z file,common.txt http://target/FUZZ",
     "Advanced", "Recon",
     "Fuzz URL paths to find hidden admin panels or APIs",
     "200 responses found"),

    ("enum4linux",   "enum4linux -a [target]",
     "Enumerate Samba shares, users, and groups on Windows/Linux",
     "enum4linux -a 192.168.1.100",
     "Intermediate", "Recon",
     "Gather information from Windows/Samba hosts",
     "Users: admin, guest – Shares: public, admin$"),
]

CYBER_DEFENSE_CMDS = [
    ("iptables-block","iptables -A INPUT -s [ip] -j DROP",
     "Block a specific IP address using iptables firewall",
     "iptables -A INPUT -s 203.0.113.1 -j DROP",
     "Intermediate", "Firewall",
     "Block malicious IP from accessing the system",
     "Rule added – traffic from IP dropped"),

    ("iptables-list","iptables -L -n -v",
     "List all current firewall rules with statistics",
     "iptables -L -n -v",
     "Beginner", "Firewall",
     "Review all active iptables rules",
     "Chain INPUT (policy ACCEPT)"),

    ("ufw-enable",   "ufw enable",
     "Enable UFW firewall (Ubuntu/Debian default firewall)",
     "ufw enable",
     "Beginner", "Firewall",
     "Activate the Uncomplicated Firewall",
     "Firewall is active and enabled on system startup"),

    ("ufw-deny",     "ufw deny [port]",
     "Block a specific port with UFW",
     "ufw deny 22",
     "Beginner", "Firewall",
     "Prevent incoming connections on a port",
     "Rule added"),

    ("fail2ban",     "fail2ban-client status",
     "Check fail2ban status and banned IPs",
     "fail2ban-client status sshd",
     "Intermediate", "IDS",
     "Review automatic brute-force protection",
     "Banned IP list: 203.0.113.9"),

    ("wireshark-tshark","tshark -i [iface] -Y [filter]",
     "Capture and filter packets with TShark (CLI Wireshark)",
     "tshark -i eth0 -Y 'http.request'",
     "Advanced", "Monitoring",
     "Analyse network traffic for anomalies",
     "HTTP GET requests captured"),

    ("snort",        "snort -A console -i [iface] -c [config]",
     "Run Snort IDS to detect intrusion attempts",
     "snort -A console -i eth0 -c /etc/snort/snort.conf",
     "Advanced", "IDS",
     "Monitor traffic for known attack signatures",
     "ALERT tcp $EXTERNAL_NET any -> $HOME_NET 22"),

    ("aide-check",   "aide --check",
     "Run AIDE file integrity checker to detect changes",
     "aide --check",
     "Advanced", "Integrity",
     "Detect unauthorised file modifications",
     "File: /etc/passwd – MD5 changed"),

    ("chkrootkit",   "chkrootkit",
     "Scan for installed rootkits",
     "chkrootkit",
     "Intermediate", "Forensics",
     "Detect common rootkit infection patterns",
     "not infected / INFECTED"),

    ("lynis-audit",  "lynis audit system",
     "Run Lynis security audit on the system",
     "lynis audit system",
     "Intermediate", "Audit",
     "Perform a full security hardening assessment",
     "Hardening index: 65 [##########]"),

    ("openssl-cert", "openssl x509 -in [cert] -noout -text",
     "Inspect SSL certificate details",
     "openssl x509 -in server.crt -noout -text",
     "Intermediate", "Crypto",
     "View certificate validity, issuer, and SANs",
     "Validity: Not After: Dec 31 2025"),

    ("gpg-encrypt",  "gpg --encrypt -r [recipient] [file]",
     "Encrypt a file for a specific recipient using GPG",
     "gpg --encrypt -r admin@example.com secrets.txt",
     "Intermediate", "Crypto",
     "Securely encrypt sensitive data using asymmetric cryptography",
     "secrets.txt.gpg created"),

    ("auditctl",     "auditctl -l",
     "List active Linux audit rules",
     "auditctl -l",
     "Advanced", "Audit",
     "Review kernel-level audit logging rules",
     "-a always,exit -F arch=b64 -S execve"),

    ("logwatch",     "logwatch --detail high --mailto [email]",
     "Generate daily system log summary report",
     "logwatch --detail high",
     "Intermediate", "Monitoring",
     "Review security events from system logs",
     "Logwatch report for hostname"),
]

# -----------------------------------------------------------------------------
# CMD003: Pentest / Kali / Network Commands (for network_recon_lab)
# -----------------------------------------------------------------------------
PENTEST_ATTACK_CMDS = [
    ("nmap-ping",    "nmap -sn [subnet]",
     "Ping sweep: discover live hosts on a subnet",
     "nmap -sn 192.168.1.0/24",
     "Beginner", "Discovery",
     "Find which hosts are online without port scanning",
     "Host is up – 192.168.1.100, 192.168.1.1"),

    ("nmap-udp",     "nmap -sU [target]",
     "UDP scan: detect open UDP services (DNS, SNMP, etc.)",
     "nmap -sU 192.168.1.100",
     "Intermediate", "Discovery",
     "Find services running over UDP protocol",
     "53/udp open domain\n161/udp open snmp"),

    ("nmap-vuln",    "nmap --script vuln [target]",
     "Run Nmap vulnerability scripts against target",
     "nmap --script vuln 192.168.1.100",
     "Intermediate", "Vuln Scan",
     "Detect known vulnerabilities using NSE scripts",
     "VULNERABLE: MS17-010 EternalBlue"),

    ("masscan",      "masscan [subnet] -p[ports] --rate=1000",
     "Ultra-fast port scanner – faster than nmap",
     "masscan 192.168.1.0/24 -p1-1000 --rate=1000",
     "Advanced", "Discovery",
     "Scan large ranges quickly for open ports",
     "Discovered open port 22 on 192.168.1.100"),

    ("aircrack",     "aircrack-ng [cap-file] -w [wordlist]",
     "Crack WPA/WPA2 WiFi password from captured handshake",
     "aircrack-ng capture.cap -w rockyou.txt",
     "Advanced", "WiFi",
     "Recover wireless network password from a capture file",
     "KEY FOUND! [ password123 ]"),

    ("airodump",     "airodump-ng [iface]",
     "Monitor WiFi traffic and capture WPA handshakes",
     "airodump-ng wlan0mon",
     "Advanced", "WiFi",
     "Scan nearby wireless networks and capture packets",
     "BSSID: AA:BB:CC:DD:EE:FF – ESSID: TargetNetwork"),

    ("wireshark",    "wireshark -i [iface] -k",
     "Launch Wireshark GUI packet capture and analysis",
     "wireshark -i eth0 -k",
     "Intermediate", "Traffic",
     "Capture and inspect network packets visually",
     "Wireshark GUI opened – capturing"),

    ("dig-axfr",     "dig @[dns-server] [domain] AXFR",
     "DNS zone transfer: dump all DNS records from a server",
     "dig @dns.example.com example.com AXFR",
     "Advanced", "Recon",
     "Extract all subdomains via DNS zone transfer misconfiguration",
     "mail.example.com IN A 10.0.0.10"),

    ("dnsenum",      "dnsenum [domain]",
     "Enumerate DNS records and subdomains",
     "dnsenum example.com",
     "Intermediate", "Recon",
     "Find DNS information, subdomains and zone transfer attempts",
     "Found 5 subdomains"),

    ("hping3",       "hping3 -S --flood -p [port] [target]",
     "Send custom TCP/UDP packets; can simulate DoS",
     "hping3 -S --flood -p 80 192.168.1.100",
     "Advanced", "DoS",
     "Test target resilience with high-rate SYN packets",
     "HPING 192.168.1.100: S set, 40 headers + 0 data bytes"),

    ("msfconsole-use","use exploit/[module]",
     "Select an exploit module in Metasploit",
     "use exploit/windows/smb/ms17_010_eternalblue",
     "Advanced", "Exploit",
     "Load a specific exploit module in Metasploit Framework",
     "msf6 exploit(ms17_010_eternalblue) >"),

    ("searchsploit", "searchsploit [term]",
     "Search offline Exploit-DB for known exploits",
     "searchsploit apache 2.4",
     "Intermediate", "Research",
     "Find public exploits for a given service/version",
     "Apache 2.4.49 – Remote Code Execution"),

    ("proxychains",  "proxychains [command]",
     "Route traffic through proxy chains (Tor, SOCKS5)",
     "proxychains nmap -sT 192.168.1.100",
     "Advanced", "Evasion",
     "Anonymise scanning traffic through proxy servers",
     "ProxyChains – tunnelled connection"),

    ("crunch",       "crunch [min] [max] [chars] -o [file]",
     "Generate custom wordlists for brute-force attacks",
     "crunch 6 8 abc123 -o wordlist.txt",
     "Intermediate", "Wordlist",
     "Create targeted password dictionaries",
     "Wordlist generated: 500,000 words"),

    ("hashcat",      "hashcat -m [mode] [hashfile] [wordlist]",
     "GPU-accelerated password hash cracker",
     "hashcat -m 1000 hashes.txt rockyou.txt",
     "Advanced", "Crack",
     "Crack NTLM, MD5, SHA hashes at high speed",
     "Status: Cracked – Password: admin123"),
]

PENTEST_DEFENSE_CMDS = [
    ("nmap-firewall-test","nmap -sA [host]",
     "ACK scan to test firewall rule filtering",
     "nmap -sA 192.168.1.1",
     "Intermediate", "Firewall",
     "Determine which ports are filtered by a firewall",
     "filtered ports vs unfiltered"),

    ("tcpdump-filter","tcpdump -i [iface] 'tcp[tcpflags] & (tcp-syn) != 0'",
     "Capture SYN packets to detect port scans",
     "tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'",
     "Advanced", "Monitoring",
     "Detect incoming port scan activity",
     "SYN flood detected from 203.0.113.9"),

    ("ss",           "ss -tulpn",
     "Show socket statistics – faster than netstat",
     "ss -tulpn | grep LISTEN",
     "Beginner", "Monitoring",
     "List all listening sockets and owning processes",
     "tcp LISTEN 0 128 0.0.0.0:22"),

    ("nftables",     "nft list ruleset",
     "List all nftables firewall rules",
     "nft list ruleset",
     "Advanced", "Firewall",
     "View nftables-based firewall configuration",
     "table inet filter { chain input { ... } }"),

    ("psad",         "psad --Status",
     "Port Scan Attack Detector – scan status",
     "psad --Status",
     "Advanced", "IDS",
     "Check if PSAD has detected port scans",
     "Danger level: 5 – Attacker: 203.0.113.9"),

    ("rkhunter",     "rkhunter --check",
     "Scan for rootkits, backdoors and local exploits",
     "rkhunter --check",
     "Intermediate", "Forensics",
     "Detect hidden rootkit infections",
     "Checking for rootkits... none found"),

    ("tripwire",     "tripwire --check",
     "File integrity monitor – detect file changes",
     "tripwire --check",
     "Advanced", "Integrity",
     "Identify modified system files since last baseline",
     "Modified: /bin/ls – suspect tampering"),

    ("apparmor",     "aa-status",
     "Show AppArmor profiles and enforcement status",
     "aa-status",
     "Intermediate", "Hardening",
     "Check application sandboxing status",
     "34 profiles in enforce mode"),

    ("selinux",      "sestatus",
     "Check SELinux status and policy",
     "sestatus",
     "Intermediate", "Hardening",
     "Verify SELinux is enforcing mandatory access control",
     "SELinux status: enabled – Mode: Enforcing"),

    ("netfilter",    "iptables -A INPUT -p tcp --dport [port] -j REJECT",
     "Reject TCP connections on a specific port",
     "iptables -A INPUT -p tcp --dport 445 -j REJECT",
     "Intermediate", "Firewall",
     "Block SMB/NetBIOS port to prevent lateral movement",
     "Rule added – port 445 now rejected"),
]

# -----------------------------------------------------------------------------
# CMD004: AWS CLI Commands (for open_s3_lab)
# -----------------------------------------------------------------------------
AWS_ATTACK_CMDS = [
    ("aws-s3-ls",          "aws s3 ls",
     "List all S3 buckets in the current AWS account",
     "aws s3 ls",
     "Beginner", "S3 Recon",
     "Enumerate S3 buckets to identify targets",
     "2024-01-15 10:23:45 monish-s3-lab\n2024-01-15 10:25:12 open-lab-public"),

    ("aws-s3-ls-bucket",  "aws s3 ls s3://[bucket]",
     "List all objects inside a specific S3 bucket",
     "aws s3 ls s3://open-lab-public",
     "Beginner", "S3 Recon",
     "Enumerate files inside a bucket – look for sensitive data",
     "102400 credentials.csv\n245760 database_backup.sql"),

    ("aws-s3-ls-recursive","aws s3 ls s3://[bucket] --recursive",
     "Recursively list all objects in a bucket including subdirectories",
     "aws s3 ls s3://open-lab-public --recursive",
     "Intermediate", "S3 Recon",
     "Discover hidden files in nested bucket paths",
     "data/internal/secrets.json"),

    ("aws-s3-cp",          "aws s3 cp s3://[bucket]/[key] ./",
     "Download a file from S3 bucket to local machine",
     "aws s3 cp s3://open-lab-public/credentials.csv ./credentials.csv",
     "Beginner", "S3 Exploit",
     "Exfiltrate sensitive files from a public bucket",
     "download: s3://open-lab-public/credentials.csv to ./credentials.csv"),

    ("aws-s3-sync",        "aws s3 sync s3://[bucket] ./[dir]",
     "Download the entire contents of a bucket",
     "aws s3 sync s3://open-lab-public ./stolen-data",
     "Intermediate", "S3 Exploit",
     "Mass-download all bucket contents for offline analysis",
     "download: s3://bucket/file1.csv ..."),

    ("aws-s3api-acl",     "aws s3api get-bucket-acl --bucket [name]",
     "Check bucket ACL – reveals if public access is granted",
     "aws s3api get-bucket-acl --bucket open-lab-public",
     "Intermediate", "S3 Recon",
     "Identify over-permissive bucket ACLs",
     '{"Grantee":{"Type":"Group","URI":"AllUsers"},"Permission":"READ"}'),

    ("aws-s3api-policy",  "aws s3api get-bucket-policy --bucket [name]",
     "Retrieve the bucket policy JSON document",
     "aws s3api get-bucket-policy --bucket open-lab-public",
     "Intermediate", "S3 Recon",
     "Read the bucket resource policy for permission misconfigurations",
     '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*"}]}'),

    ("aws-s3api-head",    "aws s3api head-bucket --bucket [name]",
     "Check if a bucket exists and is accessible",
     "aws s3api head-bucket --bucket open-lab-public",
     "Beginner", "S3 Recon",
     "Verify bucket existence without listing contents",
     "HTTP 200 – bucket accessible"),

    ("aws-sts-identity",  "aws sts get-caller-identity",
     "Get the identity of the current AWS credentials",
     "aws sts get-caller-identity",
     "Beginner", "IAM Recon",
     "Identify what account/role the leaked credentials belong to",
     '{"Account":"123456789012","Arn":"arn:aws:iam::123456789012:user/attacker"}'),

    ("aws-iam-users",     "aws iam list-users",
     "List all IAM users in the AWS account",
     "aws iam list-users",
     "Intermediate", "IAM Recon",
     "Enumerate user accounts to find privilege escalation paths",
     "Users: admin, developer, readonly-svc"),

    ("aws-configure",     "aws configure",
     "Set up AWS CLI with access key, secret, and region",
     "aws configure",
     "Beginner", "Setup",
     "Configure AWS credentials for CLI access",
     "AWS Access Key ID [None]: AKIAIO..."),
]

AWS_DEFENSE_CMDS = [
    ("aws-s3api-block",   "aws s3api put-public-access-block --bucket [name] --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
     "Block ALL public access to a bucket – the most important mitigation",
     "aws s3api put-public-access-block --bucket open-lab-public --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
     "Beginner", "Remediation",
     "Apply public access block to prevent any public access",
     "Public access block applied successfully"),

    ("aws-s3api-encrypt", "aws s3api put-bucket-encryption --bucket [name] --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}'",
     "Enable server-side encryption on S3 bucket",
     "aws s3api put-bucket-encryption --bucket open-lab-public ...",
     "Intermediate", "Encryption",
     "Encrypt all objects in the bucket using AES-256",
     "Bucket encryption enabled"),

    ("aws-s3api-logging", "aws s3api put-bucket-logging --bucket [name] --bucket-logging-status ...",
     "Enable access logging on S3 bucket",
     "aws s3api put-bucket-logging --bucket open-lab-public ...",
     "Intermediate", "Monitoring",
     "Track all S3 access requests for audit",
     "Logging enabled"),

    ("aws-cloudtrail",    "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ListBuckets",
     "Search CloudTrail for specific API events",
     "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetObject",
     "Advanced", "Forensics",
     "Audit trail of API calls to detect unauthorized access",
     "Events found: 3 GetObject calls from 203.0.113.9"),

    ("aws-guardduty",     "aws guardduty list-detectors",
     "List GuardDuty detectors for threat detection status",
     "aws guardduty list-detectors",
     "Intermediate", "Monitoring",
     "Verify AWS GuardDuty is enabled for threat detection",
     "DetectorIds: [abc123def456]"),

    ("aws-iam-mfa",       "aws iam list-virtual-mfa-devices",
     "List IAM users with MFA enabled",
     "aws iam list-virtual-mfa-devices",
     "Intermediate", "IAM Hardening",
     "Identify accounts without multi-factor authentication",
     "Users without MFA: developer"),

    ("aws-iam-policy",    "aws iam put-user-policy --user-name [user] --policy-name [name] --policy-document file://policy.json",
     "Apply a least-privilege IAM policy to a user",
     "aws iam put-user-policy --user-name readonly --policy-name s3-readonly ...",
     "Advanced", "IAM Hardening",
     "Restrict user permissions to only what is necessary",
     "Policy applied successfully"),
]


def get_or_create_table(cur, table, ddl):
    cur.execute(ddl)


def seed_linux_db():
    """Seed linux_commands.db with CMD001 Linux dataset."""
    print(f"\n[CMD001] Seeding linux_commands.db ...")
    conn = sqlite3.connect(LINUX_DB)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS linux_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            pattern TEXT NOT NULL,
            description TEXT,
            example TEXT,
            level TEXT,
            use_case TEXT,
            source TEXT DEFAULT 'CMD001',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE TABLE IF NOT EXISTS command_aliases (id INTEGER PRIMARY KEY, command_id INTEGER, alias_name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS command_usage_logs (id INTEGER PRIMARY KEY, command_id INTEGER, execution_count INTEGER DEFAULT 0, last_used TEXT)")

    # Add columns that may not exist in older DB versions
    for col in ("source TEXT DEFAULT 'CMD001'", "use_case TEXT"):
        try:
            cur.execute(f"ALTER TABLE linux_commands ADD COLUMN {col}")
        except Exception:
            pass

    # Clear and re-seed for idempotency
    cur.execute("DELETE FROM linux_commands")

    for name, cat, pat, desc, ex, lvl, src in LINUX_COMMANDS:
        cur.execute("""
            INSERT INTO linux_commands (name, category, pattern, description, example, level, use_case, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, cat, pat, desc, ex, lvl, desc, src))

    conn.commit()
    print(f"  [OK] {len(LINUX_COMMANDS)} linux commands seeded")
    conn.close()


def seed_s3_db():
    """Seed open_s3_lab.db with CMD002 Cyber + CMD004 AWS commands."""
    print(f"\n[CMD002+CMD004] Seeding open_s3_lab.db ...")
    conn = sqlite3.connect(S3_DB)
    cur  = conn.cursor()

    # Ensure attack/defense command tables exist with full schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attack_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pattern TEXT NOT NULL,
            hint TEXT,
            example TEXT,
            level TEXT,
            category TEXT,
            description TEXT,
            expected_output TEXT,
            source TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS defense_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pattern TEXT NOT NULL,
            hint TEXT,
            example TEXT,
            level TEXT,
            category TEXT,
            description TEXT,
            expected_output TEXT,
            source TEXT
        )
    """)

    # Add source column if missing (upgrade existing DBs)
    for tbl in ("attack_commands", "defense_commands"):
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN source TEXT")
        except Exception:
            pass
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN expected_output TEXT")
        except Exception:
            pass

    # Clear existing seeded rows from our sources
    cur.execute("DELETE FROM attack_commands WHERE source IN ('CMD002','CMD004')")
    cur.execute("DELETE FROM defense_commands WHERE source IN ('CMD002','CMD004')")

    for name, pat, hint, ex, lvl, cat, desc, out in CYBER_ATTACK_CMDS:
        cur.execute("""
            INSERT INTO attack_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD002')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    for name, pat, hint, ex, lvl, cat, desc, out in CYBER_DEFENSE_CMDS:
        cur.execute("""
            INSERT INTO defense_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD002')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    # AWS commands (CMD004) go into S3 lab
    for name, pat, hint, ex, lvl, cat, desc, out in AWS_ATTACK_CMDS:
        cur.execute("""
            INSERT INTO attack_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD004')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    for name, pat, hint, ex, lvl, cat, desc, out in AWS_DEFENSE_CMDS:
        cur.execute("""
            INSERT INTO defense_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD004')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    conn.commit()
    c1 = cur.execute("SELECT COUNT(*) FROM attack_commands").fetchone()[0]
    c2 = cur.execute("SELECT COUNT(*) FROM defense_commands").fetchone()[0]
    print(f"  [OK] attack_commands: {c1} total  |  defense_commands: {c2} total")
    conn.close()


def seed_network_db():
    """Seed network_recon_lab.db with CMD002 Cyber + CMD003 Pentest commands."""
    print(f"\n[CMD002+CMD003] Seeding network_recon_lab.db ...")
    conn = sqlite3.connect(NET_DB)
    cur  = conn.cursor()

    for tbl in ("attack_commands", "defense_commands"):
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {tbl} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                pattern TEXT,
                hint TEXT,
                example TEXT,
                level TEXT,
                category TEXT,
                description TEXT,
                expected_output TEXT,
                source TEXT
            )
        """)
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN description TEXT")
        except Exception:
            pass
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN expected_output TEXT")
        except Exception:
            pass
        try:
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN source TEXT")
        except Exception:
            pass

    cur.execute("DELETE FROM attack_commands WHERE source IN ('CMD002','CMD003')")
    cur.execute("DELETE FROM defense_commands WHERE source IN ('CMD002','CMD003')")

    for name, pat, hint, ex, lvl, cat, desc, out in PENTEST_ATTACK_CMDS:
        cur.execute("""
            INSERT INTO attack_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD003')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    for name, pat, hint, ex, lvl, cat, desc, out in PENTEST_DEFENSE_CMDS:
        cur.execute("""
            INSERT INTO defense_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD003')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    for name, pat, hint, ex, lvl, cat, desc, out in CYBER_ATTACK_CMDS:
        cur.execute("""
            INSERT INTO attack_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD002')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    for name, pat, hint, ex, lvl, cat, desc, out in CYBER_DEFENSE_CMDS:
        cur.execute("""
            INSERT INTO defense_commands (name, pattern, hint, example, level, category, description, expected_output, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CMD002')
        """, (name, pat, hint, ex, lvl, cat, desc, out))

    conn.commit()
    c1 = cur.execute("SELECT COUNT(*) FROM attack_commands").fetchone()[0]
    c2 = cur.execute("SELECT COUNT(*) FROM defense_commands").fetchone()[0]
    print(f"  [OK] attack_commands: {c1} total  |  defense_commands: {c2} total")
    conn.close()


def print_summary():
    print("\n" + "="*60)
    print("  COMMAND DATABASE SEED COMPLETE")
    print("="*60)
    print("  CMD001 – Linux Commands      → data/linux_commands.db")
    print("  CMD002 – Cyber Security      → open_s3_lab.db + network_recon_lab.db")
    print("  CMD003 – Pentest/Kali        → network_recon_lab.db")
    print("  CMD004 – AWS CLI             → open_s3_lab.db")
    print()
    print("  [WARN]  These commands are for: hints | terminal output | AI analysis")
    print("  [NO]  Task completion = ONLY via /api/submit_task answer check")
    print("="*60)


if __name__ == "__main__":
    for path in [S3_DB, NET_DB, LINUX_DB]:
        if not os.path.exists(os.path.dirname(path)):
            print(f"[ERROR] Directory missing: {os.path.dirname(path)}")
            sys.exit(1)

    seed_linux_db()
    seed_s3_db()
    seed_network_db()
    print_summary()
