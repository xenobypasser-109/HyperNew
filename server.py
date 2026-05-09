import datetime
import os

import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    add_audit,
    create_user,
    get_all_users,
    get_audit,
    get_data,
    get_system_state,
    get_user,
    save_data,
    set_system_state,
    update_user,
)

load_dotenv()

app = Flask(__name__)
SECRET = os.getenv("JWT_SECRET") or os.urandom(32).hex()


def make_token(user):
    return jwt.encode(
        {
            "username": user["username"],
            "role": user.get("role", "user"),
            "tier": user.get("tier", "basic"),
            "is_admin": user.get("role") in ("admin", "co-admin"),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        },
        SECRET,
        algorithm="HS256",
    )


def verify_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None


def current_user():
    auth = request.headers.get("Authorization", "").replace("Bearer ", "")
    return verify_token(auth)


def require_admin():
    user = current_user()
    if not user or user.get("role") not in ("admin", "co-admin"):
        return None
    return user


def user_payload(user):
    return {
        "token": make_token(user),
        "username": user["username"],
        "role": user.get("role", "user"),
        "tier": user.get("tier", "basic"),
        "is_admin": user.get("role") in ("admin", "co-admin"),
    }


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    role = "admin" if admin_username and username == admin_username else "user"
    tier = "business" if role == "admin" else "basic"
    user = create_user(username, generate_password_hash(password), role=role, tier=tier)
    if not user:
        return jsonify({"error": "Username taken"}), 409
    save_data("users", {"event": "signup", "username": username}, owner="global")
    return jsonify({"ok": True}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = get_user(data.get("username", ""), include_private=True)
    if not user or not check_password_hash(user.get("password", ""), data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    if user.get("is_banned"):
        return jsonify({"error": "Account banned"}), 403
    public_user = get_user(user["username"])
    return jsonify(user_payload(public_user))


@app.route("/status", methods=["GET"])
def status():
    state = get_system_state()
    return jsonify({"online": True, **state})


@app.route("/data", methods=["POST"])
def data_save():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    item_id = save_data(data.get("collection", "general"), data.get("data", {}), owner=user["username"])
    return jsonify({"ok": True, "id": item_id})


@app.route("/data", methods=["GET"])
def data_list():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
    collection = request.args.get("collection")
    owner = None if user.get("role") in ("admin", "co-admin") else user["username"]
    if request.args.get("global") == "true":
        owner = "global"
    return jsonify(get_data(collection=collection, owner=owner))


@app.route("/admin/data", methods=["GET"])
def admin_data_list():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(get_data(collection=request.args.get("collection")))


@app.route("/admin/users", methods=["GET"])
def admin_users():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(get_all_users())


@app.route("/admin/ban", methods=["POST"])
def admin_ban():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    banned = bool(data.get("banned", False))
    user = update_user(username, {"is_banned": banned})
    if not user:
        return jsonify({"error": "User not found"}), 404
    add_audit(admin["username"], f"{'BAN' if banned else 'UNBAN'}: {username}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/set_role", methods=["POST"])
def admin_set_role():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    role = data.get("role", "user")
    if role not in ("user", "moderator", "co-admin", "admin"):
        return jsonify({"error": "Invalid role"}), 400
    user = update_user(data.get("username", ""), {"role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    add_audit(admin["username"], f"ROLE {data.get('username', '')}: {role}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/set_tier", methods=["POST"])
def admin_set_tier():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "basic")
    if tier not in ("basic", "pro", "business"):
        return jsonify({"error": "Invalid tier"}), 400
    user = update_user(data.get("username", ""), {"tier": tier})
    if not user:
        return jsonify({"error": "User not found"}), 404
    add_audit(admin["username"], f"TIER {data.get('username', '')}: {tier}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/broadcast", methods=["POST"])
def admin_broadcast():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    item_id = save_data("broadcasts", {"message": data.get("message", "")}, owner="global")
    add_audit(admin["username"], "BROADCAST")
    return jsonify({"ok": True, "id": item_id})


@app.route("/admin/maintenance", methods=["POST"])
def admin_maintenance():
    admin = require_admin()
    if not admin:
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    set_system_state({
        "maintenance": bool(data.get("active", False)),
        "message": data.get("message", "HyperXeno is under maintenance. Please check back soon."),
    })
    add_audit(admin["username"], f"MAINTENANCE: {bool(data.get('active', False))}")
    return jsonify({"ok": True, **get_system_state()})


@app.route("/admin/audit", methods=["GET"])
def admin_audit():
    if not require_admin():
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(get_audit())


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
