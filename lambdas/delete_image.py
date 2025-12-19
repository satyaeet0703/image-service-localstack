import json
import boto3
from botocore.exceptions import ClientError
from config import *
from utils import success, error

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
            return error(404, "Image not found")

        # Delete from S3
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=item["s3_key"]
        )

        # Delete metadata
        table.delete_item(Key={"image_id": image_id})

        return success(200, {"message": "Image deleted successfully"})

    except ClientError as e:
        return error(500, "AWS error", str(e))

    except Exception as e:
        return error(500, "Internal server error", str(e))


