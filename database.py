import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "hyperxeno")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing. Add it to your .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db["users"]
app_data = db["data"]
messages = db["messages"]
subscription_requests = db["subscription_requests"]
audit_log = db["audit_log"]
system_state = db["system_state"]

users.create_index("username", unique=True)
app_data.create_index([("collection", 1), ("owner", 1), ("created_at", -1)])
messages.create_index([("participants", 1), ("created_at", -1)])
subscription_requests.create_index([("status", 1), ("created_at", -1)])


def _now():
    return datetime.now(timezone.utc)


def _public_user(doc):
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "username": doc.get("username", ""),
        "role": doc.get("role", "user"),
        "tier": doc.get("tier", "basic"),
        "is_admin": doc.get("role") in ("admin", "co-admin"),
        "banned": bool(doc.get("is_banned", False)),
        "joined": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def create_user(username, password_hash, role="user", tier="basic"):
    doc = {
        "username": username,
        "password": password_hash,
        "role": role,
        "tier": tier,
        "is_banned": False,
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        result = users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _public_user(doc)
    except DuplicateKeyError:
        return None


def get_user(username, include_private=False):
    doc = users.find_one({"username": username})
    if include_private:
        return doc
    return _public_user(doc)


def update_user(username, updates):
    clean_updates = {k: v for k, v in updates.items() if k not in {"_id", "username", "password"}}
    clean_updates["updated_at"] = _now()
    doc = users.find_one_and_update(
        {"username": username},
        {"$set": clean_updates},
        return_document=ReturnDocument.AFTER,
    )
    return _public_user(doc)


def upsert_user(username, password_hash=None, role="user", tier="basic"):
    updates = {"role": role, "tier": tier, "updated_at": _now()}
    if password_hash:
        updates["password"] = password_hash
    doc = users.find_one_and_update(
        {"username": username},
        {"$set": updates, "$setOnInsert": {"created_at": _now(), "is_banned": False}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return _public_user(doc)


def get_all_users():
    return [_public_user(doc) for doc in users.find({}, sort=[("created_at", -1)])]


def change_user_password(username, new_password_hash):
    """Update only the password field for a user."""
    doc = users.find_one_and_update(
        {"username": username},
        {"$set": {"password": new_password_hash, "updated_at": _now()}},
        return_document=ReturnDocument.AFTER,
    )
    return _public_user(doc)


def change_username(old_username, new_username, password_hash=None):
    """
    Rename a user. Returns None if new_username is already taken.
    Also migrates all their messages to the new username.
    """
    if users.find_one({"username": new_username}):
        return None  # taken
    updates = {"username": new_username, "updated_at": _now()}
    if password_hash:
        updates["password"] = password_hash
    doc = users.find_one_and_update(
        {"username": old_username},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if doc:
        # Migrate messages
        messages.update_many({"sender": old_username}, {"$set": {"sender": new_username}})
        messages.update_many({"receiver": old_username}, {"$set": {"receiver": new_username}})
        messages.update_many(
            {"participants": old_username},
            [{"$set": {"participants": {
                "$map": {"input": "$participants",
                         "as": "p",
                         "in": {"$cond": [{"$eq": ["$$p", old_username]}, new_username, "$$p"]}}}}}]
        )
    return _public_user(doc)


def reset_user_data(username):
    """
    Wipe all personal app_data and messages for a user.
    Account itself stays intact.
    """
    app_data.delete_many({"owner": username})
    messages.delete_many({"participants": username})
    users.update_one({"username": username}, {"$set": {"updated_at": _now()}})
    return True


def delete_user(username):
    """
    Permanently delete user + all their data.
    Returns True if deleted, False if not found.
    """
    result = users.delete_one({"username": username})
    if result.deleted_count == 0:
        return False
    app_data.delete_many({"owner": username})
    messages.delete_many({"participants": username})
    return True


def save_message(sender, receiver, content):
    participants = sorted([sender, receiver])
    doc = {
        "sender": sender,
        "receiver": receiver,
        "participants": participants,
        "content": content,
        "created_at": _now(),
    }
    result = messages.insert_one(doc)
    doc["_id"] = result.inserted_id
    return public_message(doc)


def public_message(doc):
    return {
        "id": str(doc["_id"]),
        "sender": doc.get("sender", ""),
        "receiver": doc.get("receiver", ""),
        "content": doc.get("content", ""),
        "created_at": str(doc.get("created_at", "")),
    }


def get_messages(user_a, user_b, limit=100):
    participants = sorted([user_a, user_b])
    rows = list(messages.find({"participants": participants}).sort("created_at", -1).limit(limit))
    rows.reverse()
    return [public_message(doc) for doc in rows]


def create_subscription_request(username, plan, email, cashapp):
    doc = {
        "username": username,
        "plan": plan,
        "email": email,
        "cashapp": cashapp,
        "status": "pending",
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = subscription_requests.insert_one(doc)
    doc["_id"] = result.inserted_id
    return public_subscription_request(doc)


def public_subscription_request(doc):
    return {
        "id": str(doc["_id"]),
        "username": doc.get("username", ""),
        "plan": doc.get("plan", ""),
        "email": doc.get("email", ""),
        "cashapp": doc.get("cashapp", ""),
        "status": doc.get("status", "pending"),
        "created_at": str(doc.get("created_at", "")),
        "updated_at": str(doc.get("updated_at", "")),
    }


def get_subscription_requests(status=None):
    query = {}
    if status:
        query["status"] = status
    return [public_subscription_request(doc) for doc in subscription_requests.find(query).sort("created_at", -1)]


def update_subscription_request(request_id, updates):
    from bson import ObjectId
    updates["updated_at"] = _now()
    doc = subscription_requests.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return public_subscription_request(doc) if doc else None


def save_data(collection, data, owner="global"):
    doc = {
        "collection": collection,
        "owner": owner,
        "data": data,
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = app_data.insert_one(doc)
    return str(result.inserted_id)


def get_data(collection=None, owner=None):
    query = {}
    if collection:
        query["collection"] = collection
    if owner:
        query["owner"] = owner
    rows = []
    for doc in app_data.find(query, sort=[("created_at", -1)]):
        rows.append({
            "id": str(doc["_id"]),
            "collection": doc.get("collection"),
            "owner": doc.get("owner"),
            "data": doc.get("data", {}),
            "created_at": str(doc.get("created_at", "")),
            "updated_at": str(doc.get("updated_at", "")),
        })
    return rows


def add_audit(admin, action):
    audit_log.insert_one({"admin": admin, "action": action, "timestamp": _now()})


def get_audit(limit=200):
    rows = list(audit_log.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    for r in rows:
        if "timestamp" in r:
            r["timestamp"] = str(r["timestamp"])
    return rows


def get_system_state():
    state = system_state.find_one({"_id": "global"}) or {}
    return {
        "maintenance": bool(state.get("maintenance", False)),
        "message": state.get("message", "HyperXeno is under maintenance. Please check back soon."),
    }


def set_system_state(updates):
    updates["updated_at"] = _now()
    return system_state.find_one_and_update(
        {"_id": "global"},
        {"$set": updates},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
