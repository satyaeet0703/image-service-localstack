import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from config import *

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT
)

table = dynamodb.Table(TABLE_NAME)


def list_images(event):
    try:
        params = event.get("queryStringParameters") or {}

        user_id = params.get("user_id")

        if user_id:
            response = table.query(
                IndexName="user_id-created_at-index",
                KeyConditionExpression=Key("user_id").eq(user_id)
            )
            items = response.get("Items", [])
        else:
            response = table.scan()
            items = response.get("Items", [])

        # Optional visibility filter

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items)
        }

    except Exception as e:
        return _error_response(500, "Failed to list images", str(e))


def _error_response(status, message, detail=None):
    payload = {"message": message}
    if detail:
        payload["detail"] = detail

    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload)
    }
