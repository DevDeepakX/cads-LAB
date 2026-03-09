from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import json
import sqlite3
import os
import re
import secrets
import uuid
from datetime import datetime
import random
from typing import Optional
import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system env variables
    pass

app = Flask(__name__)
# Use a secure random secret key unless provided via env
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_urlsafe(32)

# ── Groq API configuration ─────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# Default: llama-3.3-70b-versatile (fastest, high quality)
# Alternatives: mixtral-8x7b-32768  |  llama3-8b-8192  |  gemma2-9b-it
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Cyber knowledge base (built from UNSW-NB15 dataset) ─────────────────────
_CYBER_KNOWLEDGE_PROMPT = ""
_CYBER_KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "src", "cyber_knowledge.json")
try:
    with open(_CYBER_KNOWLEDGE_PATH, "r", encoding="utf-8") as _kf:
        import json as _json
        _kdata = _json.load(_kf)
        _CYBER_KNOWLEDGE_PROMPT = _kdata.get("prompt_context", "")
    print(f"[INFO] Cyber knowledge base loaded ({len(_CYBER_KNOWLEDGE_PROMPT)} chars)")
except Exception as _ke:
    print(f"[WARNING] Could not load cyber_knowledge.json: {_ke}")
    print("[INFO] Run: python src/build_cyber_knowledge.py  to build the knowledge base.")

# Ensure logs dir and database exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
OPEN_S3_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "open_s3_lab", "open_s3_lab.db")
PWNDORA_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "pwndora_lab", "pwndora_lab.db")
NETWORK_RECON_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "network_recon_lab", "network_recon_lab.db")


def get_lab_db_path(lab_id):
    """Return the database path for a given lab."""
    lab_paths = {
        "s3": OPEN_S3_DB_PATH,
        "pwndora": PWNDORA_DB_PATH,
        "network": NETWORK_RECON_DB_PATH,
    }
    return lab_paths.get(lab_id, OPEN_S3_DB_PATH)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lab_name TEXT,
            lab_id TEXT,
            score INTEGER,
            attempts INTEGER,
            detection_speed REAL,
            correct_commands INTEGER,
            mitigation_success INTEGER,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def get_s3_db_connection():
    conn = sqlite3.connect(OPEN_S3_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_lab_db_connection(lab_id):
    db_path = get_lab_db_path(lab_id)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_open_s3_db():
    conn = None
    try:
        conn = sqlite3.connect(OPEN_S3_DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_lab_id TEXT,
                timestamp TEXT,
                mode TEXT,
                command TEXT,
                outcome TEXT,
                details TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attack_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_lab_id TEXT,
                timestamp TEXT,
                command TEXT,
                outcome TEXT,
                details TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS defense_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_lab_id TEXT,
                timestamp TEXT,
                command TEXT,
                outcome TEXT,
                details TEXT
            )
        """)
        conn.commit()
    except Exception:
        pass
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def record_action(command: str, mode: Optional[str], outcome: str, details: Optional[dict] = None):
    """Record executed terminal commands and high-level actions into the lab-specific DB.

    `details` will be stored as a JSON string when provided.
    """
    try:
        lab_id = session.get("lab_id")
        # determine lab type id used for lab DB selection
        name = session.get("lab_name", "")
        if "Open S3" in name or name.lower().startswith("open s3"):
            lab_type_id = "s3"
        elif "PwnDora" in name or name.lower().startswith("pwndora"):
            lab_type_id = "pwndora"
        elif "Network" in name or name.lower().startswith("network"):
            lab_type_id = "network"
        else:
            lab_type_id = "s3"
        
        conn = get_lab_db_connection(lab_type_id)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO actions (session_lab_id, timestamp, mode, command, outcome, details) VALUES (?, ?, ?, ?, ?, ?)",
            (
                lab_id,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                mode,
                command,
                outcome,
                json.dumps(details) if details is not None else None,
            ),
        )
        # Also record into per-mode execution tables for easier separation
        if mode == "attack":
            try:
                cur.execute(
                    "INSERT INTO attack_executions (session_lab_id, timestamp, command, outcome, details) VALUES (?, ?, ?, ?, ?)",
                    (
                        lab_id,
                        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        command,
                        outcome,
                        json.dumps(details) if details is not None else None,
                    ),
                )
            except Exception:
                pass
        elif mode == "defense":
            try:
                cur.execute(
                    "INSERT INTO defense_executions (session_lab_id, timestamp, command, outcome, details) VALUES (?, ?, ?, ?, ?)",
                    (
                        session.get("lab_id"),
                        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        command,
                        outcome,
                        json.dumps(details) if details is not None else None,
                    ),
                )
            except Exception:
                pass

        conn.commit()
        conn.close()
    except Exception:
        pass


def get_session_lab_type():
    name = session.get("lab_name", "")
    if "Open S3" in name or name.lower().startswith("open s3"):
        return "s3"
    if "PwnDora" in name or name.lower().startswith("pwndora"):
        return "pwndora"
    if "Network" in name or name.lower().startswith("network"):
        return "network"
    return "s3"


def get_lab_ips(lab_type):
    """Return a list of IP addresses relevant to the specified lab."""
    ips = []
    try:
        conn = get_lab_db_connection(lab_type)
        cur = conn.cursor()
        if lab_type == "s3":
            try:
                cur.execute("SELECT DISTINCT requester_ip FROM access_logs WHERE requester_ip IS NOT NULL")
                ips = [r[0] for r in cur.fetchall() if r[0]]
            except Exception:
                ips = []
        elif lab_type == "pwndora":
            try:
                cur.execute("SELECT DISTINCT ip_address FROM sessions WHERE ip_address IS NOT NULL")
                ips = [r[0] for r in cur.fetchall() if r[0]]
            except Exception:
                ips = []
        elif lab_type == "network":
            try:
                cur.execute("SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL")
                ips = [r[0] for r in cur.fetchall() if r[0]]
                # include traffic src/dst
                cur.execute("SELECT DISTINCT src_ip FROM network_traffic WHERE src_ip IS NOT NULL")
                ips += [r[0] for r in cur.fetchall() if r[0]]
                cur.execute("SELECT DISTINCT dst_ip FROM network_traffic WHERE dst_ip IS NOT NULL")
                ips += [r[0] for r in cur.fetchall() if r[0]]
            except Exception:
                ips = []
        conn.close()
    except Exception:
        ips = []
    # dedupe and return up to 10
    seen = []
    for ip in ips:
        if ip not in seen:
            seen.append(ip)
    return seen[:10]


def _session_log_path():
    """Return the path to the current session's log file."""
    session_id = session.get("lab_id", "unknown")
    return os.path.join(LOGS_DIR, f"lab_{session_id}.json")


def _ensure_session_log():
    """Ensure a per-session log file exists for the current lab session."""
    try:
        log_file = _session_log_path()
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump({"session_id": session.get("lab_id"), "events": []}, f)
    except Exception:
        pass


def generate_log(action: str, source_ip: str, description: str):
    """Generate a log entry for the current session's activity."""
    try:
        session_id = session.get("lab_id", "unknown")
        log_file = os.path.join(LOGS_DIR, f"lab_{session_id}.json")
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "source_ip": source_ip,
            "description": description
        }
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                data = json.load(f)
            data["events"].append(log_entry)
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=2)
    except Exception:
        pass


def bot_actions_after_command():
    """Simple rule-based bot actions executed after each user command.
    - If user selected 'defense', an AI Attack Bot will generate attacks.
    - If user selected 'attack', an AI Defense Bot will detect/mitigate attacks.
    """
    try:
        mode = session.get("mode")
        state = session.get("lab_state")
        out = session.get("terminal_output", [])

        # AI Attack Bot (when user is defending)
        if mode == "defense":
            level = session.get("level", "Beginner")
            try:
                sconn = get_s3_db_connection()
                cur = sconn.cursor()
                cur.execute("SELECT detection_modifier FROM levels WHERE name=?", (level,))
                row = cur.fetchone()
                modifier = float(row[0]) if row else 0.3
                sconn.close()
            except Exception:
                modifier = 0.3

            probe_chance = 0.2 + modifier * 0.5
            if state in ("initialized", "recon") and random.random() < probe_chance:
                out.append("[ai-attack] Automated attacker is probing the environment")
                generate_log("PortScan", "203.0.113.9", "Automated reconnaissance")
                if random.random() < (0.4 + modifier * 0.4):
                    session["lab_state"] = "attack_started"
                    session["attack_started_at"] = datetime.utcnow().timestamp()
                    generate_log("AutomatedAttack", "203.0.113.9", "Attempted object access")

        # AI Defense Bot (when user is attacking)
        if mode == "attack":
            level = session.get("level", "Beginner")
            try:
                sconn = get_s3_db_connection()
                cur = sconn.cursor()
                cur.execute("SELECT detection_modifier FROM levels WHERE name=?", (level,))
                row = cur.fetchone()
                modifier = float(row[0]) if row else 0.3
                sconn.close()
            except Exception:
                modifier = 0.3

            detected = False
            if state == "attack_started" and not session.get("attack_detected_at"):
                base = 0.25 + modifier * 0.5
                started = session.get("attack_started_at") or datetime.utcnow().timestamp()
                age = max(0, datetime.utcnow().timestamp() - started)
                age_boost = min(1.0, age / 60.0)
                detect_prob = min(0.95, base + age_boost * 0.3)
                if random.random() < detect_prob:
                    detected = True

            if detected:
                out.append("[ai-defense] Automated defense system flagged suspicious activity")
                session["attack_detected_at"] = datetime.utcnow().timestamp()
                session["lab_state"] = "attack_detected"
                generate_log("IntrusionDetected", "10.0.0.5", "Automated detection: suspicious S3 access")
                if level == "Advanced" and random.random() < 0.7:
                    out.append("[ai-defense] Automated mitigation applied: public access blocked")
                    generate_log("PutPublicAccessBlock", "INTERNAL", "Auto mitigation by defense AI")
                    session["lab_state"] = "mitigation_applied"
                    session["mitigation_success"] = 1

        session["terminal_output"] = out
    except Exception:
        pass


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LAB LIST ----------------
@app.route("/labs")
def labs():
    return render_template("labs.html")


# ---------------- START LAB ----------------
@app.route("/lab/pwndora")
def pwndora_lab():
    # Show introduction page for PwnDora Challenge lab
    lab_what = (
        "The PwnDora Challenge is a web application security lab named after the famous Pandora's Box. "
        "It simulates a vulnerable web application with multiple security flaws including injection vulnerabilities, "
        "broken authentication, cross-site scripting (XSS), insecure deserialization, and more OWASP Top 10 vulnerabilities. "
        "Your mission is to identify these weaknesses and either exploit them or defend against them."
    )
    lab_why = (
        "Web application vulnerabilities remain one of the most common attack vectors. "
        "The OWASP Top 10 represents the most critical security risks to web applications, affecting millions of sites worldwide. "
        "By mastering these vulnerabilities in a safe sandbox, you'll be able to build secure applications and protect against real-world threats."
    )
    lab_learn = (
        "• Identification and exploitation of SQL injection, XSS, and CSRF vulnerabilities\n"
        "• Bypassing authentication and session management controls\n"
        "• Discovering and exploiting information disclosure issues\n"
        "• Testing and fixing broken access controls\n"
        "• Implementing input validation and output encoding\n"
        "• Securing web applications against common attack patterns"
    )
    lab_platform_value = (
        "PwnDora offers a realistic web application environment where you can practice ethical hacking and defensive techniques. "
        "All data is synthetic and poses no risk. Learn through hands-on exploitation, understand how defenses work, and develop "
        "the skills to secure modern web applications against evolving threats."
    )
    
    return render_template(
        "lab_intro.html",
        lab_title="PwnDora Challenge",
        lab_id="pwndora",
        lab_what=lab_what,
        lab_why=lab_why,
        lab_learn=lab_learn,
        lab_platform_value=lab_platform_value
    )


@app.route("/lab/pwndora/select_mode")
def pwndora_select_mode():
    # Show mode selection page for PwnDora lab
    return render_template("lab_mode_select.html", lab_title="PwnDora Challenge", lab_id="pwndora")


@app.route("/lab/pwndora/start", methods=["POST"])
def pwndora_start():
    # Initialize lab session with selected mode and level
    mode = request.form.get("mode")
    level = request.form.get("level")
    
    if mode not in ("attack", "defense") or level not in ("Beginner", "Intermediate", "Advanced"):
        return "Invalid mode or level", 400
    
    # Initialize a new lab session for PwnDora
    session.clear()
    session["lab_id"] = uuid.uuid4().hex
    session["lab_name"] = "PwnDora Challenge"
    session["lab_state"] = "initialized"
    session["terminal_output"] = []
    session["score"] = 0
    session["attempts"] = 0
    session["correct_commands"] = 0
    session["mitigation_success"] = 0
    session["attack_started_at"] = None
    session["attack_detected_at"] = None
    session["mode"] = mode
    session["level"] = level
    session["cheatsheet_views_pwndora"] = 0
    session["cheatsheet_last_access_pwndora"] = None

    # create fresh per-session log file
    _ensure_session_log()

    return redirect(url_for("terminal"))


@app.route("/lab/s3")
def s3_lab():
    # Show introduction page for Open S3 Bucket lab
    lab_what = (
        "The Open S3 Bucket lab simulates a real-world cloud misconfiguration scenario. "
        "You will work with Amazon S3 buckets that have been incorrectly configured with public access permissions. "
        "Your task is to discover these misconfigurations, understand the security implications, and apply the correct remediation steps."
    )
    lab_why = (
        "S3 bucket misconfigurations are one of the leading causes of data breaches in cloud environments. "
        "Organizations worldwide have exposed sensitive data, credentials, and intellectual property through publicly accessible S3 buckets. "
        "Understanding how these vulnerabilities occur and how to prevent them is critical for any cloud security professional."
    )
    lab_learn = (
        "• How to enumerate and discover S3 buckets\n"
        "• How to identify public access configurations\n"
        "• How to exfiltrate data from misconfigured buckets\n"
        "• How to apply security controls (public access blocks, ACLs, bucket policies)\n"
        "• How to detect and respond to S3-based attacks"
    )
    lab_platform_value = (
        "This platform provides a safe, sandbox environment where you can practice real cloud attack and defense techniques "
        "without any risk to actual data or infrastructure. All datasets are completely fictional and dummy data. "
        "Learn hands-on skills through realistic scenarios, receive immediate feedback, and progressively master cloud security."
    )
    
    return render_template(
        "lab_intro.html",
        lab_title="Open S3 Bucket Lab",
        lab_id="s3",
        lab_what=lab_what,
        lab_why=lab_why,
        lab_learn=lab_learn,
        lab_platform_value=lab_platform_value
    )


@app.route("/lab/s3/select_mode")
def s3_select_mode():
    # Show mode selection page for S3 lab
    return render_template("lab_mode_select.html", lab_title="Open S3 Bucket Lab", lab_id="s3")


@app.route("/lab/s3/start", methods=["POST"])
def s3_start():
    # Initialize lab session with selected mode and level
    mode = request.form.get("mode")
    level = request.form.get("level")
    
    if mode not in ("attack", "defense") or level not in ("Beginner", "Intermediate", "Advanced"):
        return "Invalid mode or level", 400
    
    # Initialize a new lab session for the Open S3 Bucket lab
    session.clear()
    session["lab_id"] = uuid.uuid4().hex
    session["lab_name"] = "Open S3 Bucket"
    session["lab_state"] = "initialized"
    session["terminal_output"] = []
    session["score"] = 0
    session["attempts"] = 0
    session["correct_commands"] = 0
    session["mitigation_success"] = 0
    session["attack_started_at"] = None
    session["attack_detected_at"] = None
    session["mode"] = mode
    session["level"] = level

    # create fresh per-session log file
    _ensure_session_log()

    return redirect(url_for("terminal"))

@app.route("/lab/network")
def network_lab():
    # Show introduction page for Network Recon lab
    lab_what = (
        "The Network Reconnaissance lab simulates enterprise network environments with multiple hosts, services, and potential vulnerabilities. "
        "You will practice network scanning techniques, service enumeration, vulnerability identification, and network defense strategies. "
        "This lab mirrors real-world penetration testing scenarios where reconnaissance is the critical first phase of any engagement."
    )
    lab_why = (
        "Network reconnaissance and enumeration are foundational skills in cybersecurity. "
        "Attackers use these techniques to map networks, identify targets, and find entry points. "
        "Defenders must understand these methods to implement proper network segmentation, monitoring, and intrusion detection. "
        "Mastering network recon is essential for both offensive and defensive security roles."
    )
    lab_learn = (
        "• Network mapping and topology discovery using tools like nmap and traceroute\n"
        "• Service enumeration and version identification\n"
        "• Vulnerability scanning and assessment\n"
        "• Network segmentation and access control bypass techniques\n"
        "• Implementing network defenses (firewalls, IDS/IPS, network monitoring)\n"
        "• Analyzing network traffic and detecting suspicious activity"
    )
    lab_platform_value = (
        "Network Reconnaissance provides a realistic multi-host environment with simulated services and vulnerabilities. "
        "Practice advanced reconnaissance techniques safely in a sandbox where all data is fictional. "
        "Gain practical experience in network mapping, vulnerability assessment, and defense implementation. "
        "Build expertise in network security without any impact on real systems."
    )
    
    return render_template(
        "lab_intro.html",
        lab_title="Network Reconnaissance Lab",
        lab_id="network",
        lab_what=lab_what,
        lab_why=lab_why,
        lab_learn=lab_learn,
        lab_platform_value=lab_platform_value
    )


@app.route("/lab/network/select_mode")
def network_select_mode():
    # Show mode selection page for Network Recon lab
    return render_template("lab_mode_select.html", lab_title="Network Reconnaissance Lab", lab_id="network")


@app.route("/lab/network/start", methods=["POST"])
def network_start():
    # Initialize lab session with selected mode and level
    mode = request.form.get("mode")
    level = request.form.get("level")
    
    if mode not in ("attack", "defense") or level not in ("Beginner", "Intermediate", "Advanced"):
        return "Invalid mode or level", 400
    
    # Initialize a new lab session for Network Recon
    session.clear()
    session["lab_id"] = uuid.uuid4().hex
    session["lab_name"] = "Network Recon"
    session["lab_state"] = "initialized"
    session["terminal_output"] = []
    session["score"] = 0
    session["attempts"] = 0
    session["correct_commands"] = 0
    session["mitigation_success"] = 0
    session["attack_started_at"] = None
    session["attack_detected_at"] = None
    session["mode"] = mode
    session["level"] = level
    session["cheatsheet_views_network"] = 0
    session["cheatsheet_last_access_network"] = None

    # create fresh per-session log file
    _ensure_session_log()

    return redirect(url_for("terminal"))


@app.route("/lobby", methods=["GET", "POST"])
def lobby():
    """Lobby where player selects difficulty level before starting lab."""
    if request.method == "POST":
        level = request.form.get("level")
        if level in ("Beginner", "Intermediate", "Advanced"):
            session["level"] = level
            session.setdefault("terminal_output", []).append(f"[lobby] Selected level: {level}")
        return redirect(url_for("s3_lab"))
    # Simple endpoint to show available levels (frontend can use template)
    conn = None
    levels = []
    try:
        conn = get_s3_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name,description FROM levels ORDER BY id")
        levels = cur.fetchall()
    except Exception:
        levels = [("Beginner", "Slow/lenient AI detection"), ("Intermediate", "Moderate"), ("Advanced", "Aggressive")]
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

    return render_template("labs.html", levels=levels)


@app.route('/admin/commands')
def admin_commands():
    """Admin UI: browse attack/defense command definitions and executions."""
    s3conn = None
    attack_cmds = []
    defense_cmds = []
    attack_exec = []
    defense_exec = []
    try:
        s3conn = get_s3_db_connection()
        cur = s3conn.cursor()
        cur.execute('SELECT id,name,pattern,hint,example FROM attack_commands ORDER BY id')
        attack_cmds = cur.fetchall()
        cur.execute('SELECT id,name,pattern,hint,example FROM defense_commands ORDER BY id')
        defense_cmds = cur.fetchall()
        cur.execute('SELECT id,session_lab_id,timestamp,command,outcome,details FROM attack_executions ORDER BY id DESC LIMIT 200')
        attack_exec = cur.fetchall()
        cur.execute('SELECT id,session_lab_id,timestamp,command,outcome,details FROM defense_executions ORDER BY id DESC LIMIT 200')
        defense_exec = cur.fetchall()
    except Exception:
        # keep empty lists on error
        pass
    finally:
        try:
            if s3conn:
                s3conn.close()
        except Exception:
            pass

    return render_template('admin_commands.html',
                           attack_cmds=attack_cmds,
                           defense_cmds=defense_cmds,
                           attack_exec=attack_exec,
                           defense_exec=defense_exec)


# ---------------- ATTACK INFO PAGE ----------------
@app.route("/attack")
def attack_phase():
    # Simulate an automated attack event when user opens the attack info page
    session.setdefault("terminal_output", [])
    session["terminal_output"].append("[attack-page] Simulated attacker scanning S3 buckets...")
    generate_log("ListBuckets", "198.51.100.12", "Automated enumeration")
    generate_log("GetObject", "185.220.101.45", "Automated unauthorized object access")

    # escalate lab state
    if session.get("lab_state") in ("initialized", "recon"):
        session["lab_state"] = "attack_started"
        session["attack_started_at"] = datetime.utcnow().timestamp()

    # If defense bot is active (mode=attack), detection may occur automatically
    if session.get("mode") == "attack":
        session["attack_detected_at"] = datetime.utcnow().timestamp()
        session["lab_state"] = "attack_detected"
        generate_log("IntrusionDetected", "10.0.0.5", "Automated detection: suspicious S3 access")
        session["terminal_output"].append("[auto-detect] Defense systems detected suspicious activity")

    return render_template("attack.html")


@app.route("/cheatsheet")
def cheatsheet():
    # Fetch command definitions from lab-specific DB and present a full cheat-sheet
    mode = session.get("mode")
    commands = []
    
    # Determine lab type
    if "Open S3" in session.get("lab_name", ""):
        lab_type_id = "s3"
    elif "PwnDora" in session.get("lab_name", ""):
        lab_type_id = "pwndora"
    elif "Network" in session.get("lab_name", ""):
        lab_type_id = "network"
    else:
        lab_type_id = "s3"
    
    try:
        conn = get_lab_db_connection(lab_type_id)
        cur = conn.cursor()
        if mode == "attack":
            cur.execute('SELECT name,pattern,hint,example,level,category FROM attack_commands ORDER BY id')
            rows = cur.fetchall()
        elif mode == "defense":
            cur.execute('SELECT name,pattern,hint,example,level,category FROM defense_commands ORDER BY id')
            rows = cur.fetchall()
        else:
            # return both attack and defense commands when no mode selected
            cur.execute('SELECT name,pattern,hint,example,level,category, "attack" as mode FROM attack_commands ORDER BY id')
            arows = cur.fetchall()
            cur.execute('SELECT name,pattern,hint,example,level,category, "defense" as mode FROM defense_commands ORDER BY id')
            drows = cur.fetchall()
            rows = arows + drows

        for r in rows:
            try:
                name = r[0]
                pattern = r[1]
                hint = r[2]
                example = r[3]
                level = r[4]
                category = r[5]
                mode_field = r[6] if len(r) > 6 else mode
            except Exception:
                name = r['name']
                pattern = r['pattern']
                hint = r['hint']
                example = r['example']
                level = r.get('level')
                category = r.get('category')
                mode_field = r.get('mode', mode)

            howto = f"Run in the lab terminal: {example} — replace placeholders like {{bucket}}/{{key}} as needed. {hint}"
            commands.append({
                'name': name,
                'pattern': pattern,
                'hint': hint,
                'example': example,
                'level': level,
                'category': category,
                'mode': mode_field,
                'howto': howto,
            })
    except Exception:
        commands = []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return render_template("cheatsheet.html", commands=commands, mode=mode)


@app.route("/cheatsheet_api")
def cheatsheet_api():
    """Return cheatsheet commands as JSON for modal display with lab-specific rate limiting."""
    import time
    
    mode = session.get("mode")
    lab_type_id = get_session_lab_type()
    
    # Determine lab-specific rate limit keys
    lab_map = {
        "s3": ("cheatsheet_views_s3", "cheatsheet_last_access_s3"),
        "pwndora": ("cheatsheet_views_pwndora", "cheatsheet_last_access_pwndora"),
        "network": ("cheatsheet_views_network", "cheatsheet_last_access_network"),
    }
    
    views_key, access_key = lab_map.get(lab_type_id, ("cheatsheet_views", "cheatsheet_last_access"))
    
    # Get current state from session
    views_count = session.get(views_key, 0)
    last_access_time = session.get(access_key)
    current_time = time.time()
    
    # Check rate limiting: 3 free views, then 5-minute cooldown
    if views_count >= 3:
        if last_access_time is None:
            # First time hitting limit, set the timer
            session[access_key] = current_time
        else:
            # Check if 5 minutes (300 seconds) have passed
            time_since_last = current_time - last_access_time
            if time_since_last < 300:  # 5 minutes = 300 seconds
                remaining = 300 - time_since_last
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Cheatsheet for {lab_type_id} lab available again in {int(remaining)} seconds',
                    'commands': [],
                    'mode': mode
                }), 429
            else:
                # 5 minutes have passed, reset the counter for this lab
                session[views_key] = 0
                session[access_key] = None
                views_count = 0
    
    # Increment view counter for this lab
    session[views_key] = views_count + 1
    remaining_free_views = max(0, 3 - (views_count + 1))
    
    commands = []
    
    try:
        conn = get_lab_db_connection(lab_type_id)
        cur = conn.cursor()
        if mode == "attack":
            cur.execute('SELECT name,pattern,hint,example,level,category FROM attack_commands ORDER BY id')
            rows = cur.fetchall()
        elif mode == "defense":
            cur.execute('SELECT name,pattern,hint,example,level,category FROM defense_commands ORDER BY id')
            rows = cur.fetchall()
        else:
            # return both attack and defense commands when no mode selected
            cur.execute('SELECT name,pattern,hint,example,level,category FROM attack_commands ORDER BY id')
            arows = cur.fetchall()
            cur.execute('SELECT name,pattern,hint,example,level,category FROM defense_commands ORDER BY id')
            drows = cur.fetchall()
            rows = arows + drows

        for r in rows:
            try:
                name = r[0]
                pattern = r[1]
                hint = r[2]
                example = r[3]
                level = r[4]
                category = r[5]
            except Exception:
                name = r['name']
                pattern = r['pattern']
                hint = r['hint']
                example = r['example']
                level = r.get('level')
                category = r.get('category')

            description = hint or category or ""
            commands.append({
                'name': name,
                'pattern': pattern,
                'description': description,
                'example': example,
                'level': level,
            })
    except Exception as e:
        commands = []
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Also include Linux commands from the shared linux_commands.db filtered by mode
    try:
        import os
        linux_db_path = os.path.join(os.path.dirname(__file__), 'data', 'linux_commands.db')
        lconn = sqlite3.connect(linux_db_path)
        lcur = lconn.cursor()
        if mode == 'attack':
            lcur.execute("SELECT name,pattern,description,example,level,category FROM linux_commands WHERE (mode IS NULL OR mode IN ('attack','both')) ORDER BY id")
        elif mode == 'defense':
            lcur.execute("SELECT name,pattern,description,example,level,category FROM linux_commands WHERE (mode IS NULL OR mode IN ('defense','both')) ORDER BY id")
        else:
            lcur.execute("SELECT name,pattern,description,example,level,category FROM linux_commands ORDER BY id")

        lrows = lcur.fetchall()
        for r in lrows:
            try:
                lname = r[0]
                lpattern = r[1]
                ldesc = r[2]
                lex = r[3]
                llevel = r[4]
                lcat = r[5] or 'Linux Commands'
            except Exception:
                lname = r['name']
                lpattern = r['pattern']
                ldesc = r.get('description')
                lex = r.get('example')
                llevel = r.get('level')
                lcat = r.get('category') or 'Linux Commands'

            commands.append({
                'name': lname,
                'pattern': lpattern,
                'description': ldesc or lcat,
                'example': lex,
                'level': llevel,
            })
    except Exception:
        pass
    finally:
        try:
            lconn.close()
        except Exception:
            pass

    return jsonify({
        'commands': commands,
        'mode': mode,
        'remaining_free_views': remaining_free_views,
        'lab': lab_type_id
    })


# ---------------- TERMINAL ENGINE ----------------
@app.route("/terminal", methods=["GET", "POST"])
def terminal():
    if "terminal_output" not in session:
        session["terminal_output"] = []
    def append_output(line):
        session["terminal_output"].append(line)

    if request.method == "POST":
        cmd = request.form.get("command", "").strip()
        # sanitize and prevent arbitrary execution: only treat strings
        cmd = re.sub(r"\s+", " ", cmd)
        append_output(f"$ {cmd}")

        # Validate state
        state = session.get("lab_state", "initialized")

        # Determine lab type and open its DB
        lab_type = get_session_lab_type()
        lab_conn = None
        try:
            lab_conn = get_lab_db_connection(lab_type)
            lcur = lab_conn.cursor()
        except Exception:
            lab_conn = None

        # Recognize a variety of commands (IP/network, basic linux, lab-specific)
        if re.search(r"(^|\s)(ifconfig|ip\s+addr|ip\s+a)(\s|$)", cmd, re.I):
            # Simulate ifconfig/ip output using lab IPs
            ips = get_lab_ips(lab_type)
            append_output("eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500")
            for i, ip in enumerate(ips):
                append_output(f"    inet {ip}  netmask 255.255.255.0  broadcast {ip.rsplit('.',1)[0]}.255")
            append_output("lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536")
            outcome = "ifconfig_ok"
        elif re.search(r"(^|\s)(ipconfig)(\s|$)", cmd, re.I):
            ips = get_lab_ips(lab_type)
            for ip in ips:
                append_output(f"Ethernet adapter Local Area Connection:\n   IPv4 Address. . . . . . . . . . . : {ip}")
            outcome = "ipconfig_ok"
        elif re.search(r"^ls(\s+-[la]+)?(\s+.*)?$", cmd, re.I):
            # generic simulated file listing, contextual per lab
            # Matches: ls, ls -l, ls -a, ls -la, ls -al, etc.
            if lab_type == "s3":
                if "-l" in cmd:
                    append_output("-rw-r--r--  1 user  group  4096 Jan 15 10:30 reports")
                    append_output("-rw-r--r--  1 user  group  2048 Jan 15 10:30 images")
                    append_output("-rw-r--r--  1 user  group  1024 Jan 15 10:30 README.md")
                    append_output("-rw-r--r--  1 user  group   512 Jan 15 10:30 NOTES.txt")
                else:
                    append_output("reports  images  README.md  NOTES.txt")
            elif lab_type == "pwndora":
                if "-l" in cmd:
                    append_output("-rw-r--r--  1 user  group  2048 Jan 15 10:30 index.php")
                    append_output("-rw-r--r--  1 user  group  1024 Jan 15 10:30 admin.php")
                    append_output("drwxr-xr-x  2 user  group  4096 Jan 15 10:30 uploads")
                    append_output("-rw-r--r--  1 user  group   512 Jan 15 10:30 README.md")
                else:
                    append_output("index.php  admin.php  uploads  README.md")
            else:
                if "-l" in cmd:
                    append_output("dr-xr-xr-x  2 root root  4096 Jan 15 10:30 bin")
                    append_output("dr-xr-xr-x  2 root root  4096 Jan 15 10:30 etc")
                    append_output("drwxr-xr-x  3 user user 4096 Jan 15 10:30 home")
                    append_output("drwxr-xr-x 14 root root  4096 Jan 15 10:30 var")
                    append_output("drwxrwxrwt 10 root root  4096 Jan 15 10:30 tmp")
                else:
                    append_output("bin  etc  home  var  tmp")
            outcome = "ls"
        elif cmd.startswith("cat "):
            # show canned content for common files
            fn = cmd.split(" ", 1)[1].strip()
            if fn.endswith("/etc/issue") or fn == "/etc/issue":
                append_output("Ubuntu 20.04.6 LTS \nKernel fake-kernel 5.4.0")
            elif fn.endswith("README.md"):
                append_output("This is a fictional lab environment. All data is dummy and safe.")
            else:
                append_output(f"cat: {fn}: No such file or directory")
            outcome = "cat"
        elif cmd.strip() == "whoami":
            append_output("player")
            outcome = "whoami"
        elif cmd.strip() == "pwd":
            append_output("/home/player")
            outcome = "pwd"
        elif cmd.strip().startswith("uname"):
            append_output("Linux lab-machine 5.15.0-91-generic #101-Ubuntu SMP Tue Nov 14 13:30:08 UTC 2023 x86_64 GNU/Linux")
            outcome = "uname"
        elif re.search(r"aws\s+s3\s+ls\s*$", cmd, re.I):
            # List S3 buckets
            append_output("2024-01-15 10:23:45        0 monish-s3-lab/")
            append_output("2024-01-15 10:25:12        0 open-lab-public/")
            append_output("2024-01-15 10:26:33        0 secure-vault-prod/")
            session["lab_state"] = "recon"
            session["correct_commands"] = session.get("correct_commands", 0) + 1
            generate_log("ListBuckets", "198.51.100.12", "Enumerated S3 buckets")
            outcome = "aws_s3_ls"
        elif re.search(r"aws\s+s3\s+ls\s+s3://", cmd, re.I):
            # List bucket contents
            append_output("2024-01-15 10:30:15        4096 data/")
            append_output("2024-01-15 10:31:22      102400 credentials.csv")
            append_output("2024-01-15 10:32:01      245760 database_backup.sql")
            append_output("2024-01-15 10:33:44       51200 config.yml")
            session["lab_state"] = "recon"
            outcome = "aws_s3_ls_bucket"
        elif re.search(r"aws\s+s3\s+cp", cmd, re.I):
            # Copy/download file
            append_output("download: s3://bucket/file.txt to ./file.txt")
            append_output("Completed 1.2 MiB/1.2 MiB (2.4 MiB/s) with 0 file(s) remaining")
            session["lab_state"] = "attack_started"
            session["attack_started_at"] = datetime.utcnow().timestamp()
            generate_log("GetObject", "185.220.101.45", "Downloaded S3 object")
            outcome = "aws_s3_cp"
        elif re.search(r"aws\s+s3\s+sync", cmd, re.I):
            # Sync bucket
            append_output("download: s3://bucket/file1.txt")
            append_output("download: s3://bucket/file2.txt")
            append_output("download: s3://bucket/data/file3.bin")
            append_output("Completed 48.6 MiB/48.6 MiB (12.4 MiB/s) with 0 file(s) remaining")
            session["lab_state"] = "attack_started"
            session["attack_started_at"] = datetime.utcnow().timestamp()
            generate_log("SyncBucket", "185.220.101.45", "Synced entire bucket")
            outcome = "aws_s3_sync"
        elif re.search(r"aws\s+s3api\s+put-public-access-block", cmd, re.I):
            # Block public access
            append_output("Done!")
            session["lab_state"] = "mitigation_applied"
            session["mitigation_success"] = 1
            generate_log("PutPublicAccessBlock", "INTERNAL", "Applied public access block")
            outcome = "aws_put_public_block"
        elif re.search(r"nmap\s+-", cmd, re.I):
            # Network scan
            append_output("Starting Nmap 7.93 ( https://nmap.org ) at 2024-01-15 10:45 UTC")
            append_output("Nmap scan report for 192.168.1.100")
            append_output("Host is up (0.0042s latency).")
            append_output("PORT    STATE SERVICE")
            append_output("22/tcp  open  ssh")
            append_output("80/tcp  open  http")
            append_output("443/tcp open  https")
            append_output("3306/tcp open  mysql")
            append_output("Nmap done at 2024-01-15 10:45 UTC; 1 IP address scanned in 0.45 seconds")
            session["lab_state"] = "recon"
            generate_log("Nmap", "198.51.100.12", "Network scan completed")
            outcome = "nmap_scan"
        elif re.search(r"curl\s+https?://", cmd, re.I):
            # HTTP request
            append_output("<!DOCTYPE html>")
            append_output("<html>")
            append_output("<body>")
            append_output("<h1>Welcome to Lab Server</h1>")
            append_output("<p>Admin panel: /admin</p>")
            append_output("<p>API endpoint: /api/v1</p>")
            append_output("</body>")
            append_output("</html>")
            session["lab_state"] = "recon"
            outcome = "curl_request"
        elif re.search(r"find\s+", cmd, re.I):
            # File search
            append_output("./config/.env")
            append_output("./data/secrets.txt")
            append_output("./backup/admin.sql")
            append_output("./logs/access.log")
            session["lab_state"] = "recon"
            outcome = "find_search"
        elif re.search(r"grep\s+", cmd, re.I):
            # Pattern search
            append_output("password=admin123")
            append_output("api_key=sk_live_x1y2z3...")
            append_output("db_host=db.internal.prod")
            session["lab_state"] = "recon"
            outcome = "grep_search"
        elif re.search(r"cat\s+", cmd, re.I):
            # Read file
            fn = cmd.split(" ", 1)[1].strip()
            if "config" in fn.lower() or "env" in fn.lower():
                append_output("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
                append_output("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
                append_output("DB_PASSWORD=SuperSecret123!")
            elif "credential" in fn.lower():
                append_output("root:x:0:0:root:/root:/bin/bash")
                append_output("admin:x:1000:1000:admin user:/home/admin:/bin/bash")
            else:
                append_output(f"Contents of {fn}: sample data")
            outcome = "cat_file"
        else:
            # Fallback: use improved pattern detection for unmatched commands
            is_recon = bool(re.search(r"(aws\s+s3\s+ls|enumerate|nmap|whois|dig|traceroute|find|grep|locate)", cmd, re.I))
            is_attack = bool(re.search(r"(aws\s+s3\s+(cp|sync|mv)|get-object|getobject|exploit|upload|access|download|retrieve|exfiltrate)", cmd, re.I))
            is_mitigate = bool(re.search(r"(put-public-access-block|block-public|put-bucket|revoke|fix|remediate|disable|deny|restrict|encrypt|enable|protect)", cmd, re.I))

            if is_recon:
                append_output("[recon] Command recognized as reconnaissance. Try one of the specific commands like 'aws s3 ls' or 'nmap -sV <target>'")
                session["lab_state"] = "recon"
                outcome = "recon_partial"
            elif is_attack:
                append_output("[attack] Command recognized as attack. Execute 'aws s3 cp' or 'aws s3 sync' to simulate data exfiltration")
                session["lab_state"] = "attack_started"
                outcome = "attack_partial"
            elif is_mitigate:
                append_output("[defense] Mitigation command recognized. Use 'aws s3api put-public-access-block' with full parameters")
                session["lab_state"] = "mitigation_applied"
                outcome = "mitigate_partial"

        # Record the executed action into the lab-specific DB
        try:
            record_action(cmd, session.get("mode"), outcome, {"lab_state": session.get("lab_state")})
        except Exception:
            pass

        bot_actions_after_command()

        # close lab connection if opened
        try:
            if lab_conn:
                lab_conn.close()
        except Exception:
            pass

    return render_template("terminal.html", output=session["terminal_output"])


# ──────────────────────────────────────────────────────────────────────────────
# GROQ AI COMMAND ANALYZER
# ──────────────────────────────────────────────────────────────────────────────

def call_groq_command_analysis(cmd, output_lines, lab_name, mode, lab_state):
    """Call Groq API to analyze a terminal command and return a short AI insight.

    This is called after every terminal command to give inline AI feedback.
    Uses a fast, concise prompt (not the full knowledge base) for speed.

    Returns:
        str: 2-4 line AI analysis, or '' if unavailable
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        return ""

    try:
        output_preview = "\n".join(output_lines[-6:]) if output_lines else "(no output)"
        mode_label = mode or "explore"

        system_prompt = (
            f"You are CADS-AI, a cybersecurity lab terminal assistant for '{lab_name}' lab.\n"
            f"The student is in {mode_label.upper()} mode. Lab state: {lab_state}.\n\n"
            "Your job: After the student runs a terminal command, give a SHORT (2-4 line) analysis:\n"
            "  1. What this command does in a security context\n"
            "  2. What the output reveals (attack surface, vulnerability, defense status)\n"
            "  3. ONE specific next command to try (with the exact syntax)\n\n"
            "RULES:\n"
            "- Be concise. Max 4 lines total. No long explanations.\n"
            "- Always suggest 1 concrete next command.\n"
            "- Use the UNSW-NB15 dataset context when relevant "
            "(e.g. Reconnaissance=10,491 samples, DoS=12,264 samples).\n"
            "- Format: plain text only, no markdown headers.\n"
            "- Start immediately with the insight (no greeting, no 'Sure!')."
        )

        user_msg = (
            f"Command: {cmd}\n"
            f"Output:\n{output_preview}\n\n"
            "Give your 2-4 line security analysis and next step."
        )

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_msg},
                ],
                "temperature": 0.5,
                "max_tokens": 180,
                "top_p": 0.9,
                "stream": False,
            },
            timeout=12,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("choices"):
                text = data["choices"][0]["message"]["content"].strip()
                print(f"[DEBUG] Groq cmd-analysis OK: {len(text)} chars")
                return text
        else:
            print(f"[WARNING] Groq cmd-analysis: {response.status_code}")
        return ""

    except requests.exceptions.Timeout:
        print("[WARNING] Groq cmd-analysis timeout")
        return ""
    except Exception as e:
        print(f"[WARNING] Groq cmd-analysis error: {e}")
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# AJAX TERMINAL EXECUTE  (used by the JS frontend for no-reload terminal)
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/terminal_execute", methods=["POST"])
def api_terminal_execute():
    """AJAX endpoint: run a terminal command, return new output lines + AI analysis.

    Request JSON: { "command": "..." }
    Response JSON: {
        "new_lines": [...],          # lines added this execution
        "ai_analysis": "...",        # Groq AI insight (empty string if unavailable)
        "lab_state": "...",
        "score": ...,
        "mode": "..."
    }
    """
    try:
        data = request.get_json() or {}
        cmd = (data.get("command") or "").strip()
        cmd = re.sub(r"\s+", " ", cmd)

        if not cmd:
            return jsonify({"new_lines": [], "ai_analysis": "", "lab_state": session.get("lab_state"), "score": session.get("score", 0), "mode": session.get("mode")})

        # Track lines added in this call
        before_count = len(session.get("terminal_output", []))

        if "terminal_output" not in session:
            session["terminal_output"] = []

        def append_output(line):
            session["terminal_output"].append(line)

        append_output(f"$ {cmd}")

        state    = session.get("lab_state", "initialized")
        lab_type = get_session_lab_type()
        lab_conn = None
        outcome  = "unknown"

        try:
            lab_conn = get_lab_db_connection(lab_type)
        except Exception:
            lab_conn = None

        # ── Command dispatch (same logic as terminal POST) ──────────────────
        if re.search(r"(^|\s)(ifconfig|ip\s+addr|ip\s+a)(\s|$)", cmd, re.I):
            ips = get_lab_ips(lab_type)
            append_output("eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500")
            for ip in ips:
                append_output(f"    inet {ip}  netmask 255.255.255.0  broadcast {ip.rsplit('.',1)[0]}.255")
            append_output("lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536")
            outcome = "ifconfig_ok"

        elif re.search(r"(^|\s)(ipconfig)(\s|$)", cmd, re.I):
            ips = get_lab_ips(lab_type)
            for ip in ips:
                append_output(f"Ethernet adapter Local Area Connection:\n   IPv4 Address. . . : {ip}")
            outcome = "ipconfig_ok"

        elif re.search(r"^ls(\s+-[la]+)?(\s+.*)?$", cmd, re.I):
            if lab_type == "s3":
                append_output("reports  images  README.md  NOTES.txt") if "-l" not in cmd else [
                    append_output("-rw-r--r--  1 user group 4096 Jan 15 10:30 reports"),
                    append_output("-rw-r--r--  1 user group 2048 Jan 15 10:30 images"),
                    append_output("-rw-r--r--  1 user group 1024 Jan 15 10:30 README.md"),
                ]
            elif lab_type == "pwndora":
                append_output("index.php  admin.php  uploads  README.md")
            else:
                append_output("bin  etc  home  var  tmp")
            outcome = "ls"

        elif cmd.strip() == "whoami":
            append_output("player")
            outcome = "whoami"

        elif cmd.strip() == "pwd":
            append_output("/home/player")
            outcome = "pwd"

        elif cmd.strip().startswith("uname"):
            append_output("Linux lab-machine 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux")
            outcome = "uname"

        elif cmd.strip() == "id":
            append_output("uid=1000(player) gid=1000(player) groups=1000(player),4(adm),27(sudo)")
            outcome = "id"

        elif cmd.strip() == "hostname":
            append_output("cads-lab-vm")
            outcome = "hostname"

        elif re.search(r"^history", cmd, re.I):
            history = session.get("terminal_output", [])
            cmds = [l for l in history if l.startswith("$ ")][-15:]
            for i, c in enumerate(cmds, 1):
                append_output(f"  {i:3}  {c[2:]}")
            outcome = "history"

        elif re.search(r"aws\s+s3\s+ls\s*$", cmd, re.I):
            append_output("2024-01-15 10:23:45        0 monish-s3-lab/")
            append_output("2024-01-15 10:25:12        0 open-lab-public/")
            append_output("2024-01-15 10:26:33        0 secure-vault-prod/")
            session["lab_state"] = "recon"
            session["correct_commands"] = session.get("correct_commands", 0) + 1
            generate_log("ListBuckets", "198.51.100.12", "Enumerated S3 buckets")
            outcome = "aws_s3_ls"

        elif re.search(r"aws\s+s3\s+ls\s+s3://", cmd, re.I):
            append_output("2024-01-15 10:30:15        4096 data/")
            append_output("2024-01-15 10:31:22      102400 credentials.csv")
            append_output("2024-01-15 10:32:01      245760 database_backup.sql")
            append_output("2024-01-15 10:33:44       51200 config.yml")
            session["lab_state"] = "recon"
            outcome = "aws_s3_ls_bucket"

        elif re.search(r"aws\s+s3\s+cp", cmd, re.I):
            append_output("download: s3://bucket/file.txt to ./file.txt")
            append_output("Completed 1.2 MiB/1.2 MiB (2.4 MiB/s) with 0 file(s) remaining")
            session["lab_state"] = "attack_started"
            session["attack_started_at"] = datetime.utcnow().timestamp()
            generate_log("GetObject", "185.220.101.45", "Downloaded S3 object")
            outcome = "aws_s3_cp"

        elif re.search(r"aws\s+s3\s+sync", cmd, re.I):
            append_output("download: s3://bucket/file1.txt")
            append_output("download: s3://bucket/file2.txt")
            append_output("download: s3://bucket/data/file3.bin")
            append_output("Completed 48.6 MiB/48.6 MiB (12.4 MiB/s) with 0 file(s) remaining")
            session["lab_state"] = "attack_started"
            session["attack_started_at"] = datetime.utcnow().timestamp()
            generate_log("SyncBucket", "185.220.101.45", "Synced entire bucket")
            outcome = "aws_s3_sync"

        elif re.search(r"aws\s+s3api\s+put-public-access-block", cmd, re.I):
            append_output("Done!")
            session["lab_state"] = "mitigation_applied"
            session["mitigation_success"] = 1
            generate_log("PutPublicAccessBlock", "INTERNAL", "Applied public access block")
            outcome = "aws_put_public_block"

        elif re.search(r"aws\s+s3api\s+(get-bucket-acl|get-bucket-policy|head-bucket)", cmd, re.I):
            append_output('{"Owner": {"DisplayName": "labadmin", "ID": "abc123"}}')
            append_output('{"Grants": [{"Grantee": {"Type": "Group", "URI": "AllUsers"}, "Permission": "READ"}]}')
            session["lab_state"] = "recon"
            outcome = "aws_s3api_inspect"

        elif re.search(r"nmap\s+-", cmd, re.I):
            append_output("Starting Nmap 7.93 at 2024-01-15 10:45 UTC")
            append_output("Nmap scan report for 192.168.1.100")
            append_output("Host is up (0.0042s latency).")
            append_output("PORT      STATE SERVICE  VERSION")
            append_output("22/tcp    open  ssh      OpenSSH 8.2p1")
            append_output("80/tcp    open  http     Apache 2.4.41")
            append_output("443/tcp   open  https    nginx 1.18.0")
            append_output("3306/tcp  open  mysql    MySQL 8.0.25")
            append_output("Nmap done: 1 IP address scanned in 0.45 seconds")
            session["lab_state"] = "recon"
            generate_log("Nmap", "198.51.100.12", "Network scan completed")
            outcome = "nmap_scan"

        elif re.search(r"curl\s+https?://", cmd, re.I):
            append_output("HTTP/1.1 200 OK")
            append_output("Server: Apache/2.4.41")
            append_output("X-Powered-By: PHP/7.4.3")
            append_output("")
            append_output("<h1>Welcome to Lab Server</h1>")
            append_output("<p>Admin panel: /admin</p>")
            append_output("<p>API endpoint: /api/v1</p>")
            session["lab_state"] = "recon"
            outcome = "curl_request"

        elif re.search(r"find\s+", cmd, re.I):
            append_output("./config/.env")
            append_output("./data/secrets.txt")
            append_output("./backup/admin.sql")
            append_output("./logs/access.log")
            session["lab_state"] = "recon"
            outcome = "find_search"

        elif re.search(r"grep\s+", cmd, re.I):
            append_output("password=admin123")
            append_output("api_key=sk_live_x1y2z3...")
            append_output("db_host=db.internal.prod")
            session["lab_state"] = "recon"
            outcome = "grep_search"

        elif re.search(r"cat\s+", cmd, re.I):
            fn = cmd.split(" ", 1)[1].strip()
            if "config" in fn.lower() or "env" in fn.lower():
                append_output("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
                append_output("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
                append_output("DB_PASSWORD=SuperSecret123!")
            elif "credential" in fn.lower() or "passwd" in fn.lower():
                append_output("root:x:0:0:root:/root:/bin/bash")
                append_output("admin:x:1000:1000:admin user:/home/admin:/bin/bash")
            else:
                append_output(f"cat: {fn}: No such file or directory")
            outcome = "cat_file"

        elif re.search(r"(netstat|ss)\s*", cmd, re.I):
            append_output("Active Internet connections (only servers)")
            append_output("Proto Recv-Q Send-Q Local Address    Foreign Address  State")
            append_output("tcp        0      0 0.0.0.0:22       0.0.0.0:*        LISTEN")
            append_output("tcp        0      0 0.0.0.0:80       0.0.0.0:*        LISTEN")
            append_output("tcp        0      0 127.0.0.1:3306   0.0.0.0:*        LISTEN")
            session["lab_state"] = "recon"
            outcome = "netstat"

        elif re.search(r"iptables|ufw|firewall", cmd, re.I):
            append_output("Chain INPUT (policy DROP)")
            append_output("target     prot  opt  source         destination")
            append_output("ACCEPT     all   --   anywhere       anywhere      state RELATED,ESTABLISHED")
            append_output("ACCEPT     tcp   --   anywhere       anywhere      tcp dpt:ssh")
            session["lab_state"] = "mitigation_applied"
            session["mitigation_success"] = 1
            outcome = "firewall_cmd"

        elif re.search(r"tcpdump", cmd, re.I):
            append_output("tcpdump: listening on eth0, link-type EN10MB")
            append_output("10:45:01.123456 IP 198.51.100.12.54321 > 10.0.0.5.80: Flags [S]")
            append_output("10:45:01.234567 IP 10.0.0.5.80 > 198.51.100.12.54321: Flags [S.]")
            append_output("10:45:01.345678 IP 203.0.113.9.12345 > 10.0.0.5.22: Flags [S]")
            append_output("^C")
            append_output("3 packets captured")
            session["lab_state"] = "recon"
            outcome = "tcpdump"

        elif re.search(r"(whois|dig|nslookup)\s+", cmd, re.I):
            append_output("Domain: target.example.com")
            append_output("Registrar: Example Registrar, Inc.")
            append_output("Name Server: ns1.example.com")
            append_output("Name Server: ns2.example.com")
            append_output(";; ANSWER SECTION:")
            append_output("target.example.com. 300 IN A 192.168.1.100")
            session["lab_state"] = "recon"
            outcome = "dns_lookup"

        elif re.search(r"sudo\s+", cmd, re.I):
            append_output("[sudo] password for player: ")
            append_output("Sorry, user player may not run sudo on lab-machine.")
            outcome = "sudo_denied"

        elif re.search(r"ssh\s+", cmd, re.I):
            append_output("ssh: connect to host target port 22: Connection refused")
            outcome = "ssh_attempt"

        elif re.search(r"(ping)\s+", cmd, re.I):
            append_output("PING 192.168.1.100 56(84) bytes of data.")
            append_output("64 bytes from 192.168.1.100: icmp_seq=1 ttl=64 time=0.421 ms")
            append_output("64 bytes from 192.168.1.100: icmp_seq=2 ttl=64 time=0.398 ms")
            append_output("--- 192.168.1.100 ping statistics ---")
            append_output("2 packets transmitted, 2 received, 0% packet loss")
            session["lab_state"] = "recon"
            outcome = "ping"

        elif re.search(r"(traceroute|tracert)\s+", cmd, re.I):
            append_output("traceroute to 192.168.1.100 (192.168.1.100), 30 hops max")
            append_output(" 1  gateway (10.0.0.1)  0.5 ms  0.4 ms  0.3 ms")
            append_output(" 2  router (172.16.0.1)  2.1 ms  2.0 ms  1.9 ms")
            append_output(" 3  192.168.1.100  3.4 ms  3.2 ms  3.1 ms")
            session["lab_state"] = "recon"
            outcome = "traceroute"

        elif re.search(r"help\s*$", cmd, re.I):
            append_output("┌──────────────────────────────────────────────────────────────────────────┐")
            append_output("│ CADS PLATFORM — AVAILABLE COMMANDS                                       │")
            append_output("├──────────────────────────────────────────────────────────────────────────┤")
            append_output("│ RECONNAISSANCE:   aws s3 ls, nmap -sV <ip>, curl http://<target>         │")
            append_output("│ AWS CLOUD:        aws s3 ls s3://<bucket>, aws s3api get-bucket-acl      │")
            append_output("│ ATTACK VECTOR:    aws s3 cp s3://<bucket>/<file> ./, aws s3 sync         │")
            append_output("│ DEFENSE/FIX:      aws s3api put-public-access-block --bucket <name>      │")
            append_output("│ CORE LINUX:       ls, pwd, id, whoami, uname, find, grep, cat, help      │")
            append_output("│ NETWORKING:       nmap, ping, traceroute, netstat, dig, tcpdump          │")
            append_output("├──────────────────────────────────────────────────────────────────────────┤")
            append_output("│ PRO-TIP: Use the Cheat Sheet (TOP RIGHT) for automated command pasting!  │")
            append_output("└──────────────────────────────────────────────────────────────────────────┘")
            outcome = "help"


        elif cmd.strip() in ("clear", "cls"):
            session["terminal_output"] = []
            append_output("Terminal cleared.")
            outcome = "clear"

        else:
            is_recon    = bool(re.search(r"(aws\s+s3\s+ls|enumerate|nmap|whois|dig|traceroute|find|grep|locate)", cmd, re.I))
            is_attack   = bool(re.search(r"(aws\s+s3\s+(cp|sync|mv)|get-object|exploit|upload|download|exfiltrate)", cmd, re.I))
            is_mitigate = bool(re.search(r"(put-public-access-block|block-public|revoke|fix|remediate|disable|deny|restrict|encrypt|protect)", cmd, re.I))

            if is_recon:
                append_output("[recon] Reconnaissance pattern detected. Try: aws s3 ls  or  nmap -sV <target>")
                session["lab_state"] = "recon"
                outcome = "recon_partial"
            elif is_attack:
                append_output("[attack] Attack pattern detected. Try: aws s3 cp s3://bucket/file ./")
                session["lab_state"] = "attack_started"
                outcome = "attack_partial"
            elif is_mitigate:
                append_output("[defense] Mitigation pattern detected. Try: aws s3api put-public-access-block")
                session["lab_state"] = "mitigation_applied"
                outcome = "mitigate_partial"
            else:
                append_output(f"bash: {cmd.split()[0] if cmd else 'command'}: command not found")
                append_output("Type 'help' for available commands, or open the Cheat Sheet (🕵️).")
                outcome = "unknown"

        # Record the action
        try:
            record_action(cmd, session.get("mode"), outcome, {"lab_state": session.get("lab_state")})
        except Exception:
            pass

        bot_actions_after_command()

        # Close lab connection
        try:
            if lab_conn:
                lab_conn.close()
        except Exception:
            pass

        # ── Collect NEW lines added this call ───────────────────────────────
        all_output   = session.get("terminal_output", [])
        new_lines    = all_output[before_count:]

        # ── Call Groq AI to analyze the command ─────────────────────────────
        ai_analysis = call_groq_command_analysis(
            cmd,
            new_lines,
            session.get("lab_name", "Cybersecurity Lab"),
            session.get("mode", ""),
            session.get("lab_state", "initialized"),
        )

        return jsonify({
            "new_lines":   new_lines,
            "ai_analysis": ai_analysis,
            "lab_state":   session.get("lab_state"),
            "score":       session.get("score", 0),
            "mode":        session.get("mode"),
            "outcome":     outcome,
        })

    except Exception as e:
        print(f"[ERROR] api_terminal_execute: {e}")
        return jsonify({"new_lines": [f"Error: {e}"], "ai_analysis": "", "lab_state": None, "score": 0, "mode": None})


def get_session_logs():
    """Read and return log events for the current session."""
    try:
        log_file = _session_log_path()
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                data = json.load(f)
            events = []
            for ev in data.get('events', []):
                events.append({
                    'timestamp': ev.get('timestamp', ''),
                    'event':     ev.get('action', ev.get('event', 'Event')),
                    'action':    ev.get('action', ev.get('description', '')),
                    'source_ip': ev.get('source_ip', '-'),
                    'description': ev.get('description', ''),
                })
            return events
    except Exception:
        pass
    return []


# ---------------- VIEW LOGS ----------------
@app.route("/logs")
def view_logs():
    # Render session-specific logs as a timeline
    events = get_session_logs()
    return render_template("logs.html", logs=events)



@app.route("/api/logs")
def api_logs():
    """Return logs JSON for the current session (used by frontend timeline)."""
    events = get_session_logs()
    return jsonify({"events": events, "lab_state": session.get("lab_state")})


def is_cybersecurity_question(message):
    """Check if the question is cybersecurity/ethical hacking related."""
    cybersecurity_keywords = [
        'aws', 's3', 'bucket', 'reconnaissance', 'recon', 'scan', 'enumerate', 'vulnerability',
        'exploit', 'attack', 'defense', 'mitigation', 'secure', 'permission', 'access',
        'nmap', 'curl', 'command', 'bash', 'shell', 'injection', 'xss', 'sql', 'linux',
        'network', 'port', 'service', 'target', 'payload', 'technique', 'tool', 'ethical',
        'hacking', 'security', 'cyber', 'penetration', 'pentest', 'risk', 'threat',
        'firewall', 'iptables', 'route', 'tcpdump', 'wireshark', 'ssh', 'public', 'private',
        'key', 'certificate', 'hash', 'encrypt', 'decrypt', 'authentication', 'authorization',
        'ftp', 'http', 'https', 'telnet', 'dns', 'ldap', 'smb', 'rpc', 'docker', 'container',
        'api', 'endpoint', 'parameter', 'input', 'validation', 'sanitization', 'code'
    ]
    msg_lower = message.lower()
    return sum(1 for keyword in cybersecurity_keywords if keyword in msg_lower) > 0


@app.route('/chatbot_api', methods=['POST'])
def chatbot_api():
    """Enhanced chatbot responding ONLY to cybersecurity questions.
    
    This endpoint:
    1. Validates questions are cybersecurity-related
    2. Uses OpenAI API for intelligent responses (if key configured)
    3. Falls back to local database for commands & hints
    4. Lab-specific context and safety checks
    5. Comprehensive error handling
    """
    try:
        data = request.get_json() or {}
        msg = (data.get('message') or '').strip()
        
        if not msg:
            return jsonify({'reply': 'Please ask a cybersecurity-related question about the current lab (reconnaissance, techniques, defense, commands, etc.).'})

        # Safety: require a started lab session
        if not session.get('lab_id') or not session.get('lab_name'):
            return jsonify({'reply': 'Please start a lab session first (go to a lab introduction page and start it).'})

        # Forbidden/unsafe/illegal checks
        forbidden_terms = ['bomb', 'kill', 'murder', 'terror', 'weapon', 'how to hack bank', 'attack real', 
                          'bitcoin', 'ransomware', 'credit card', 'steal', 'girlfriend', 'homework', 'weather', 
                          'recipe', 'joke', 'sports', 'movie', 'music', 'love', 'dating']
        low = msg.lower()
        if any(term in low for term in forbidden_terms):
            return jsonify({'reply': 'I can only help with cybersecurity and ethical hacking topics related to this lab. Please ask about:\n• Reconnaissance commands\n• Security tools and techniques\n• Vulnerability assessment\n• Defense and mitigation strategies\n• Lab-specific security concepts'})

        # Validate if question is cybersecurity-related
        if not is_cybersecurity_question(msg):
            return jsonify({'reply': 'This question is not related to cybersecurity or ethical hacking. Please ask about:\n• Reconnaissance commands (nmap, aws s3, curl)\n• Security tools and techniques\n• Vulnerability assessment\n• Defense and mitigation strategies\n• Lab-specific security concepts'})

        # ── Try Groq API first (fast LLM inference + dataset knowledge) ────
        if GROQ_API_KEY:
            ai_response = call_groq_api(msg, session.get('lab_name', 'Cybersecurity Lab'))
            if ai_response:
                return jsonify({'reply': ai_response})

        # ── Fallback to local database lookup ───────────────────────────────
        return get_local_chatbot_response(msg, session.get('lab_name'))
        
    except Exception as e:
        print(f"[ERROR] Chatbot API error: {str(e)}")
        return jsonify({'reply': 'Assistant is unavailable right now. Please try again in a moment.'})


def call_groq_api(message, lab_name):
    """Call Groq API with dataset-grounded cybersecurity instructions.

    Groq provides ultra-fast LLM inference (Llama 3, Mixtral, Gemma).
    The system prompt is enriched with the UNSW-NB15 dataset knowledge.

    Args:
        message:  User's validated cybersecurity question
        lab_name: Current lab name for context

    Returns:
        str: AI response or None if API call fails
    """
    try:
        if not GROQ_API_KEY:
            print("[DEBUG] GROQ_API_KEY not configured")
            return None

        # ── System prompt: lab context + dataset knowledge ──────────────────
        system_prompt = f"""You are CADS-AI, an expert cybersecurity lab assistant for the '{lab_name}' lab on the
Cyber Attack Defense Simulation (CADS) platform.

You are trained on the UNSW-NB15 network intrusion detection dataset (257,673 real network traffic
records covering 9 attack categories). Use this dataset knowledge to ground your answers in
real attack patterns, statistical signatures, and evidence-based defense strategies.

{_CYBER_KNOWLEDGE_PROMPT}

══ YOUR ROLE ══
Help students understand cybersecurity concepts, attack techniques, and defense strategies
EXCLUSIVELY within this educational lab environment. ALL activities are simulated and ethical.

══ RESPOND ONLY TO ══
• Reconnaissance and enumeration techniques
• Security tools and commands (nmap, aws-cli, curl, netcat, wireshark, etc.)
• Vulnerability assessment and exploitation (ethical/lab only)
• Defense strategies, mitigations, and hardening
• Security concepts grounded in the UNSW-NB15 dataset patterns
• Lab-specific technical guidance and command syntax
• Intrusion detection and network forensics

══ DO NOT RESPOND TO ══
• General knowledge, small talk, or non-cybersecurity topics
• Real-world unauthorized access or illegal activities
• Off-topic subjects (weather, recipes, jokes, etc.)

══ RESPONSE FORMAT (follow every time) ══
1. One-line summary of the answer
2. Bullet points (•) for key information
3. Command examples in backtick code blocks
4. Bold **important terms**
5. Dataset insight: reference actual attack pattern from UNSW-NB15 when relevant
6. Practical next step or defense tip
Keep responses 200-350 words. Be technical, accurate, and educational.

For off-topic questions respond: "I can only assist with cybersecurity and ethical hacking for this
lab. Please ask about attack techniques, security commands, vulnerability assessment, or defense
strategies."""

        # ── Groq API request ─────────────────────────────────────────────────
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": message},
                ],
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9,
                "stream": False,
            },
            timeout=20,
        )

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and data["choices"]:
                reply = data["choices"][0]["message"]["content"].strip()
                print(f"[DEBUG] Groq API success: model={GROQ_MODEL}, tokens={data.get('usage', {}).get('total_tokens')}")
                return reply
            print(f"[ERROR] Unexpected Groq response format: {data}")
            return None

        elif response.status_code == 401:
            print("[ERROR] Groq API: Invalid API key (401)")
            return None
        elif response.status_code == 429:
            print("[ERROR] Groq API: Rate limit exceeded (429)")
            return None
        elif response.status_code == 503:
            print("[ERROR] Groq API: Service unavailable (503)")
            return None
        else:
            print(f"[ERROR] Groq API error: {response.status_code} - {response.text[:300]}")
            return None

    except requests.exceptions.Timeout:
        print("[WARNING] Groq API timeout (>20 seconds)")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[WARNING] Groq API connection failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error calling Groq: {e}")
        return None


def get_local_chatbot_response(msg, lab_name):
    """Get response from local database as fallback.
    
    Searches lab-specific command databases for relevant hints and examples.
    """
    try:
        lab_type = get_session_lab_type()
        matches = []
        
        # Try to find matching commands/hints in lab DBs
        try:
            conn = get_lab_db_connection(lab_type)
            cur = conn.cursor()
            for table in ('attack_commands', 'defense_commands'):
                try:
                    cur.execute(
                        f"SELECT name, pattern, hint, example FROM {table} WHERE name LIKE ? OR pattern LIKE ? OR hint LIKE ? OR example LIKE ? LIMIT 5",
                        tuple(['%'+msg+'%']*4)
                    )
                    rows = cur.fetchall()
                    for r in rows:
                        try:
                            # Handle both tuple and sqlite3.Row cases
                            if isinstance(r, tuple):
                                matches.append({
                                    'name': r[0],
                                    'pattern': r[1],
                                    'hint': r[2],
                                    'example': r[3]
                                })
                            else:
                                matches.append({
                                    'name': r['name'],
                                    'pattern': r['pattern'],
                                    'hint': r.get('hint'),
                                    'example': r.get('example')
                                })
                        except Exception as e:
                            print(f"[DEBUG] Error processing row: {e}")
                            continue
                except Exception as e:
                    print(f"[DEBUG] Error querying {table}: {e}")
                    continue
            
            conn.close()
        except Exception as e:
            print(f"[DEBUG] Error connecting to lab DB: {e}")
        
        # Try linux_commands DB if available
        try:
            linux_db_path = os.path.join(os.path.dirname(__file__), 'data', 'linux_commands.db')
            if os.path.exists(linux_db_path):
                lconn = sqlite3.connect(linux_db_path)
                lcur = lconn.cursor()
                lcur.execute(
                    "SELECT name, pattern, description, example FROM linux_commands WHERE name LIKE ? OR pattern LIKE ? OR description LIKE ? LIMIT 5",
                    ('%'+msg+'%', '%'+msg+'%', '%'+msg+'%')
                )
                lrows = lcur.fetchall()
                for r in lrows:
                    try:
                        matches.append({
                            'name': r[0],
                            'pattern': r[1],
                            'hint': r[2],
                            'example': r[3]
                        })
                    except Exception:
                        pass
                lconn.close()
        except Exception as e:
            print(f"[DEBUG] Error querying linux_commands: {e}")

        # If we found matches from database, return them
        if matches:
            parts = []
            for m in matches[:3]:  # Limit to 3 results
                name = m.get('name') or m.get('pattern', 'Command')
                hint = m.get('hint') or ''
                ex = m.get('example') or m.get('pattern') or ''
                if hint:
                    parts.append(f"**{name}**: {hint}\nExample: `{ex}`")
                else:
                    parts.append(f"**{name}**: `{ex}`")
            
            reply = "Here are relevant commands from the lab's database:\n\n" + "\n\n".join(parts)
            return jsonify({'reply': reply})

        # No direct matches; provide varied high-level lab guidance
        s3_guidance = [
            "**AWS S3 Reconnaissance**: Start with `aws s3 ls` to discover buckets. Once you identify a target, use `aws s3 ls s3://bucket-name` to enumerate objects. Check for publicly accessible files and permission misconfigurations.",
            "**S3 Enumeration Techniques**: Use `aws s3api head-bucket --bucket <name>` to check permissions. Try `aws s3api get-bucket-acl --bucket <name>` to analyze access control. Look for policies using `aws s3api get-bucket-policy --bucket <name>`.",
            "**S3 Exploitation Goals**: Identify overly permissive access controls. Download sensitive files with `aws s3 cp s3://bucket/file ./`. Once identified, demonstrate the risk. For mitigation, use `aws s3api put-public-access-block --bucket <name>` to block public access.",
            "**Defense Strategy**: Implement bucket policies restricting public access. Use IAM policies to limit S3 permissions. Enable versioning and MFA delete. Implement encryption and logging for compliance."
        ]
        
        pwndora_guidance = [
            "**Web Reconnaissance**: Use `curl http://target` to retrieve pages. Add `-v` flag for verbose headers: `curl -v http://target`. Look for directories, endpoints, and API information. Test for information disclosure.",
            "**Input Validation Testing**: Check for SQL injection in forms using payloads like `' OR '1'='1`. Test for XSS by injecting `<script>alert('xss')</script>`. Look for command injection by trying semicolons and pipe operators.",
            "**Vulnerability Discovery**: Enumerate parameters like `?id=1`, `?admin=true`. Try manipulation: `?admin=1`, `?role=admin`. Test authentication bypass. Look for hardcoded credentials in JavaScript.",
            "**Defense Perspective**: Implement input validation and sanitization. Use parameterized queries to prevent SQL injection. Apply context-appropriate output encoding. Implement strong authentication and authorization controls."
        ]
        
        network_guidance = [
            "**Network Reconnaissance**: Execute `nmap -sV <target>` to identify services. Use `nmap -p- <target>` for full port scan. Then probe specific services: `nmap -sC -sV -p 22,80,443 <target>`.",
            "**Service Enumeration**: Use `nc -zv <target> <port>` to check open ports. For HTTP: `curl -v http://target:port`. For SSH: `ssh -v user@target`. For DNS: `nslookup <domain>` and `dig <domain>`.",
            "**Path Discovery**: Map network topology using `traceroute <target>`. Identify intermediate hops and gateways. Use `netstat -tuln` locally to see listening services. Probe for hidden services on uncommon ports.",
            "**Securing Networks**: Implement firewall rules to restrict access. Disable unnecessary services. Use strong SSH configurations (disable root login, use key-based auth). Monitor with IDS/IPS systems."
        ]
        
        guidance = {
            's3': [s3_guidance[i % len(s3_guidance)] for i in range(1)],
            'pwndora': [pwndora_guidance[i % len(pwndora_guidance)] for i in range(1)],
            'network': [network_guidance[i % len(network_guidance)] for i in range(1)]
        }

        lab_type_key = lab_type or 's3'
        if lab_type_key in guidance:
            default_reply = guidance[lab_type_key][0]
        else:
            default_reply = 'Ask about reconnaissance techniques, security commands, vulnerability assessment, or defense strategies for this lab.'
        
        return jsonify({'reply': default_reply})
        
    except Exception as e:
        print(f"[ERROR] get_local_chatbot_response: {str(e)}")
        return jsonify({'reply': 'Assistant is unavailable right now. Please try again later.'})



@app.route("/select_mode", methods=["POST"])
def select_mode():
    mode = request.form.get("mode")
    if mode not in ("attack", "defense"):
        return ("Invalid mode"), 400
    session["mode"] = mode
    session.setdefault("terminal_output", []).append(f"[mode] Selected mode: {mode}")

    # Fetch hint-style guidance from the Open S3 DB for the selected mode
    try:
        conn = get_s3_db_connection()
        cur = conn.cursor()
        hints = []
        if mode == "attack":
            cur.execute("SELECT name,hint,example FROM attack_commands ORDER BY id LIMIT 10")
            hints = cur.fetchall()
        else:
            cur.execute("SELECT name,hint,example FROM defense_commands ORDER BY id LIMIT 10")
            hints = cur.fetchall()

        if hints:
            session.setdefault("terminal_output", []).append("[hints] Commands available in this mode:")
            for r in hints:
                # r may be a sqlite3.Row; format accordingly
                try:
                    name = r[0]
                    hint = r[1]
                    example = r[2]
                except Exception:
                    name = r['name']
                    hint = r['hint']
                    example = r['example']
                session.setdefault("terminal_output", []).append(f" - {name}: {hint} (e.g. {example})")
        # record the mode selection as an action
        try:
            record_action("select_mode", mode, "mode_selected", {"level": session.get("level")})
        except Exception:
            pass
    except Exception:
        # ignore db issues and keep original behavior
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return redirect(url_for("terminal"))


@app.route("/result", methods=["POST"])
def result():
    # Support optional form fields (from /solve) to apply mitigation
    selection = request.form.get("answer")
    applied_mitigation = False

    if selection == "public_bucket":
        # user applied correct mitigation
        session.setdefault("terminal_output", []).append("[solve] Applied public access block")
        generate_log("PutPublicAccessBlock", "INTERNAL", "Public access disabled via console")
        session["lab_state"] = "mitigation_applied"
        session["mitigation_success"] = 1
        applied_mitigation = True

    # finalize metrics and persist to DB
    session["attempts"] = session.get("attempts", 0) + 1
    result_text = "SUCCESS: Lab completed" if applied_mitigation else "COMPLETED: Review required"

    # compute detection speed
    started = session.get("attack_started_at")
    detected = session.get("attack_detected_at")
    detection_speed = None
    if started and detected:
        detection_speed = max(0.0, detected - started)

    correct = session.get("correct_commands", 0)
    mitigated = session.get("mitigation_success", 0)
    base_score = session.get("score", 0)
    # simple scoring formula
    total_score = base_score + correct * 10 + mitigated * 50
    if detection_speed:
        total_score = int(total_score - detection_speed)
    total_score = max(0, total_score)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO labs (lab_name, lab_id, score, attempts, detection_speed, correct_commands, mitigation_success, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session.get("lab_name", "Open S3 Bucket"),
            session.get("lab_id"),
            total_score,
            session.get("attempts", 1),
            detection_speed,
            correct,
            mitigated,
            "completed" if applied_mitigation else "completed",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()
    conn.close()

    # store final score in session
    session["score"] = total_score

    # record completion action
    try:
        record_action("lab_result", session.get("mode"), "completed", {"score": session.get("score"), "result": result_text})
    except Exception:
        pass

    return render_template(
        "result.html",
        result=result_text,
        score=session["score"],
        attempts=session["attempts"]
    )


# ---------------- RESET LAB ----------------
@app.route("/reset")
def reset_lab():
    # clear logs for this session and reset
    path = _session_log_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    session.clear()
    return render_template("reset.html")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
