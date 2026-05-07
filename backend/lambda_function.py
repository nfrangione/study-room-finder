"""
lambda_function.py — SSU Room Occupancy Scanner
AWS Lambda (Python 3.9) — handles all API requests via API Gateway.
Covers all SSU academic buildings: Salazar, Darwin, Stevenson,
Schulz Information Center (Library), Student Center, Rachel Carson Hall.

IAM Role: ssu-scanner-lambda-role (least privilege — DynamoDB only)
"""

import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "SSURooms")
table = dynamodb.Table(TABLE_NAME)

CORS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
}


def respond(status, body):
    return {"statusCode": status, "headers": CORS, "body": json.dumps(body)}


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")
    path   = event.get("path", "/rooms")
    params = event.get("queryStringParameters") or {}

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS, "body": ""}

    try:
        # GET /rooms — all rooms, optional ?building= or ?status= filter
        if method == "GET" and path == "/rooms":
            return get_rooms(params)

        # GET /rooms/{roomId} — single room
        elif method == "GET" and path.startswith("/rooms/"):
            room_id = path.split("/")[-1]
            return get_room(room_id)

        # GET /buildings — list of all buildings with summary counts
        elif method == "GET" and path == "/buildings":
            return get_buildings()

        # POST /rooms/update — update a room's occupancy status
        elif method == "POST" and path == "/rooms/update":
            body = json.loads(event.get("body", "{}"))
            return update_room(body)

        else:
            return respond(404, {"error": "Route not found"})

    except Exception as e:
        print(f"ERROR: {e}")
        return respond(500, {"error": str(e)})


def get_rooms(params):
    """Return all rooms. Optionally filter by building or status."""
    result = table.scan()
    rooms = result.get("Items", [])

    building = params.get("building")
    status   = params.get("status")

    if building:
        rooms = [r for r in rooms if r.get("Building", "").lower() == building.lower()]
    if status:
        rooms = [r for r in rooms if r.get("Status", "").lower() == status.lower()]

    # Sort by building then room name
    rooms.sort(key=lambda r: (r.get("Building", ""), r.get("RoomName", "")))

    return respond(200, {
        "rooms": rooms,
        "count": len(rooms),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


def get_room(room_id):
    """Return a single room by RoomID."""
    result = table.get_item(Key={"RoomID": room_id})
    room = result.get("Item")
    if not room:
        return respond(404, {"error": f"Room {room_id} not found"})
    return respond(200, room)


def get_buildings():
    """Return a summary of each building with empty/occupied counts."""
    result = table.scan()
    rooms = result.get("Items", [])

    summary = {}
    for room in rooms:
        b = room.get("Building", "Unknown")
        if b not in summary:
            summary[b] = {"building": b, "total": 0, "empty": 0, "occupied": 0}
        summary[b]["total"] += 1
        if room.get("Status") == "empty":
            summary[b]["empty"] += 1
        else:
            summary[b]["occupied"] += 1

    return respond(200, {
        "buildings": list(summary.values()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


def update_room(body):
    """Update a room's occupancy. Body: {room_id, status: 'empty'|'occupied'}"""
    room_id = body.get("room_id")
    status  = body.get("status")

    if not room_id or status not in ["empty", "occupied"]:
        return respond(400, {"error": "room_id and status ('empty' or 'occupied') required"})

    table.update_item(
        Key={"RoomID": room_id},
        UpdateExpression="SET #s = :status, LastUpdated = :ts",
        ExpressionAttributeNames={"#s": "Status"},
        ExpressionAttributeValues={
            ":status": status,
            ":ts": datetime.utcnow().isoformat() + "Z",
        },
    )

    return respond(200, {
        "message": f"Room {room_id} marked as {status}",
        "room_id": room_id,
        "status": status,
        "updated": datetime.utcnow().isoformat() + "Z",
    })
