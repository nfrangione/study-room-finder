"""
seed_and_simulate.py — SSU Room Occupancy Simulator
Runs inside Docker container. Seeds DynamoDB with all SSU academic building
rooms, then simulates real-time occupancy changes every 60 seconds.
In production, replace simulate_updates() with real sensor/calendar data.
"""

import boto3
import os
import time
import random
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "SSURooms")
INTERVAL = int(os.environ.get("UPDATE_INTERVAL_SECONDS", "60"))
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-1")
SIMULATE = os.environ.get("SIMULATE", "false").lower() == "true"

# ── ALL SSU ACADEMIC BUILDINGS & ROOMS ───────────────────────────
ROOMS = [
    # Salazar Hall
    {"RoomID": "SAL-101", "Building": "Salazar Hall",            "Floor": "1", "RoomName": "Salazar 101",       "RoomType": "Classroom",   "Capacity": 30},
    {"RoomID": "SAL-102", "Building": "Salazar Hall",            "Floor": "1", "RoomName": "Salazar 102",       "RoomType": "Study Room",  "Capacity": 8},
    {"RoomID": "SAL-201", "Building": "Salazar Hall",            "Floor": "2", "RoomName": "Salazar 201",       "RoomType": "Classroom",   "Capacity": 40},
    {"RoomID": "SAL-202", "Building": "Salazar Hall",            "Floor": "2", "RoomName": "Salazar 202",       "RoomType": "Study Room",  "Capacity": 6},
    {"RoomID": "SAL-301", "Building": "Salazar Hall",            "Floor": "3", "RoomName": "Salazar 301",       "RoomType": "Lab",         "Capacity": 24},

    # Darwin Hall
    {"RoomID": "DAR-101", "Building": "Darwin Hall",             "Floor": "1", "RoomName": "Darwin 101",        "RoomType": "Classroom",   "Capacity": 35},
    {"RoomID": "DAR-102", "Building": "Darwin Hall",             "Floor": "1", "RoomName": "Darwin 102",        "RoomType": "Lab",         "Capacity": 20},
    {"RoomID": "DAR-201", "Building": "Darwin Hall",             "Floor": "2", "RoomName": "Darwin 201",        "RoomType": "Study Room",  "Capacity": 10},
    {"RoomID": "DAR-202", "Building": "Darwin Hall",             "Floor": "2", "RoomName": "Darwin 202",        "RoomType": "Classroom",   "Capacity": 30},
    {"RoomID": "DAR-301", "Building": "Darwin Hall",             "Floor": "3", "RoomName": "Darwin 301",        "RoomType": "Lab",         "Capacity": 18},

    # Stevenson Hall
    {"RoomID": "STV-101", "Building": "Stevenson Hall",          "Floor": "1", "RoomName": "Stevenson 101",     "RoomType": "Classroom",   "Capacity": 45},
    {"RoomID": "STV-102", "Building": "Stevenson Hall",          "Floor": "1", "RoomName": "Stevenson 102",     "RoomType": "Study Room",  "Capacity": 8},
    {"RoomID": "STV-201", "Building": "Stevenson Hall",          "Floor": "2", "RoomName": "Stevenson 201",     "RoomType": "Classroom",   "Capacity": 35},
    {"RoomID": "STV-202", "Building": "Stevenson Hall",          "Floor": "2", "RoomName": "Stevenson Computer Lab", "RoomType": "Lab",    "Capacity": 30},

    # Schulz Information Center (Library)
    {"RoomID": "LIB-1A",  "Building": "Schulz Information Center", "Floor": "1", "RoomName": "Library Room 1A", "RoomType": "Study Room",  "Capacity": 6},
    {"RoomID": "LIB-1B",  "Building": "Schulz Information Center", "Floor": "1", "RoomName": "Library Room 1B", "RoomType": "Study Room",  "Capacity": 8},
    {"RoomID": "LIB-2A",  "Building": "Schulz Information Center", "Floor": "2", "RoomName": "Library Room 2A", "RoomType": "Study Room",  "Capacity": 10},
    {"RoomID": "LIB-2B",  "Building": "Schulz Information Center", "Floor": "2", "RoomName": "Library Quiet Zone", "RoomType": "Lounge",   "Capacity": 20},
    {"RoomID": "LIB-3A",  "Building": "Schulz Information Center", "Floor": "3", "RoomName": "Library Conference Room", "RoomType": "Study Room", "Capacity": 12},

    # Student Center
    {"RoomID": "SC-101",  "Building": "Student Center",          "Floor": "1", "RoomName": "Student Center Lounge",   "RoomType": "Lounge",    "Capacity": 40},
    {"RoomID": "SC-102",  "Building": "Student Center",          "Floor": "1", "RoomName": "Student Center Meeting A", "RoomType": "Study Room", "Capacity": 10},
    {"RoomID": "SC-201",  "Building": "Student Center",          "Floor": "2", "RoomName": "Student Center Meeting B", "RoomType": "Study Room", "Capacity": 8},

    # Rachel Carson Hall
    {"RoomID": "RC-101",  "Building": "Rachel Carson Hall",      "Floor": "1", "RoomName": "Carson 101",        "RoomType": "Classroom",   "Capacity": 30},
    {"RoomID": "RC-102",  "Building": "Rachel Carson Hall",      "Floor": "1", "RoomName": "Carson Lab A",      "RoomType": "Lab",         "Capacity": 20},
    {"RoomID": "RC-201",  "Building": "Rachel Carson Hall",      "Floor": "2", "RoomName": "Carson 201",        "RoomType": "Classroom",   "Capacity": 25},
    {"RoomID": "RC-202",  "Building": "Rachel Carson Hall",      "Floor": "2", "RoomName": "Carson Study Room", "RoomType": "Study Room",  "Capacity": 6},
]

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)


def seed_rooms():
    """Write all room records to DynamoDB. Skips rooms that already exist."""
    logger.info(f"Seeding {len(ROOMS)} rooms across all SSU buildings...")
    seeded = 0
    for room in ROOMS:
        try:
            table.put_item(
                Item={
                    **room,
                    "Status": "empty",
                    "LastUpdated": datetime.utcnow().isoformat() + "Z",
                },
                ConditionExpression="attribute_not_exists(RoomID)",
            )
            seeded += 1
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            pass  # Room already exists, skip
    logger.info(f"Seeded {seeded} new rooms. {len(ROOMS) - seeded} already existed.")


def simulate_updates():
    """Randomly update room occupancy to simulate real usage patterns."""
    logger.info("Simulating occupancy updates...")
    for room in ROOMS:
        # Weight varies by room type — classrooms more likely occupied during day
        weights = {
            "Classroom":  [0.35, 0.65],  # 65% chance occupied
            "Lab":        [0.40, 0.60],
            "Study Room": [0.50, 0.50],
            "Lounge":     [0.45, 0.55],
        }
        w = weights.get(room["RoomType"], [0.5, 0.5])
        status = random.choices(["empty", "occupied"], weights=w)[0]

        table.update_item(
            Key={"RoomID": room["RoomID"]},
            UpdateExpression="SET #s = :status, LastUpdated = :ts",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={
                ":status": status,
                ":ts": datetime.utcnow().isoformat() + "Z",
            },
        )
        logger.info(f"  {room['RoomID']:10s} ({room['Building']:30s}) → {status}")


if __name__ == "__main__":
    logger.info(f"SSU Room Simulator starting. Table: {TABLE_NAME}, Region: {REGION}")
    seed_rooms()

    if not SIMULATE:
        logger.info("SIMULATE=false, so seeding is complete and container will exit.")
        exit(0)

    logger.info(f"SIMULATE=true. Updating every {INTERVAL} seconds.")
    while True:
        try:
            simulate_updates()
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        logger.info(f"Next update in {INTERVAL}s...")
        time.sleep(INTERVAL)
