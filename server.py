"""
Simple chatroom server.

Small Flask app that supports signup, login, sending messages, and polling messages.
This is written in a clear, simple way so another student can read and understand it.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

engine = create_engine("sqlite:///project.db",echo=False)

app = Flask(__name__)
CORS(app)

# ---------- Signup ----------

def find_user_by_email(email):
    """
    Look up a user row by email and return the row mapping or None.

    This runs a simple SELECT over the user table and compares emails.
    It returns the first matching row as a mapping.
    """
    with engine.connect() as conn:
        query = f"SELECT * FROM user"
        result = conn.execute(text(query))
        for row in result.mappings().all():
            if row.get("email") == email:
                return row
    return None


@app.route("/sinup", methods = ["POST"])
def singup():
    """
    Create a new user account.

    Expects JSON with username, email and password. Returns 201 on success.
    If username/email already exist, returns 409 with a helpful JSON error.
    """
    data = request.get_json(silent=True)
    user_name = data.get("username").strip()
    email_id = data.get("email").strip()
    passw = data.get("password")

    if not user_name or not email_id or not passw:
        return jsonify({"error" : "username, email & password required!"}), 400
    
    hashed_passwd = generate_password_hash(passw)
    with engine.begin() as conn:
        try:
            conn.execute(
                text("INSERT INTO user (username, email, password) VALUES (:u, :e, :p)"),
                {"u": user_name, "e": email_id, "p": hashed_passwd},
            )
        except IntegrityError:
            # username or email already exists
            return jsonify({"error": "username or email already exists"}), 409
    return jsonify({"status": "registered", "username": user_name, "email": email_id}), 201


# ---------- Login (email + password) ----------


@app.route("/login", methods=["POST"])
def login():
    """
    Login endpoint using email + password.

    Returns 200 with display username on success, 401 on failure.
    """
    data = request.get_json(silent=True)
    email = data.get("email").strip()
    passw = data.get("password").strip()

    if not email or not passw:
        return jsonify({"error": "email and password reqiered!"}), 400

    found = find_user_by_email(email)
    if not found:
        print(f"login: email not found with: {email}")
        return jsonify({"error" : "invalid email!"}), 401
    
    hashed_passwd = found.get("password")
    if not hashed_passwd:
        print(f"login: no password hash for user row: {found}")
        return jsonify({"error": "invalid credentials"}), 401
    
    if not check_password_hash(hashed_passwd,passw):
        print(f"ogin: password mismatch for email {email}")
        return jsonify({"error": "invalid credentials"}), 401
    
    # success->> return username (display name)
    return jsonify({"status": "ok", "username": found.get("username"), "email": found.get("email")}), 200

# ---------- Send message (email + password + message) ----------

@app.route("/send", methods=["POST"])
def send_message():
    """
    Send a chat message.

    Authenticates using email + password then inserts a message row with timestamp.
    Returns 201 on success or 401 if auth fails.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email").strip()
    password = data.get("password")
    message = data.get("message").strip()

    if not email or not password or not message:
        return jsonify({"error": "email, password, and message required"}), 400


    found = find_user_by_email(email)
    if not found or not check_password_hash(found.get("password",""), password):
        print(f"[DEBUG] send: auth failed for email {email}")
        return jsonify({"error": "invalid credentials"}), 401

    user_name = found.get("username")
    now = datetime.now()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO message (username, message, message_date, message_time) VALUES (:u, :m, :mdate, :mtime)"),
            {"u": user_name, "m": message, "mdate": now.date().isoformat(), "mtime": now.time().isoformat()}
        )
    return jsonify({"status": "sent", "username": user_name}), 201

# ---------- polling ----------

@app.route("/poll", methods=["GET"])
def poll():
    """
    Poll for new messages.

    Query params:
      - username (required)
      - since (optional): numeric message id to fetch messages after
      - limit (optional): max number of rows

    Returns a JSON list of messages with id, username, message and created_at string.
    """
    user_name = (request.args.get("username") or "").strip()
    since = request.args.get("since")
    limit = int(request.args.get("limit") or 100)

    if not user_name:
        return jsonify({"error": "username required"}), 400

    # check username exists
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT username FROM user"))
        exists = False
        for row in result.mappings().all():
            if row.get("username") == user_name:
                exists = True
                break
        if not exists:
            return jsonify({"error": "unknown username"}), 404

        if since is None:
            rows = conn.execute(text("SELECT unique_id, username, message, message_date, message_time FROM message ORDER BY unique_id DESC LIMIT 50")).mappings().fetchall()
            rows = list(reversed(rows))
        else:
            try:
                sid = int(since)
                rows = conn.execute(text("SELECT unique_id, username, message, message_date, message_time FROM message WHERE unique_id > :sid ORDER BY unique_id ASC LIMIT :lim"), {"sid": sid, "lim": limit}).mappings().fetchall()
            except ValueError:
                rows = []

        out = []
        for r in rows:
            created_at = ""
            if r.get("message_date") and r.get("message_time"):
                created_at = f"{r['message_date']} {r['message_time']}"
            elif r.get("message_date"):
                created_at = r["message_date"]
            out.append({"id": r["unique_id"], "username": r["username"], "message": r["message"], "created_at": created_at})

        return jsonify({"messages": out}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)