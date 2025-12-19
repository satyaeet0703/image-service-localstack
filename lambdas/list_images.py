import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

from config import *
from utils import success, error

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
        filter_expr = None
        visibility = params.get("visibility")

        # Optional filters
        if visibility:
            filter_expr = Attr("visibility").eq(visibility)
        if user_id:
            query_args = {
                "IndexName": "user_id-created_at-index",
                "KeyConditionExpression": Key("user_id").eq(user_id),
            }

            if filter_expr:
                query_args["FilterExpression"] = filter_expr
            response = table.query(**query_args)
        else:
            scan_args = {}
            if filter_expr:
                scan_args["FilterExpression"] = filter_expr

            response = table.scan(**scan_args)

        items = response.get("Items", [])

        # Optional visibility filter

        return success(200, items)

    except Exception as e:
        return error(500, "Failed to list images", str(e))
