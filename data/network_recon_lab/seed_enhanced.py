#!/usr/bin/env python3
"""Enhanced seed script for Network Recon lab with large dummy dataset."""
from __future__ import annotations
import sqlite3
import json
import os
import random
from datetime import datetime, timezone, timedelta


BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "network_recon_lab.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")


def now_iso(delta_days=0):
    return (datetime.now(timezone.utc) - timedelta(days=delta_days)).isoformat()


def load_schema(conn: sqlite3.Connection):
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def insert_many(conn, sql, rows):
    cur = conn.cursor()
    cur.executemany(sql, rows)
    return cur


def seed():
    random.seed(42)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn)

    # ==================== HOSTS (50+) ====================
    hosts_rows = []
    host_names = []
    for i in range(50):
        ip = f"192.168.1.{i+1}"
        hostname = f"host-{i:03d}.lab.local"
        os_type = random.choice(["Linux", "Windows", "macOS", "RouterOS"])
        is_active = random.choice([0, 1])
        discovered = now_iso(random.randint(0, 30))
        hosts_rows.append((ip, hostname, os_type, is_active, discovered))
        host_names.append(hostname)
    
    insert_many(conn, "INSERT INTO hosts(ip_address, hostname, os_type, is_active, discovered_at) VALUES (?, ?, ?, ?, ?)", hosts_rows)

    # Fetch host ids
    cur = conn.cursor()
    cur.execute("SELECT id, ip_address FROM hosts")
    host_map = {r[1]: r[0] for r in cur.fetchall()}
    host_list = list(host_map.values())

    # ==================== SERVICES (150+) ====================
    services_rows = []
    service_types = [
        ("SSH", 22, "tcp", "OpenSSH 7.4"),
        ("HTTP", 80, "tcp", "Apache 2.4"),
        ("HTTPS", 443, "tcp", "Apache 2.4"),
        ("MySQL", 3306, "tcp", "MySQL 5.7"),
        ("PostgreSQL", 5432, "tcp", "PostgreSQL 10"),
        ("FTP", 21, "tcp", "vsftpd 3.0"),
        ("Telnet", 23, "tcp", "Linux Telnet"),
        ("SMTP", 25, "tcp", "Postfix 2.11"),
        ("DNS", 53, "udp", "BIND 9.11"),
        ("SNMP", 161, "udp", "NET-SNMP 5.7"),
        ("RDP", 3389, "tcp", "Windows RDP"),
        ("VNC", 5900, "tcp", "VNC Server"),
        ("Redis", 6379, "tcp", "Redis 4.0"),
        ("MongoDB", 27017, "tcp", "MongoDB 3.6"),
        ("Elasticsearch", 9200, "tcp", "Elasticsearch 6.0"),
    ]
    
    # Create unique combinations of host/port/protocol
    seen_combos = set()
    for _ in range(150):
        while True:
            host_id = random.choice(host_list)
            service_name, port, protocol, version = random.choice(service_types)
            combo = (host_id, port, protocol)
            if combo not in seen_combos:
                seen_combos.add(combo)
                break
        
        is_vulnerable = random.choice([0, 1])
        discovered = now_iso(random.randint(0, 60))
        services_rows.append((host_id, port, protocol, service_name, version, is_vulnerable, discovered))
    
    insert_many(conn, "INSERT INTO services(host_id, port, protocol, service_name, version, is_vulnerable, discovered_at) VALUES (?, ?, ?, ?, ?, ?, ?)", services_rows)

    # Fetch service ids
    cur.execute("SELECT id FROM services")
    service_ids = [r[0] for r in cur.fetchall()]

    # ==================== VULNERABILITIES (100+) ====================
    vulnerabilities_rows = []
    vuln_data = [
        ("CVE-2021-12345", "SQL Injection", "CRITICAL", "Potential SQL injection in web application", "Data breach", "Use parameterized queries"),
        ("CVE-2020-56789", "Buffer Overflow", "CRITICAL", "Buffer overflow in OpenSSH", "Remote code execution", "Update to latest version"),
        ("CVE-2021-11111", "XSS Vulnerability", "HIGH", "XSS vulnerability in web interface", "Session hijacking", "Sanitize user input"),
        ("CVE-2020-22222", "Weak Encryption", "MEDIUM", "Using DES encryption", "Data exposure", "Switch to AES-256"),
        ("CVE-2021-33333", "Missing Patch", "HIGH", "Security patch not applied", "Exploitation risk", "Apply latest patches"),
        ("CVE-2020-44444", "Default Credentials", "CRITICAL", "Using default username/password", "Unauthorized access", "Change default credentials"),
        ("CVE-2021-55555", "CSRF Token Missing", "MEDIUM", "CSRF protection not implemented", "Session hijacking", "Implement CSRF tokens"),
        ("CVE-2020-66666", "Unencrypted Protocol", "MEDIUM", "HTTP instead of HTTPS", "Data interception", "Enable SSL/TLS"),
    ]
    
    for i in range(100):
        service_id = random.choice(service_ids) if random.random() > 0.3 else service_ids[0]
        cve_id, title, severity, description, impact, remediation = random.choice(vuln_data)
        discovered = now_iso(random.randint(0, 90))
        vulnerabilities_rows.append((service_id, cve_id, title, severity, description, impact, remediation, discovered))
    
    insert_many(conn, "INSERT INTO vulnerabilities(service_id, cve_id, title, severity, description, impact, remediation, discovered_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", vulnerabilities_rows)

    # ==================== NETWORK TRAFFIC (200+) ====================
    traffic_rows = []
    for i in range(200):
        src_ip = f"10.0.0.{random.randint(1, 255)}"
        dst_ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        dst_port = random.choice([22, 80, 443, 3306, 5432, 53, 25, 21, 5900])
        protocol = random.choice(["TCP", "UDP", "ICMP"])
        packet_count = random.randint(1, 1000)
        bytes_sent = random.randint(100, 1000000)
        timestamp = now_iso(random.randint(0, 30))
        
        traffic_rows.append((src_ip, dst_ip, dst_port, protocol, packet_count, bytes_sent, timestamp))
    
    insert_many(conn, "INSERT INTO network_traffic(src_ip, dst_ip, dst_port, protocol, packet_count, bytes_sent, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", traffic_rows)

    # ==================== FIREWALL RULES (50+) ====================
    firewall_rules_rows = []
    rule_configs = [
        ("Allow HTTP", "0.0.0.0/0", "0.0.0.0/0", 80, "TCP", "ALLOW", 1),
        ("Allow HTTPS", "0.0.0.0/0", "0.0.0.0/0", 443, "TCP", "ALLOW", 1),
        ("Allow SSH Admin", "10.0.0.0/8", "192.168.0.0/16", 22, "TCP", "ALLOW", 1),
        ("Deny Telnet", "0.0.0.0/0", "0.0.0.0/0", 23, "TCP", "DENY", 1),
        ("Deny FTP", "0.0.0.0/0", "0.0.0.0/0", 21, "TCP", "DENY", 1),
        ("Allow DNS", "0.0.0.0/0", "8.8.8.8/32", 53, "UDP", "ALLOW", 1),
    ]
    
    for i in range(50):
        config = rule_configs[i % len(rule_configs)]
        base_name, src_range, dst_range, dst_port, protocol, action, enabled = config
        rule_name = f"{base_name} {i}" # Make each unique
        created = now_iso(random.randint(0, 180))
        firewall_rules_rows.append((rule_name, src_range, dst_range, dst_port, protocol, action, enabled, created))
    
    insert_many(conn, "INSERT INTO firewall_rules(rule_name, src_range, dst_range, dst_port, protocol, action, is_enabled, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", firewall_rules_rows)

    # ==================== IDS ALERTS (80+) ====================
    ids_alerts_rows = []
    alert_configs = [
        ("Port Scan", "Multiple ports scanned from single source"),
        ("Brute Force", "Repeated failed authentication attempts"),
        ("SQL Injection Attempt", "Suspicious SQL characters detected"),
        ("XSS Attempt", "Script tags detected in HTTP request"),
        ("DDoS Pattern", "Abnormal traffic volume detected"),
        ("Malware Signature", "Known malware signature detected"),
        ("Privilege Escalation", "Unauthorized privilege elevation attempt"),
        ("Data Exfiltration", "Large data transfer to external IP"),
    ]
    
    for i in range(80):
        src_ip = f"203.0.113.{random.randint(1, 255)}"
        dst_ip = f"192.168.1.{random.randint(1, 255)}"
        alert_type, details = random.choice(alert_configs)
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        timestamp = now_iso(random.randint(0, 60))
        
        ids_alerts_rows.append((src_ip, dst_ip, alert_type, severity, details, timestamp))
    
    insert_many(conn, "INSERT INTO ids_alerts(src_ip, dst_ip, alert_type, severity, details, timestamp) VALUES (?, ?, ?, ?, ?, ?)", ids_alerts_rows)

    # ==================== ATTACK COMMANDS ====================
    attack_commands = [
        ("Nmap Scan", "nmap -sV [target]", "Scan for services and versions", "nmap -sV 192.168.1.0/24", "Beginner", "Reconnaissance"),
        ("Traceroute", "traceroute [target]", "Trace network path to target", "traceroute 192.168.1.1", "Beginner", "Reconnaissance"),
        ("ARP Scan", "arp-scan -l", "Discover hosts on local network", "arp-scan -l --localnet", "Beginner", "Reconnaissance"),
        ("DNS Enumeration", "dig axfr @[dns_server] [domain]", "Perform DNS zone transfer", "dig axfr @ns1.example.com example.com", "Intermediate", "Reconnaissance"),
        ("Service Enumeration", "nmap -sC -sV [target]", "Detect running services", "nmap -sC -sV -p- 192.168.1.1", "Intermediate", "Reconnaissance"),
        ("Vulnerability Scan", "nessus/openvas scan", "Vulnerability assessment", "nessus-cli --scan vuln_scan 192.168.1.0/24", "Intermediate", "Scanning"),
        ("Man-in-the-Middle", "ettercap -T arp", "ARP spoofing attack", "ettercap -T arp:remote /192.168.1.1// /192.168.1.2//", "Advanced", "Attack"),
        ("DDoS Attack", "hping3 --flood -S -p [port] [target]", "Flood target with packets", "hping3 --flood -S -p 80 192.168.1.1", "Advanced", "Attack"),
        ("Network Sniffing", "tcpdump -i eth0", "Capture network traffic", "tcpdump -i eth0 -w capture.pcap", "Intermediate", "Analysis"),
        ("Wireshark Analysis", "wireshark", "Analyze captured traffic", "wireshark capture.pcap", "Intermediate", "Analysis"),
        ("Nessus Full Audit", "nessus [full-audit]", "Complete vulnerability assessment", "nessus --audit full 192.168.1.0/24", "Advanced", "Scanning"),
        ("Packet Crafting", "scapy", "Create custom packets", "python scapy_script.py", "Advanced", "Attack"),
    ]
    
    insert_many(conn, "INSERT INTO attack_commands(name, pattern, hint, example, level, category) VALUES (?, ?, ?, ?, ?, ?)", attack_commands)

    # ==================== DEFENSE COMMANDS ====================
    defense_commands = [
        ("Configure Firewall", "firewall-cmd --add-service=[service]", "Add service to firewall whitelist", "firewall-cmd --add-service=http --permanent", "Beginner", "Prevention"),
        ("Update Firewall Rules", "iptables -A INPUT -p tcp --dport 22 -j ACCEPT", "Create firewall ACL", "iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 22 -j ACCEPT", "Intermediate", "Prevention"),
        ("Enable IDS", "suricata/snort -c rules.yaml", "Deploy intrusion detection", "suricata -c /etc/suricata/suricata.yaml -i eth0", "Intermediate", "Detection"),
        ("Monitor Logs", "tail -f /var/log/syslog", "Real-time log monitoring", "tail -f /var/log/auth.log | grep 'Failed'", "Beginner", "Detection"),
        ("Network Segmentation", "vlan configuration", "Implement network isolation", "create vlan 100 name admin-segment", "Intermediate", "Prevention"),
        ("Disable Unnecessary Services", "systemctl disable [service]", "Stop unused services", "systemctl disable telnet; systemctl disable ftp", "Beginner", "Hardening"),
        ("Update Systems", "apt-get update && apt-get upgrade", "Apply security patches", "apt-get update; apt-get upgrade -y", "Beginner", "Hardening"),
        ("Change Default Credentials", "passwd [user]", "Update default passwords", "echo 'user:newpass' | chpasswd", "Beginner", "Hardening"),
        ("Enable Encryption", "openssl/ssh-keygen", "Encrypt network traffic", "ssh-keygen -t rsa -b 4096", "Intermediate", "Protection"),
        ("Setup VPN", "openvpn/wireguard config", "Create secure tunnel", "openvpn --config server.conf", "Advanced", "Protection"),
        ("SIEM Configuration", "splunk/elk setup", "Centralized log management", "splunk add forward-server 192.168.1.10:9998", "Advanced", "Detection"),
        ("Incident Response", "isolate_host [ip]", "Quarantine compromised host", "iptables -A FORWARD -s 192.168.1.50 -j DROP", "Advanced", "Response"),
    ]
    
    insert_many(conn, "INSERT INTO defense_commands(name, pattern, hint, example, level, category) VALUES (?, ?, ?, ?, ?, ?)", defense_commands)

    conn.commit()

    # Export to JSON
    for tbl in ("hosts", "services", "vulnerabilities", "network_traffic", "firewall_rules", "ids_alerts", "attack_commands", "defense_commands"):
        try:
            rows = [dict(r) for r in conn.execute(f"SELECT * FROM {tbl}")]
            with open(os.path.join(BASE_DIR, f"{tbl}.json"), "w", encoding="utf-8") as jf:
                json.dump(rows, jf, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not export {tbl}: {e}")

    conn.close()
    print(f"Network Recon lab database seeded successfully at {DB_PATH}")
    print(f"- Hosts: {len(hosts_rows)}")
    print(f"- Services: {len(services_rows)}")
    print(f"- Vulnerabilities: {len(vulnerabilities_rows)}")
    print(f"- Network Traffic: {len(traffic_rows)}")
    print(f"- Firewall Rules: {len(firewall_rules_rows)}")
    print(f"- IDS Alerts: {len(ids_alerts_rows)}")
    print(f"- Attack Commands: {len(attack_commands)}")
    print(f"- Defense Commands: {len(defense_commands)}")
    print(f"- Total Records: {len(hosts_rows) + len(services_rows) + len(vulnerabilities_rows) + len(traffic_rows) + len(firewall_rules_rows) + len(ids_alerts_rows) + len(attack_commands) + len(defense_commands)}")


if __name__ == "__main__":
    seed()
