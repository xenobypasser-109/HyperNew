import datetime
import os

import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database import (
    add_audit,
    change_user_password,
    change_username,
    create_user,
    create_subscription_request,
    delete_user,
    get_all_users,
    get_audit,
    get_data,
    get_messages,
    get_subscription_requests,
    get_system_state,
    get_user,
    reset_user_data,
    save_data,
    save_message,
    set_system_state,
    update_subscription_request,
    update_user,
    upsert_user,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
SECRET = os.getenv("JWT_SECRET") or os.getenv("MONGO_URI", "hyperxeno-dev-secret")

# ─────────────────────────────────────────────────────────────────────────────
#  CORS — allow the desktop client (no Origin) and any browser origin
# ─────────────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    origin = request.headers.get("Origin", "")
    # Desktop Python client sends no Origin — always allow
    if not origin:
        response.headers["Access-Control-Allow-Origin"] = "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Content-Type, X-Requested-With, X-HyperXeno-Client"
    )
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path=""):
    return jsonify({"ok": True}), 200


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def make_token(user):
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    is_admin = user.get("role") in ("admin", "co-admin") or (
        admin_username and user.get("username") == admin_username
    )
    role = (
        "admin"
        if is_admin and user.get("username") == admin_username
        else user.get("role", "user")
    )
    tier = "business" if role == "admin" else user.get("tier", "basic")
    return jwt.encode(
        {
            "username": user["username"],
            "role": role,
            "tier": tier,
            "is_admin": bool(is_admin),
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
    auth = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    return verify_token(auth)


def require_admin():
    user = current_user()
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    if not user:
        return None
    if admin_username and user.get("username") == admin_username:
        return user
    if user.get("role") not in ("admin", "co-admin"):
        return None
    return user


def user_payload(user):
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    is_admin = user.get("role") in ("admin", "co-admin") or (
        admin_username and user.get("username") == admin_username
    )
    role = (
        "admin"
        if is_admin and user.get("username") == admin_username
        else user.get("role", "user")
    )
    tier = "business" if role == "admin" else user.get("tier", "basic")
    return {
        "token": make_token(user),
        "username": user["username"],
        "role": role,
        "tier": tier,
        "is_admin": bool(is_admin),
    }


def err(msg, code=400):
    return jsonify({"error": msg}), code


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return err("Missing fields")
    if len(username) < 3:
        return err("Username must be at least 3 characters")
    if len(password) < 6:
        return err("Password must be at least 6 characters")
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    role = "admin" if admin_username and username == admin_username else "user"
    tier = "business" if role == "admin" else "basic"
    user = create_user(username, generate_password_hash(password), role=role, tier=tier)
    if not user:
        return err("Username already taken", 409)
    save_data("users", {"event": "signup", "username": username}, owner="global")
    return jsonify({"ok": True}), 201


@app.route("/register", methods=["POST"])
def register():
    """Alias for /signup — HyperXeno client uses /register."""
    return signup()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    admin_password = os.getenv("HYPERXENO_ADMIN_PASS", "").strip()
    user = get_user(username, include_private=True)
    admin_fallback = bool(
        admin_username and admin_password
        and username == admin_username
        and password == admin_password
    )
    if not user and admin_fallback:
        upsert_user(username, generate_password_hash(password), role="admin", tier="business")
        user = get_user(username, include_private=True)
    if not user or (
        not check_password_hash(user.get("password", ""), password) and not admin_fallback
    ):
        return err("Invalid credentials", 401)
    if user.get("is_banned"):
        return err("Account banned", 403)
    if admin_username and user["username"] == admin_username:
        updates = {"role": "admin", "tier": "business"}
        if admin_fallback:
            updates["password"] = generate_password_hash(password)
        upsert_user(user["username"], updates.get("password"), role="admin", tier="business")
    public_user = get_user(user["username"])
    return jsonify(user_payload(public_user))


@app.route("/login", methods=["GET"])
def login_info():
    return jsonify({"ok": True, "message": "HyperXeno login is online. Use POST /login."})


@app.route("/me", methods=["GET"])
def me():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    public_user = get_user(user["username"])
    if not public_user:
        return err("User not found", 404)
    return jsonify({
        "username": public_user["username"],
        "role": user.get("role", public_user.get("role", "user")),
        "tier": user.get("tier", public_user.get("tier", "basic")),
        "is_admin": bool(user.get("is_admin")),
    })


@app.route("/status", methods=["GET"])
def status():
    state = get_system_state()
    return jsonify({"online": True, **state})


# ─────────────────────────────────────────────────────────────────────────────
#  ACCOUNT MANAGEMENT  (self-service)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/account/change-password", methods=["POST"])
def account_change_password():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "").strip()
    if not old_pw or not new_pw:
        return err("old_password and new_password are required")
    if len(new_pw) < 6:
        return err("New password must be at least 6 characters")
    db_user = get_user(user["username"], include_private=True)
    if not db_user or not check_password_hash(db_user.get("password", ""), old_pw):
        return err("Current password is incorrect", 401)
    change_user_password(user["username"], generate_password_hash(new_pw))
    add_audit(user["username"], "CHANGE_PASSWORD")
    return jsonify({"ok": True, "message": "Password updated successfully"})


@app.route("/account/change-username", methods=["POST"])
def account_change_username():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    new_u = data.get("new_username", "").strip()
    password = data.get("password", "")
    if not new_u or not password:
        return err("new_username and password are required")
    if len(new_u) < 3:
        return err("Username must be at least 3 characters")
    db_user = get_user(user["username"], include_private=True)
    if not db_user or not check_password_hash(db_user.get("password", ""), password):
        return err("Password is incorrect", 401)
    result = change_username(user["username"], new_u)
    if result is None:
        return err("Username already taken", 409)
    add_audit(user["username"], f"CHANGE_USERNAME -> {new_u}")
    # Return new token so client can update session
    new_user_doc = get_user(new_u)
    return jsonify({"ok": True, "user": result, "token": make_token(new_user_doc)})


@app.route("/account/reset", methods=["POST"])
def account_reset():
    """Wipe all personal data (messages, app data) but keep the account."""
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not password:
        return err("password is required")
    db_user = get_user(user["username"], include_private=True)
    if not db_user or not check_password_hash(db_user.get("password", ""), password):
        return err("Password is incorrect", 401)
    reset_user_data(user["username"])
    add_audit(user["username"], "ACCOUNT_RESET")
    return jsonify({"ok": True, "message": "Account data cleared. Account is still active."})


@app.route("/account/delete", methods=["POST", "DELETE"])
def account_delete():
    """Permanently delete the account and all its data."""
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if not password:
        return err("password is required")
    # Prevent admin from self-deleting
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    if admin_username and user["username"] == admin_username:
        return err("Admin account cannot be deleted via API", 403)
    db_user = get_user(user["username"], include_private=True)
    if not db_user or not check_password_hash(db_user.get("password", ""), password):
        return err("Password is incorrect", 401)
    ok = delete_user(user["username"])
    if not ok:
        return err("User not found", 404)
    add_audit(user["username"], "ACCOUNT_DELETED")
    return jsonify({"ok": True, "message": "Account permanently deleted."})


# ─────────────────────────────────────────────────────────────────────────────
#  DATA
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/data", methods=["POST"])
def data_save():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    item_id = save_data(data.get("collection", "general"), data.get("data", {}), owner=user["username"])
    return jsonify({"ok": True, "id": item_id})


@app.route("/data", methods=["GET"])
def data_list():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    collection = request.args.get("collection")
    owner = None if user.get("role") in ("admin", "co-admin") else user["username"]
    if request.args.get("global") == "true":
        owner = "global"
    return jsonify(get_data(collection=collection, owner=owner))


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/messages/users", methods=["GET"])
def message_users():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    rows = []
    for u in get_all_users():
        if not u.get("username"):
            continue
        rows.append({
            "id": u.get("id", ""),
            "username": u.get("username", ""),
            "role": u.get("role", "user"),
            "tier": u.get("tier", "basic"),
        })
    return jsonify(rows)


@app.route("/messages/<username>", methods=["GET"])
def message_thread(username):
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    return jsonify(get_messages(user["username"], username))


@app.route("/messages/<username>", methods=["POST"])
def message_send(username):
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    if not content:
        return err("Missing message content")
    if not get_user(username):
        return err("User not found", 404)
    return jsonify({"ok": True, "message": save_message(user["username"], username, content)})


# ─────────────────────────────────────────────────────────────────────────────
#  SUBSCRIPTION
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/subscription/request", methods=["POST"])
def subscription_request():
    user = current_user()
    if not user:
        return err("Unauthorized", 401)
    data = request.get_json(silent=True) or {}
    plan = data.get("plan", "").strip().lower()
    email = data.get("email", "").strip()
    cashapp = data.get("cashapp", "").strip()
    if plan not in ("pro", "business"):
        return err("Invalid plan — must be 'pro' or 'business'")
    if not email or not cashapp:
        return err("Email and Cash App tag are required")
    req = create_subscription_request(user["username"], plan, email, cashapp)
    return jsonify({"ok": True, "request": req})


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/admin/subscriptions", methods=["GET"])
def admin_subscriptions():
    if not require_admin():
        return err("Unauthorized", 403)
    return jsonify(get_subscription_requests(status=request.args.get("status")))


@app.route("/admin/subscriptions/<request_id>/approve", methods=["POST"])
def admin_subscription_approve(request_id):
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    req = update_subscription_request(request_id, {"status": "approved", "reviewed_by": admin["username"]})
    if not req:
        return err("Request not found", 404)
    user = update_user(req["username"], {"tier": req["plan"]})
    add_audit(admin["username"], f"SUB APPROVE {req['username']}: {req['plan']}")
    return jsonify({"ok": True, "request": req, "user": user})


@app.route("/admin/subscriptions/<request_id>/reject", methods=["POST"])
def admin_subscription_reject(request_id):
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    req = update_subscription_request(request_id, {"status": "rejected", "reviewed_by": admin["username"]})
    if not req:
        return err("Request not found", 404)
    add_audit(admin["username"], f"SUB REJECT {req['username']}: {req['plan']}")
    return jsonify({"ok": True, "request": req})


@app.route("/admin/data", methods=["GET"])
def admin_data_list():
    if not require_admin():
        return err("Unauthorized", 403)
    return jsonify(get_data(collection=request.args.get("collection")))


@app.route("/admin/users", methods=["GET"])
def admin_users():
    if not require_admin():
        return err("Unauthorized", 403)
    return jsonify(get_all_users())


@app.route("/admin/ban", methods=["POST"])
def admin_ban():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    banned = bool(data.get("banned", False))
    user = update_user(username, {"is_banned": banned})
    if not user:
        return err("User not found", 404)
    add_audit(admin["username"], f"{'BAN' if banned else 'UNBAN'}: {username}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/delete_user", methods=["POST"])
def admin_delete_user():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    if not username:
        return err("username is required")
    # Prevent deleting the master admin account
    admin_username = os.getenv("HYPERXENO_ADMIN_USER", "").strip()
    if admin_username and username == admin_username:
        return err("Cannot delete the master admin account", 403)
    ok = delete_user(username)
    if not ok:
        return err("User not found", 404)
    add_audit(admin["username"], f"DELETE_USER: {username}")
    return jsonify({"ok": True, "message": f"User '{username}' permanently deleted."})


@app.route("/admin/set_role", methods=["POST"])
def admin_set_role():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    role = data.get("role", "user")
    if role not in ("user", "moderator", "co-admin", "admin"):
        return err("Invalid role")
    user = update_user(data.get("username", ""), {"role": role})
    if not user:
        return err("User not found", 404)
    add_audit(admin["username"], f"ROLE {data.get('username', '')}: {role}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/set_tier", methods=["POST"])
def admin_set_tier():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "basic")
    if tier not in ("basic", "pro", "business"):
        return err("Invalid tier")
    user = update_user(data.get("username", ""), {"tier": tier})
    if not user:
        return err("User not found", 404)
    add_audit(admin["username"], f"TIER {data.get('username', '')}: {tier}")
    return jsonify({"ok": True, "user": user})


@app.route("/admin/broadcast", methods=["POST"])
def admin_broadcast():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    item_id = save_data("broadcasts", {"message": data.get("message", "")}, owner="global")
    add_audit(admin["username"], "BROADCAST")
    return jsonify({"ok": True, "id": item_id})


@app.route("/admin/maintenance", methods=["POST"])
def admin_maintenance():
    admin = require_admin()
    if not admin:
        return err("Unauthorized", 403)
    data = request.get_json(silent=True) or {}
    set_system_state({
        "maintenance": bool(data.get("active", False)),
        "message": data.get(
            "message", "HyperXeno is under maintenance. Please check back soon."
        ),
    })
    add_audit(admin["username"], f"MAINTENANCE: {bool(data.get('active', False))}")
    return jsonify({"ok": True, **get_system_state()})


@app.route("/admin/audit", methods=["GET"])
def admin_audit():
    if not require_admin():
        return err("Unauthorized", 403)
    return jsonify(get_audit())


# ─────────────────────────────────────────────────────────────────────────────
#  404 CATCH-ALL — return JSON, never HTML
# ─────────────────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": f"Route not found: {request.path}"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": f"Method {request.method} not allowed on {request.path}"}), 405


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "detail": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
