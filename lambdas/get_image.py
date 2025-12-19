import json
import boto3
from botocore.exceptions import ClientError
from config import *
from utils import success, error
PORT = os.environ.get("X_PORT", "4566")


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
            return error(404, "Image not found")

        if item.get("status") != "INIT" and item.get("s3_key"):
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": item["s3_key"]
                },
                ExpiresIn=3600
            )
            download_url = LOCALSTACK_P + download_url.split(PORT)[-1]

        else:
            return error(400, "Image not uploaded yet")


        return success(200, {"download_url": download_url})

    except ClientError as e:
        return error(500, "AWS error", str(e))

    except Exception as e:
        return error(500, "Internal server error", str(e))
