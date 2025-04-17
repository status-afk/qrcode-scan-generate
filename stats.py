import json
import logging
import os
from pathlib import Path

STATS_FILE = Path("user_stats.json")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_stats():
    if not os.path.exists(STATS_FILE) or os.stat(STATS_FILE).st_size == 0:
        with open(STATS_FILE, "w") as f:
            json.dump({"users": []}, f)
    with open(STATS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            with open(STATS_FILE, "w") as f_reset:
                json.dump({"users": []}, f_reset)
            return {"users": []}

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_user(user_id, username=None):
    stats = load_stats()
    if not any(user["id"] == user_id for user in stats["users"]):
        stats["users"].append({
            "id": user_id,
            "username": username or ""
        })
        save_stats(stats)

def delete_user(user_id):
    stats = load_stats()
    stats["users"] = [u for u in stats["users"] if u["id"] != user_id]
    save_stats(stats)

def get_user_by_id(user_id):
    stats = load_stats()
    return next((u for u in stats["users"] if u["id"] == user_id), None)

def get_user_by_username(username):
    stats = load_stats()
    return next((u for u in stats["users"] if u["username"] == username), None)

def get_user_count():
    stats = load_stats()
    return len(stats["users"])

def get_users():
    logging.debug(f"Checking {STATS_FILE.resolve()}")
    if STATS_FILE.exists():
        logging.debug(f"Found {STATS_FILE}")
        try:
            with STATS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                logging.debug(f"Loaded JSON: {data}")
                users = [user["id"] for user in data.get("users", []) if isinstance(user.get("id"), int)]
                logging.debug(f"User IDs: {users}")
                return users
        except Exception as e:
            logging.error(f"Error loading users: {e}")
            return []
    logging.warning(f"{STATS_FILE} not found")
    return []
