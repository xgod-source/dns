from flask import Flask, request, jsonify
import sqlite3
from cloudflare import update_dns
from datetime import datetime
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")

# Fungsi untuk ambil IP dari request (fallback jika tidak pakai ?ip=)
def get_request_ip():
    if request.environ.get("HTTP_X_FORWARDED_FOR"):
        ip = request.environ["HTTP_X_FORWARDED_FOR"]
    else:
        ip = request.remote_addr
    return ip

# Inisialisasi database kalau belum ada
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subdomain TEXT UNIQUE NOT NULL,
                token TEXT NOT NULL,
                ip TEXT,
                updated_at TEXT
            )
        ''')
        conn.commit()

# Main endpoint: update IP
@app.route("/update", methods=["GET"])
def update():
    sub = request.args.get("sub")
    token = request.args.get("token")
    ip = request.args.get("ip") or get_request_ip()

    if not sub or not token:
        return jsonify({"success": False, "message": "Parameter 'sub' dan 'token' wajib ada"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT token FROM records WHERE subdomain = ?", (sub,))
        row = cur.fetchone()

        if not row:
            return jsonify({"success": False, "message": f"Subdomain '{sub}' not listed"}), 404

        if row[0] != token:
            return jsonify({"success": False, "message": "Token not valid"}), 403

        # Update Cloudflare
        ok, msg = update_dns(sub, ip)

        if ok:
            cur.execute("UPDATE records SET ip = ?, updated_at = ? WHERE subdomain = ?", (ip, datetime.now(), sub))
            conn.commit()
            return jsonify({"success": True, "message": msg, "ip": ip})
        else:
            return jsonify({"success": False, "message": msg}), 500

# Run server
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
