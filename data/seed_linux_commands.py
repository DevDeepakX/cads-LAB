#!/usr/bin/env python3
"""
Seed the linux_commands.db with intermediate-level Linux commands
Used across all labs
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "linux_commands.db")

def seed_linux_commands():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create schema
    with open(os.path.join(os.path.dirname(__file__), "linux_commands_schema.sql")) as f:
        cur.executescript(f.read())
    
    # Intermediate-level commands
    commands = [
        # File and Directory Management
        ("ls -lah", "File Management", "ls -lah [directory]", "List files with detailed info and hidden files", "ls -lah /home/user", "Intermediate", "View directory contents with permissions and sizes"),
        ("find", "File Management", "find [path] -name [pattern]", "Search for files by name or pattern", "find /var -name '*.log'", "Intermediate", "Locate files across directory trees"),
        ("grep", "File Management", "grep -r [pattern] [path]", "Search file contents recursively", "grep -r 'admin' /etc", "Intermediate", "Search for text patterns in files"),
        ("awk", "File Management", "awk '{print $1}' [file]", "Parse and process text fields", "awk '{print $1}' /var/log/access.log", "Intermediate", "Extract and manipulate columns from files"),
        ("sed", "File Management", "sed 's/old/new/g' [file]", "Stream editor for text substitution", "sed 's/password/REDACTED/g' config.txt", "Intermediate", "Replace text in files and streams"),
        
        # Process Management
        ("ps aux", "Process Management", "ps aux | grep [process]", "List all running processes", "ps aux | grep apache", "Intermediate", "Monitor running processes and resource usage"),
        ("top", "Process Management", "top -b -n 1", "Display real-time system statistics", "top -b -n 1 | head -20", "Intermediate", "Monitor CPU and memory usage"),
        ("kill", "Process Management", "kill -9 [PID]", "Terminate process by ID", "kill -9 1234", "Intermediate", "Forcefully stop running processes"),
        ("lsof", "Process Management", "lsof -i :8080", "List open files and network connections", "lsof -i :443", "Intermediate", "Identify processes using specific ports"),
        ("netstat", "Process Management", "netstat -tulpn", "Display network statistics and connections", "netstat -tulpn | grep LISTEN", "Intermediate", "Monitor network connections and listening ports"),
        
        # Network Reconnaissance
        ("ping", "Network", "ping -c 4 [host]", "Test host connectivity", "ping -c 4 8.8.8.8", "Intermediate", "Check if host is reachable"),
        ("nmap", "Network", "nmap -sV [host]", "Port scanning and service detection", "nmap -sV -p 1-1000 192.168.1.0/24", "Intermediate", "Enumerate hosts and services on network"),
        ("traceroute", "Network", "traceroute [host]", "Trace route to remote host", "traceroute google.com", "Intermediate", "Identify network path and hops"),
        ("dig", "Network", "dig [domain] +short", "Query DNS records", "dig example.com MX", "Intermediate", "Resolve domain names and DNS information"),
        ("whois", "Network", "whois [domain]", "Query domain registration information", "whois example.com", "Intermediate", "Gather domain ownership details"),
        ("curl", "Network", "curl -X POST -H 'Content-Type: application/json' -d '{...}' [url]", "Transfer data with URLs", "curl -X GET http://api.example.com/users", "Intermediate", "Test APIs and fetch web content"),
        ("wget", "Network", "wget -r [url]", "Download files from web", "wget -r http://example.com/data", "Intermediate", "Bulk download files from websites"),
        
        # User and Permission Management
        ("whoami", "User Management", "whoami", "Display current user", "whoami", "Intermediate", "Identify logged-in user"),
        ("id", "User Management", "id [username]", "Display user and group info", "id root", "Intermediate", "Check user privileges and groups"),
        ("sudo", "User Management", "sudo [command]", "Execute as superuser", "sudo apt-get install package", "Intermediate", "Run commands with elevated privileges"),
        ("useradd", "User Management", "useradd -m [username]", "Create new user account", "useradd -m -s /bin/bash newuser", "Intermediate", "Add system users"),
        ("chmod", "User Management", "chmod 755 [file]", "Change file permissions", "chmod 644 config.txt", "Intermediate", "Modify file and directory permissions"),
        ("chown", "User Management", "chown [user]:[group] [file]", "Change file ownership", "chown apache:apache /var/www/html", "Intermediate", "Transfer file ownership"),
        ("umask", "User Management", "umask 0077", "Set default file creation permissions", "umask 0077", "Intermediate", "Control default permissions for new files"),
        
        # System Information
        ("uname", "System Info", "uname -a", "Display system information", "uname -a", "Intermediate", "Get kernel and OS details"),
        ("df", "System Info", "df -h", "Show disk space usage", "df -h /", "Intermediate", "Monitor filesystem usage"),
        ("du", "System Info", "du -sh [directory]", "Display directory size", "du -sh /home", "Intermediate", "Calculate directory and file sizes"),
        ("free", "System Info", "free -h", "Display memory usage", "free -h", "Intermediate", "Monitor RAM and swap usage"),
        ("uptime", "System Info", "uptime", "Display system uptime", "uptime", "Intermediate", "Check how long system has been running"),
        ("hostnamectl", "System Info", "hostnamectl", "Display and set hostname", "hostnamectl set-hostname newname", "Intermediate", "Manage system hostname"),
        ("systemctl", "System Info", "systemctl status [service]", "Manage system services", "systemctl restart apache2", "Intermediate", "Control and monitor system services"),
        
        # Archive and Compression
        ("tar", "Archive", "tar -czf [archive.tar.gz] [directory]", "Create compressed archives", "tar -czf backup.tar.gz /home/user", "Intermediate", "Backup and compress directories"),
        ("gzip", "Archive", "gzip -9 [file]", "Compress files with gzip", "gzip -9 largefile.txt", "Intermediate", "High compression ratio for files"),
        ("zip", "Archive", "zip -r [archive.zip] [directory]", "Create zip archives", "zip -r data.zip /var/data", "Intermediate", "Create Windows-compatible archives"),
        ("unzip", "Archive", "unzip [archive.zip]", "Extract zip files", "unzip data.zip -d /tmp", "Intermediate", "Extract zip archive contents"),
        
        # Text Processing
        ("cat", "Text Processing", "cat [file]", "Display file contents", "cat /etc/passwd", "Intermediate", "View file content"),
        ("head", "Text Processing", "head -n 20 [file]", "Display first N lines", "head -n 100 /var/log/auth.log", "Intermediate", "Preview beginning of large files"),
        ("tail", "Text Processing", "tail -f [file]", "Display last N lines (follow)", "tail -f /var/log/syslog", "Intermediate", "Monitor log files in real-time"),
        ("wc", "Text Processing", "wc -l [file]", "Count lines, words, characters", "wc -l /var/log/auth.log", "Intermediate", "Get file statistics"),
        ("sort", "Text Processing", "sort -n [file]", "Sort file contents", "sort -rn /var/log/access.log | head", "Intermediate", "Arrange data in order"),
        ("uniq", "Text Processing", "uniq -c [file]", "Remove or count duplicate lines", "sort file.txt | uniq -c", "Intermediate", "Identify duplicate entries"),
        ("tr", "Text Processing", "tr 'a-z' 'A-Z' < [file]", "Translate characters", "tr '[:lower:]' '[:upper:]' < file.txt", "Intermediate", "Transform character sets"),
        ("cut", "Text Processing", "cut -d: -f1 [file]", "Extract columns from file", "cut -d: -f1,3 /etc/passwd", "Intermediate", "Select specific fields from files"),
        
        # Security and Audit
        ("sha256sum", "Security", "sha256sum [file]", "Calculate SHA256 hash", "sha256sum backup.tar.gz", "Intermediate", "Verify file integrity"),
        ("md5sum", "Security", "md5sum [file]", "Calculate MD5 hash", "md5sum file.iso", "Intermediate", "Quick file integrity check"),
        ("openssl", "Security", "openssl s_client -connect [host:port]", "SSL/TLS testing and encryption", "openssl s_client -connect example.com:443", "Intermediate", "Test SSL certificates and encryption"),
        ("gpg", "Security", "gpg --encrypt -r [recipient] [file]", "Encrypt/decrypt with GPG", "gpg --encrypt file.txt", "Intermediate", "Secure file encryption and signing"),
        ("ssh", "Security", "ssh -i [key] user@[host]", "Secure shell connection", "ssh -i ~/.ssh/id_rsa admin@192.168.1.1", "Intermediate", "Remote secure access"),
        ("scp", "Security", "scp -r [source] [dest]", "Secure file copy", "scp -r user@remote:/data /local/backup", "Intermediate", "Securely transfer files"),
        
        # Log Analysis
        ("journalctl", "Log Analysis", "journalctl -u [service] -n 50", "Query system journal", "journalctl -u ssh -n 20", "Intermediate", "View system logs by service"),
        ("lastlog", "Log Analysis", "lastlog", "Display user login history", "lastlog | head -20", "Intermediate", "Check user last login times"),
        ("last", "Log Analysis", "last -f /var/log/wtmp", "Show login history", "last -n 50", "Intermediate", "Review login and logout records"),
        ("audit", "Log Analysis", "ausearch -m execve", "Search audit logs", "ausearch -m user_auth", "Intermediate", "Query system audit logs"),
        
        # Package Management
        ("apt-get", "Package Mgmt", "apt-get install [package]", "Debian/Ubuntu package manager", "apt-get install openssh-server", "Intermediate", "Install system packages"),
        ("dpkg", "Package Mgmt", "dpkg -l | grep [pattern]", "Debian package tool", "dpkg -l | grep apache", "Intermediate", "List and query installed packages"),
        ("yum", "Package Mgmt", "yum install [package]", "Red Hat package manager", "yum install httpd", "Intermediate", "Install packages on RedHat systems"),
        ("rpm", "Package Mgmt", "rpm -qa", "RPM package manager", "rpm -qa | grep kernel", "Intermediate", "Query installed RPM packages"),
        
        # Monitoring and Debugging
        ("strace", "Debugging", "strace -e open [command]", "Trace system calls", "strace -o trace.txt curl example.com", "Intermediate", "Debug application behavior"),
        ("ltrace", "Debugging", "ltrace [binary]", "Trace library calls", "ltrace ./myapp", "Intermediate", "Monitor library function calls"),
        ("valgrind", "Debugging", "valgrind --leak-check=full [binary]", "Memory debugger", "valgrind --leak-check=full ./app", "Intermediate", "Detect memory leaks"),
        ("gdb", "Debugging", "gdb [binary]", "GNU debugger", "gdb -ex run --args ./app arg1", "Intermediate", "Interactive debugging tool"),
    ]
    
    # Insert commands
    for name, category, pattern, description, example, level, use_case in commands:
        cur.execute("""
            INSERT INTO linux_commands (name, category, pattern, description, example, level, use_case)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, pattern, description, example, level, use_case))
    
    conn.commit()
    conn.close()
    print(f"Linux commands database seeded successfully at {DB_PATH}")
    print(f"Total commands: {len(commands)}")

if __name__ == "__main__":
    seed_linux_commands()
