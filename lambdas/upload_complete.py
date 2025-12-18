import boto3
import urllib.parse
from config import *


dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    endpoint_url=AWS_ENDPOINT
)

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Triggered by S3 ObjectCreated events.
    Marks image upload as COMPLETE in DynamoDB.
    """

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        # key format: user_id/image_id
        try:
            user_id, image_id = key.split("/", 1)
        except ValueError:
            continue

        table.update_item(
            Key={"image_id": image_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "UPLOADED"}
        )

    return {"statusCode": 200}
