import sqlite3
from pathlib import Path

db = Path(__file__).parent / "open_s3_lab.db"
conn = sqlite3.connect(db)
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('tables:', tables)
try:
    cnt = cur.execute('SELECT count(*) FROM actions').fetchone()[0]
    print('actions count:', cnt)
except Exception as e:
    print('actions not present or error:', e)
conn.close()
