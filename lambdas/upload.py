import json
import uuid
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from config import *
from utils import success, error
PORT = os.environ.get("X_PORT", "4566")


s3 = boto3.client(
    "s3",
    region_name=REGION,
    endpoint_url=LOCALSTACK_P
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT
)

table = dynamodb.Table(TABLE_NAME)


def generate_upload_url(event):
    """
    Generates a pre-signed S3 PUT URL and stores image metadata in DynamoDB.
    """

    try:
        body = json.loads(event.get("body", "{}"))
        print(body)
        # ---- Required fields ----
        user_id = body["user_id"]
        content_type = body["content_type"]

        # ---- Optional fields ----
        tags = body.get("tags", [])
        visibility = body.get("visibility", "public")

        image_id = str(uuid.uuid4())
        s3_key = f"{user_id}/{image_id}"

        # Generate pre-signed PUT URL
        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type
            },
            ExpiresIn=300
        )

        # Persist metadata (status INIT)
        table.put_item(Item={
            "image_id": image_id,
            "user_id": user_id,
            "s3_bucket": BUCKET_NAME,
            "s3_key": s3_key,
            "content_type": content_type,
            "tags": tags,
            "visibility": visibility,
            "status": "INIT",
            "created_at": datetime.now().isoformat()
        })
        #### for debug
        upload_url = LOCALSTACK_P+upload_url.split(PORT)[1]


        return success(200, {
                "image_id": image_id,
                "upload_url": upload_url,
                "curl_debug": "curl -X PUT -H 'Content-Type: image/jpeg'  --data-binary '@test.jpg' '"+upload_url+"'",
                "expires_in": 300
            })

    except KeyError as e:
        return error(
            400, f"Missing required field: {str(e)}"
        )

    except ClientError as e:
        return error(
            500, "AWS service error", str(e)
        )

    except Exception as e:
        return error(
            500, "Internal server error", str(e)
        )
