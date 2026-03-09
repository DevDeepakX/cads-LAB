"""
build_cyber_knowledge.py
========================
Processes the UNSW-NB15 network intrusion dataset from archive (1).zip
and builds a compact cybersecurity knowledge base (cyber_knowledge.json)
that is injected into the Groq AI system prompt to give the chatbot
real dataset-grounded knowledge about attack patterns.

Run once:
    python src/build_cyber_knowledge.py

Output: src/cyber_knowledge.json
"""

import zipfile
import os
import json
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_PATH = os.path.join(SCRIPT_DIR, "archive (1).zip")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "cyber_knowledge.json")


def load_dataset():
    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas not installed. Run: pip install pandas pyarrow")
        sys.exit(1)

    print(f"[INFO] Loading dataset from: {ARCHIVE_PATH}")
    with zipfile.ZipFile(ARCHIVE_PATH) as z:
        with z.open("UNSW_NB15_training-set.parquet") as f:
            train_df = pd.read_parquet(f)
        with z.open("UNSW_NB15_testing-set.parquet") as f:
            test_df = pd.read_parquet(f)

    df = pd.concat([train_df, test_df], ignore_index=True)
    print(f"[INFO] Dataset loaded: {len(df)} records, {df['attack_cat'].nunique()} attack categories")
    return df


def extract_knowledge(df):
    """Extract a compact, AI-usable knowledge base from the dataset."""

    # ── 1. Attack category overview ──────────────────────────────────────────
    counts = df["attack_cat"].value_counts().to_dict()
    total = len(df)
    attack_summary = {
        cat: {
            "count": int(cnt),
            "pct": round(cnt / total * 100, 2)
        }
        for cat, cnt in counts.items()
    }

    # ── 2. Per-category feature statistics ───────────────────────────────────
    numeric_cols = ["dur", "sbytes", "dbytes", "rate", "spkts", "dpkts",
                    "sloss", "dloss", "sjit", "djit", "sload", "dload"]
    numeric_cols = [c for c in numeric_cols if c in df.columns]

    category_profiles = {}
    for cat in df["attack_cat"].unique():
        sub = df[df["attack_cat"] == cat]
        profile = {}
        for col in numeric_cols:
            m = float(sub[col].mean())
            profile[col] = round(m, 4)

        # Most common protocol and service
        if "proto" in df.columns:
            profile["top_proto"] = sub["proto"].value_counts().index[0] if len(sub) > 0 else "tcp"
        if "service" in df.columns:
            profile["top_service"] = sub["service"].value_counts().index[0] if len(sub) > 0 else "-"
        if "state" in df.columns:
            profile["top_state"] = sub["state"].value_counts().index[0] if len(sub) > 0 else "FIN"

        category_profiles[cat] = profile

    # ── 3. Human-readable attack descriptions ────────────────────────────────
    attack_descriptions = {
        "Normal": {
            "description": "Legitimate network traffic with normal behavioral patterns.",
            "indicators": ["Stable connection rates", "Expected packet sizes", "Normal session durations"],
            "mitigations": ["Baseline monitoring", "Anomaly detection systems"],
        },
        "Generic": {
            "description": "Generic attack technique not fitting a specific category — often brute-force or protocol abuse.",
            "indicators": ["High packet rates", "Unusual flag combinations", "Repeated connection attempts"],
            "commands": ["nmap -sS <target>", "hydra -l admin -P passwords.txt <target>"],
            "mitigations": ["Rate limiting", "IP blocklisting", "IDS rules for unusual flag patterns"],
            "defense_commands": ["iptables -A INPUT -m limit --limit 10/min -j ACCEPT",
                                 "fail2ban-client status"],
        },
        "Exploits": {
            "description": "Attacks exploiting known software vulnerabilities (CVEs) for remote code execution or privilege escalation.",
            "indicators": ["Unexpected payloads in traffic", "Connections to unusual ports", "Large spike in bytes sent to service"],
            "commands": ["msfconsole", "searchsploit <service>", "exploit/multi/handler"],
            "mitigations": ["Patch management", "WAF deployment", "Service version hardening"],
            "defense_commands": ["dpkg -l | grep <package>", "apt-get update && apt-get upgrade",
                                 "ufw enable"],
        },
        "Fuzzers": {
            "description": "Automated input fuzzing to discover vulnerabilities by sending malformed or random data.",
            "indicators": ["High volume of malformed requests", "Elevated error rates", "Connection resets"],
            "commands": ["wfuzz -c -z file,wordlist.txt http://target/FUZZ",
                         "ffuf -w wordlist.txt -u http://target/FUZZ"],
            "mitigations": ["Input validation", "Web application firewall", "Error handling hardening"],
            "defense_commands": ["grep '400\\|500' /var/log/apache2/access.log | wc -l",
                                 "fail2ban-client status"],
        },
        "DoS": {
            "description": "Denial of Service attacks that overwhelm target resources to cause unavailability.",
            "indicators": ["Sudden traffic spike", "High SYN packet rate", "Server CPU at 100%", "Connection timeouts"],
            "commands": ["hping3 -S --flood -V -p 80 <target>",
                         "slowhttptest -c 500 -H -g -o test -i 10 -r 200 -t GET -u http://target"],
            "mitigations": ["SYN cookies", "Rate limiting", "CDN/DDoS protection", "ISP-level filtering"],
            "defense_commands": ["netstat -n | awk '/SYN_RECV/ {print $5}' | cut -d: -f1 | sort | uniq -c | sort -n",
                                 "iptables -A INPUT -p tcp --syn -m limit --limit 1/s -j ACCEPT"],
        },
        "Reconnaissance": {
            "description": "Information-gathering phase: scanning, enumeration, and fingerprinting of targets before attack.",
            "indicators": ["Port scan patterns", "Multiple probes from same IP", "DNS enumeration bursts"],
            "commands": ["nmap -sV -p- <target>", "nmap -O <target>",
                         "aws s3 ls", "aws s3api get-bucket-acl --bucket <name>"],
            "mitigations": ["IDS/IPS with scan detection", "Honeypots", "Rate-limiting probes", "Firewall logging"],
            "defense_commands": ["nmap -sn 192.168.1.0/24",
                                 "tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'",
                                 "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=ListBuckets"],
        },
        "Analysis": {
            "description": "Traffic analysis and protocol inspection attacks — often MITM or passive interception.",
            "indicators": ["ARP spoofing", "Unusual ICMP traffic", "Protocol anomalies"],
            "commands": ["tcpdump -i eth0 -w capture.pcap",
                         "arpspoof -i eth0 -t <victim> <gateway>"],
            "mitigations": ["Encrypted communications (TLS)", "Static ARP entries", "Network segmentation"],
            "defense_commands": ["arp -n", "arping -I eth0 <gateway>", "openssl s_client -connect <host>:443"],
        },
        "Backdoor": {
            "description": "Persistent unauthorized access mechanism installed post-exploitation to maintain foothold.",
            "indicators": ["Unusual outbound connections", "New cron jobs or services", "Modified system binaries"],
            "commands": ["netcat -lvp 4444", "meterpreter > run persistence"],
            "mitigations": ["File integrity monitoring", "Endpoint detection", "Network egress filtering"],
            "defense_commands": ["find / -mtime -1 -type f 2>/dev/null",
                                 "netstat -tulpn | grep LISTEN",
                                 "crontab -l && ls /etc/cron*"],
        },
        "Shellcode": {
            "description": "Machine-code payloads injected into vulnerable processes to execute arbitrary commands.",
            "indicators": ["NOP sled patterns in traffic", "Unusual memory addresses in payloads", "Buffer overflow patterns"],
            "commands": ["msfvenom -p linux/x86/shell_reverse_tcp LHOST=<ip> LPORT=4444 -f elf"],
            "mitigations": ["ASLR/DEP/NX bit enabled", "Stack canaries", "Seccomp filters"],
            "defense_commands": ["cat /proc/sys/kernel/randomize_va_space",
                                 "checksec --file=./binary",
                                 "sysctl kernel.exec-shield"],
        },
        "Worms": {
            "description": "Self-propagating malware that spreads across networks by exploiting vulnerabilities autonomously.",
            "indicators": ["Network broadcast storms", "High outbound connection rate", "Unexpected port 445/139 activity"],
            "commands": ["nmap -p 445 192.168.1.0/24 --open"],
            "mitigations": ["Network segmentation", "Patch SMB vulnerabilities", "Host-based firewalls"],
            "defense_commands": ["iptables -A INPUT -p tcp --dport 445 -j DROP",
                                 "smb client list",
                                 "netstat -an | grep 445"],
        },
    }

    # ── 4. Protocol distribution ─────────────────────────────────────────────
    proto_dist = {}
    if "proto" in df.columns:
        proto_dist = {
            k: int(v) for k, v in df["proto"].value_counts().head(10).to_dict().items()
        }

    # ── 5. Feature importance hints (based on mean differences vs normal) ────
    normal_means = {}
    if "Normal" in category_profiles:
        normal_means = category_profiles["Normal"]

    feature_importance = {}
    for col in numeric_cols:
        if col in normal_means:
            nval = normal_means[col]
            diffs = {}
            for cat, prof in category_profiles.items():
                if cat == "Normal":
                    continue
                val = prof.get(col, nval)
                if nval > 0:
                    diffs[cat] = round((val - nval) / max(nval, 0.001), 2)
            if diffs:
                feature_importance[col] = diffs

    knowledge = {
        "dataset": "UNSW-NB15 Network Intrusion Detection Dataset",
        "total_records": total,
        "attack_summary": attack_summary,
        "category_profiles": category_profiles,
        "attack_descriptions": attack_descriptions,
        "protocol_distribution": proto_dist,
        "feature_importance": feature_importance,
    }

    return knowledge


def build_compact_prompt_context(knowledge):
    """
    Build a compact text summary of the knowledge base.
    This is injected into the Groq AI system prompt.
    """
    lines = [
        "=== CYBERSECURITY KNOWLEDGE BASE (from UNSW-NB15 Dataset) ===",
        f"Dataset: {knowledge['dataset']} | Records: {knowledge['total_records']:,}",
        "",
        "ATTACK CATEGORIES (real network traffic analysis):",
    ]

    for cat, info in knowledge["attack_summary"].items():
        lines.append(f"  • {cat}: {info['count']:,} samples ({info['pct']}%)")

    lines.append("")
    lines.append("ATTACK DESCRIPTIONS, INDICATORS & COMMANDS:")
    for cat, desc in knowledge["attack_descriptions"].items():
        if cat == "Normal":
            continue
        lines.append(f"\n[{cat.upper()}]")
        lines.append(f"  Description: {desc['description']}")
        lines.append(f"  Indicators: {', '.join(desc.get('indicators', []))}")
        if "commands" in desc:
            lines.append(f"  Attack commands: {' | '.join(desc['commands'][:2])}")
        if "defense_commands" in desc:
            lines.append(f"  Defense commands: {' | '.join(desc['defense_commands'][:2])}")
        if "mitigations" in desc:
            lines.append(f"  Mitigations: {', '.join(desc['mitigations'])}")

    lines.append("\n=== END KNOWLEDGE BASE ===")
    return "\n".join(lines)


def main():
    df = load_dataset()
    knowledge = extract_knowledge(df)
    knowledge["prompt_context"] = build_compact_prompt_context(knowledge)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Knowledge base saved to: {OUTPUT_PATH}")
    print(f"[INFO] Prompt context length: {len(knowledge['prompt_context'])} characters")
    print("[INFO] Attack categories found:", list(knowledge["attack_summary"].keys()))


if __name__ == "__main__":
    main()
