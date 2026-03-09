#!/usr/bin/env python3
"""Seed script for Network Reconnaissance lab.

Creates an SQLite DB at `network_recon_lab.db`, populates tables with synthetic
network environment data including hosts, services, vulnerabilities, and traffic.
All data is completely fictional and for educational purposes only.
"""
from __future__ import annotations
import sqlite3
import json
import os
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
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn)

    # Levels
    levels = [
        ("Beginner", 0.3, "Slower/lenient AI detection, hints more helpful"),
        ("Intermediate", 0.6, "Moderate AI detection and reactive behavior"),
        ("Advanced", 0.85, "Aggressive AI detection and active mitigation"),
    ]
    insert_many(conn, "INSERT INTO levels(name,detection_modifier,description) VALUES (?,?,?)", levels)

    # Hosts: simulated network environment
    hosts = [
        ("192.168.1.10", "lab-gateway.local", "Linux", 1, now_iso(30)),
        ("192.168.1.20", "lab-web-server.local", "Linux", 1, now_iso(30)),
        ("192.168.1.30", "lab-db-server.local", "Linux", 1, now_iso(30)),
        ("192.168.1.40", "lab-mail-server.local", "Linux", 1, now_iso(30)),
        ("192.168.1.50", "lab-dns-server.local", "Linux", 1, now_iso(30)),
        ("192.168.1.100", "lab-workstation.local", "Windows", 1, now_iso(25)),
        ("10.0.0.5", "lab-vpn-gateway.local", "Linux", 1, now_iso(20)),
    ]
    insert_many(conn, "INSERT INTO hosts(ip_address,hostname,os_type,is_active,discovered_at) VALUES (?,?,?,?,?)", hosts)

    # Fetch host ids
    cur = conn.cursor()
    cur.execute("SELECT id,ip_address FROM hosts")
    host_map = {r[1]: r[0] for r in cur.fetchall()}

    # Services: typical enterprise services
    services_rows = [
        # Gateway
        (host_map["192.168.1.10"], 22, "tcp", "ssh", "OpenSSH 7.4", 0, now_iso(30)),
        (host_map["192.168.1.10"], 53, "udp", "dns", "BIND 9.9.5", 0, now_iso(30)),
        # Web server
        (host_map["192.168.1.20"], 22, "tcp", "ssh", "OpenSSH 7.6", 0, now_iso(30)),
        (host_map["192.168.1.20"], 80, "tcp", "http", "Apache 2.4.6", 1, now_iso(30)),
        (host_map["192.168.1.20"], 443, "tcp", "https", "Apache 2.4.6", 0, now_iso(30)),
        # Database server
        (host_map["192.168.1.30"], 22, "tcp", "ssh", "OpenSSH 7.6", 0, now_iso(30)),
        (host_map["192.168.1.30"], 3306, "tcp", "mysql", "MySQL 5.7.21", 1, now_iso(30)),
        # Mail server
        (host_map["192.168.1.40"], 22, "tcp", "ssh", "OpenSSH 7.4", 0, now_iso(30)),
        (host_map["192.168.1.40"], 25, "tcp", "smtp", "Postfix 2.10.1", 1, now_iso(30)),
        (host_map["192.168.1.40"], 143, "tcp", "imap", "Dovecot 2.2.36", 1, now_iso(30)),
        # DNS server
        (host_map["192.168.1.50"], 22, "tcp", "ssh", "OpenSSH 7.4", 0, now_iso(30)),
        (host_map["192.168.1.50"], 53, "tcp", "dns", "BIND 9.9.5", 1, now_iso(30)),
        # Workstation
        (host_map["192.168.1.100"], 445, "tcp", "smb", "SMB 1.0", 1, now_iso(25)),
        (host_map["192.168.1.100"], 3389, "tcp", "rdp", "RDP 6.1", 1, now_iso(25)),
        # VPN Gateway
        (host_map["10.0.0.5"], 22, "tcp", "ssh", "OpenSSH 8.0", 0, now_iso(20)),
        (host_map["10.0.0.5"], 1194, "udp", "openvpn", "OpenVPN 2.4.7", 0, now_iso(20)),
    ]
    insert_many(conn, "INSERT INTO services(host_id,port,protocol,service_name,version,is_vulnerable,discovered_at) VALUES (?,?,?,?,?,?,?)", services_rows)

    # Fetch service ids
    cur.execute("SELECT id,host_id,port FROM services")
    service_ids = {(r[1], r[2]): r[0] for r in cur.fetchall()}

    # Vulnerabilities: synthetic CVEs for lab purposes
    vuln_rows = [
        (service_ids[(host_map["192.168.1.20"], 80)], "CVE-2017-1234", "Apache RCE Vulnerability", "HIGH", 
         "Improper input validation in Apache 2.4.6", "Remote Code Execution", "Upgrade to Apache 2.4.37", now_iso(30)),
        (service_ids[(host_map["192.168.1.30"], 3306)], "CVE-2018-5678", "MySQL Authentication Bypass", "CRITICAL",
         "Default credentials and weak authentication", "Unauthorized database access", "Disable default accounts, enforce strong passwords", now_iso(30)),
        (service_ids[(host_map["192.168.1.40"], 25)], "CVE-2019-8765", "Postfix Open Relay", "HIGH",
         "Postfix configured to relay mail from any source", "Spam and malware distribution", "Configure relay restrictions", now_iso(30)),
        (service_ids[(host_map["192.168.1.40"], 143)], "CVE-2020-9876", "Dovecot Plaintext Login", "MEDIUM",
         "Plaintext authentication allowed over unencrypted connection", "Credential interception", "Enforce TLS/SSL", now_iso(30)),
        (service_ids[(host_map["192.168.1.50"], 53)], "CVE-2017-9999", "DNS Zone Transfer", "HIGH",
         "BIND allows unrestricted zone transfers", "DNS enumeration and information disclosure", "Restrict zone transfers", now_iso(30)),
        (service_ids[(host_map["192.168.1.100"], 445)], "CVE-2017-0144", "EternalBlue SMB", "CRITICAL",
         "SMB vulnerability allowing remote code execution", "System compromise and lateral movement", "Patch Windows system immediately", now_iso(25)),
        (service_ids[(host_map["192.168.1.100"], 3389)], "CVE-2019-0604", "RDP Vulnerability", "HIGH",
         "RDP allows unauthenticated access", "Unauthorized remote access", "Enable Network Level Authentication", now_iso(25)),
    ]
    insert_many(conn, "INSERT INTO vulnerabilities(service_id,cve_id,title,severity,description,impact,remediation,discovered_at) VALUES (?,?,?,?,?,?,?,?)", vuln_rows)

    # Network traffic: simulated communication patterns
    traffic_rows = [
        ("192.168.1.100", "192.168.1.20", 80, "tcp", 45, 12800, now_iso(1)),
        ("192.168.1.100", "192.168.1.30", 3306, "tcp", 120, 45000, now_iso(1)),
        ("192.168.1.20", "192.168.1.50", 53, "udp", 20, 5120, now_iso(1)),
        ("203.0.113.1", "192.168.1.20", 80, "tcp", 150, 64000, now_iso(2)),  # External traffic
        ("203.0.113.5", "192.168.1.20", 443, "tcp", 300, 128000, now_iso(3)),  # External HTTPS
    ]
    insert_many(conn, "INSERT INTO network_traffic(src_ip,dst_ip,dst_port,protocol,packet_count,bytes_sent,timestamp) VALUES (?,?,?,?,?,?,?)", traffic_rows)

    # Firewall rules
    firewall_rows = [
        ("Allow SSH Admin", "203.0.113.0/24", "192.168.1.10", 22, "tcp", "allow", 1, now_iso(30)),
        ("Block External HTTP", "0.0.0.0/0", "192.168.1.20", 80, "tcp", "deny", 0, now_iso(30)),
        ("Allow DNS Internal", "192.168.1.0/24", "192.168.1.50", 53, "udp", "allow", 1, now_iso(30)),
        ("Block SMB External", "0.0.0.0/0", "192.168.1.100", 445, "tcp", "deny", 1, now_iso(30)),
    ]
    insert_many(conn, "INSERT INTO firewall_rules(rule_name,src_range,dst_range,dst_port,protocol,action,is_enabled,created_at) VALUES (?,?,?,?,?,?,?,?)", firewall_rows)

    # IDS alerts: simulated detections
    ids_rows = [
        ("203.0.113.5", "192.168.1.20", "port_scan", "LOW", "Multiple port connections detected", now_iso(2)),
        ("192.168.1.100", "192.168.1.40", "brute_force", "MEDIUM", "Multiple failed login attempts on SMTP", now_iso(3)),
        ("203.0.113.1", "192.168.1.30", "sql_injection", "HIGH", "SQL injection pattern detected in traffic", now_iso(5)),
    ]
    insert_many(conn, "INSERT INTO ids_alerts(src_ip,dst_ip,alert_type,severity,details,timestamp) VALUES (?,?,?,?,?,?)", ids_rows)

    # Attack commands for Network Recon
    attack_cmds = [
        ("Network Scan", "nmap -sn 192.168.1.0/24", "Discover active hosts on network", "nmap -sn 192.168.1.0/24", "Beginner", "recon"),
        ("Port Scan", "nmap -sV 192.168.1.20", "Identify open ports and services", "nmap -sV -p- 192.168.1.20", "Beginner", "recon"),
        ("Service Enumeration", "nmap -A 192.168.1.30", "Gather detailed service information", "nmap -A -O 192.168.1.30", "Intermediate", "recon"),
        ("DNS Enumeration", "dig axfr @192.168.1.50", "Perform DNS zone transfer", "dig axfr lab.local @192.168.1.50", "Intermediate", "recon"),
        ("Vulnerability Scan", "nessus -t 192.168.1.20", "Scan target for known vulnerabilities", "nessus --scan 192.168.1.20", "Intermediate", "recon"),
        ("Brute Force SSH", "ssh -l admin 192.168.1.10", "Attempt SSH login with weak credentials", "hydra -l admin -P passwords.txt ssh://192.168.1.10", "Advanced", "access"),
    ]
    insert_many(conn, "INSERT INTO attack_commands(name,pattern,hint,example,level,category) VALUES (?,?,?,?,?,?)", attack_cmds)

    # Defense commands for Network Recon
    defense_cmds = [
        ("Network Segmentation", "firewall rules", "Isolate network segments with firewalls", "Configure firewall rules to restrict traffic", "Beginner", "prevention"),
        ("Port Hardening", "close unused ports", "Disable unused services and close ports", "Stop unnecessary services, configure ACLs", "Beginner", "prevention"),
        ("IDS/IPS Deployment", "install ids", "Deploy intrusion detection/prevention system", "Configure IDS rules and signatures", "Intermediate", "detection"),
        ("Network Monitoring", "tcpdump analysis", "Monitor network traffic for anomalies", "Use tools to capture and analyze packets", "Intermediate", "detection"),
        ("Patch Management", "apply patches", "Install security patches for services", "Regular updates for OS and applications", "Intermediate", "remediation"),
        ("SSH Hardening", "change default port", "Secure SSH configuration", "Disable root login, use key-based auth", "Advanced", "prevention"),
    ]
    insert_many(conn, "INSERT INTO defense_commands(name,pattern,hint,example,level,category) VALUES (?,?,?,?,?,?)", defense_cmds)

    conn.commit()
    conn.close()
    print(f"Network Recon lab database seeded successfully at {DB_PATH}")


if __name__ == "__main__":
    seed()
