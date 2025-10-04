from fastapi import FastAPI, Request, Response
from fastapi.responses import Response
import sqlite3, hashlib

app = FastAPI()

# --- Initialize SQLite Database ---
def init_db():
    conn = sqlite3.connect("views.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS views (
            ip_hash TEXT PRIMARY KEY,
            count INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Helper to record a view ---
def log_view(ip):
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    conn = sqlite3.connect("views.db")
    c = conn.cursor()
    c.execute("SELECT count FROM views WHERE ip_hash=?", (ip_hash,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE views SET count = count + 1 WHERE ip_hash=?", (ip_hash,))
    else:
        c.execute("INSERT INTO views (ip_hash, count) VALUES (?, ?)", (ip_hash, 1))
    conn.commit()
    conn.close()

# --- Helper to fetch stats ---
def get_stats():
    conn = sqlite3.connect("views.db")
    c = conn.cursor()
    c.execute("SELECT SUM(count), COUNT(*) FROM views")
    total_views, unique_visitors = c.fetchone()
    conn.close()
    total_views = total_views or 0
    unique_visitors = unique_visitors or 0
    avg_views = round(total_views / unique_visitors, 2) if unique_visitors > 0 else 0
    return total_views, unique_visitors, avg_views

# --- API Endpoint ---
@app.get("/stats")
async def stats(request: Request):
    ip = request.client.host or "unknown"
    log_view(ip)
    total_views, unique_visitors, avg_views = get_stats()

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="250" height="80">
      <rect width="250" height="80" fill="#1e1e2e" rx="10"/>
      <text x="15" y="25" fill="#ffffff" font-size="14">👁️ Total Views: {total_views}</text>
      <text x="15" y="45" fill="#ffffff" font-size="14">👤 Unique Users: {unique_visitors}</text>
      <text x="15" y="65" fill="#ffffff" font-size="14">📈 Avg/User: {avg_views}</text>
    </svg>
    """
    return Response(content=svg, media_type="image/svg+xml")
