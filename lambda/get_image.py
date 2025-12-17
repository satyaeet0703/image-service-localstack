import json
import boto3
from botocore.exceptions import ClientError
from config import *


s3 = boto3.client(
    "s3",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT
)

table = dynamodb.Table(TABLE_NAME)


def get_image(event):
    try:
        image_id = event["pathParameters"]["id"]

        response = table.get_item(Key={"image_id": image_id})
        item = response.get("Item")

        if not item:
            return _error_response(404, "Image not found")

        if item.get("status") != "INIT" and item.get("s3_key"):
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": item["s3_key"]
                },
                ExpiresIn=3600
            )
        else:
            return _error_response(400, "Image not uploaded yet")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"download_url": download_url})
        }

    except ClientError as e:
        return _error_response(500, "AWS error", str(e))

    except Exception as e:
        return _error_response(500, "Internal server error", str(e))


def _error_response(status, message, detail=None):
    payload = {"message": message}
    if detail:
        payload["detail"] = detail

    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload)
    }
