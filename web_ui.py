import json
import asyncio
from flask import Flask, request, jsonify
from pathlib import Path
from crypto_utils import encrypt_password, decrypt_password
from scheduler import PurchaseScheduler

app = Flask(__name__)

CONFIG_PATH = Path(__file__).parent / "tasks_config.json"

scheduler = PurchaseScheduler()
scheduler_task = None


# -------------------------------
# Helpers
# -------------------------------
def load_tasks():
    if not CONFIG_PATH.exists():
        return {"tasks": []}
    return json.loads(CONFIG_PATH.read_text())


def save_tasks(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


# -------------------------------
# API: List tasks
# -------------------------------
@app.get("/api/tasks")
def list_tasks():
    return jsonify(load_tasks())


# -------------------------------
# API: Create task
# -------------------------------
@app.post("/api/tasks")
def create_task():
    data = request.json

    # Encrypt password before saving
    if "account" in data and "password" in data["account"]:
        raw_pw = data["account"]["password"]
        data["account"]["password_encrypted"] = encrypt_password(raw_pw)
        del data["account"]["password"]

    tasks = load_tasks()
    tasks["tasks"].append(data)
    save_tasks(tasks)

    return jsonify({"status": "ok", "task": data})


# -------------------------------
# API: Update task
# -------------------------------
@app.put("/api/tasks/<task_id>")
def update_task(task_id):
    tasks = load_tasks()
    updated = request.json

    for t in tasks["tasks"]:
        if t["id"] == task_id:

            # Encrypt password if updated
            if "account" in updated and "password" in updated["account"]:
                raw_pw = updated["account"]["password"]
                updated["account"]["password_encrypted"] = encrypt_password(raw_pw)
                del updated["account"]["password"]

            t.update(updated)
            save_tasks(tasks)
            return jsonify({"status": "ok", "task": t})

    return jsonify({"error": "Task not found"}), 404


# -------------------------------
# API: Delete task
# -------------------------------
@app.delete("/api/tasks/<task_id>")
def delete_task(task_id):
    tasks = load_tasks()
    tasks["tasks"] = [t for t in tasks["tasks"] if t["id"] != task_id]
    save_tasks(tasks)
    return jsonify({"status": "deleted"})


# -------------------------------
# Background Scheduler
# -------------------------------
@app.before_first_request
def start_scheduler():
    global scheduler_task
    loop = asyncio.get_event_loop()
    scheduler_task = loop.create_task(scheduler.run_scheduler())


# -------------------------------
# Run local dev server
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
