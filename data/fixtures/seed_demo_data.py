#!/usr/bin/env python3
"""
Seed script to insert realistic smart home devices, flow summaries,
and capture sessions into MongoDB for local review and testing.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Insert project directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    print("Motor is not installed in the current environment.")
    print("Please run within an environment where backend dependencies are installed.")
    sys.exit(0)


async def seed():
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "smart_home_anomaly")
    print(f"Connecting to MongoDB at {mongo_url} (db: {db_name})...")

    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
    db = client[db_name]

    try:
        await client.admin.command("ping")
        print("Connected to MongoDB successfully.")
    except Exception as exc:
        print(f"Could not connect to MongoDB: {exc}")
        print("Make sure MongoDB Community Edition is running.")
        return

    fixtures_dir = BASE_DIR / "data" / "fixtures"

    # Seed Devices
    devices_file = fixtures_dir / "sample_devices.json"
    if devices_file.exists():
        with open(devices_file, "r") as f:
            devices = json.load(f)
            for d in devices:
                await db.devices.update_one(
                    {"device_key": d["device_key"]},
                    {"$set": d},
                    upsert=True
                )
        print(f"Seeded {len(devices)} devices into collection 'devices'.")

    # Seed Flows
    flows_file = fixtures_dir / "sample_flows.json"
    if flows_file.exists():
        with open(flows_file, "r") as f:
            flows = json.load(f)
            if flows:
                await db.flows.insert_many(flows)
        print(f"Seeded {len(flows)} flows into collection 'flows'.")

    # Seed Sample Capture Session
    session = {
        "session_id": "seed-session-001",
        "interface": "eth0",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "stopped_at": datetime.now(timezone.utc).isoformat(),
        "status": "stopped",
        "packets_seen": 640,
        "flows_created": 5,
        "last_error": None
    }
    await db.capture_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": session},
        upsert=True
    )
    print("Seeded sample capture session into collection 'capture_sessions'.")

    client.close()
    print("Seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())

