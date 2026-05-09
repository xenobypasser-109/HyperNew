import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "hyperxeno")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing. Add it to your .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db["users"]
app_data = db["data"]
audit_log = db["audit_log"]
system_state = db["system_state"]

users.create_index("username", unique=True)
app_data.create_index([("collection", 1), ("owner", 1), ("created_at", -1)])


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


def get_all_users():
    return [_public_user(doc) for doc in users.find({}, sort=[("created_at", -1)])]


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
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        })
    return rows


def add_audit(admin, action):
    audit_log.insert_one({"admin": admin, "action": action, "timestamp": _now()})


def get_audit(limit=200):
    return list(audit_log.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))


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
