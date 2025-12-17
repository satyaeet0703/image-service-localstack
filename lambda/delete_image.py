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


def delete_image(event):
    try:
        image_id = event["pathParameters"]["id"]

        response = table.get_item(Key={"image_id": image_id})
        item = response.get("Item")

        if not item:
            return _error_response(404, "Image not found")

        # Delete from S3
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=item["s3_key"]
        )

        # Delete metadata
        table.delete_item(Key={"image_id": image_id})

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Image deleted successfully"})
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
