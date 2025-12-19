import boto3
import pytest
import sys
from moto import mock_dynamodb, mock_s3
from botocore.exceptions import ClientError

REGION = "ap-south-1"
TABLE_NAME = "ImagesMetadata-test4"
BUCKET = "test-bucket-4"

import os
sys.path.insert(0, os.path.abspath("lambdas"))

os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_SESSION_TOKEN"] = "test"
os.environ["AWS_DEFAULT_REGION"] = REGION
os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"
os.environ["IMAGE_TABLE"]=TABLE_NAME
os.environ["IMAGE_BUCKET"] = BUCKET

@pytest.fixture
def aws_env():
    with mock_dynamodb(), mock_s3():
        # DynamoDB
        try:
            dynamodb = boto3.resource("dynamodb", region_name=REGION)
            table = dynamodb.create_table(
                TableName=TABLE_NAME,
                AttributeDefinitions=[
                    {"AttributeName": "image_id", "AttributeType": "S"},
                    {"AttributeName": "user_id", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "image_id", "KeyType": "HASH"}
                ],
                BillingMode="PAY_PER_REQUEST",
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "user_id-created_at-index",
                        "KeySchema": [
                            {"AttributeName": "user_id", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
            )
            table.wait_until_exists()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {TABLE_NAME} already exists. Proceeding with existing table.")
                # Get a reference to the existing table
                table = dynamodb.Table(TABLE_NAME)
            else:
                # Handle other potential errors
                raise e

        # S3
        s3 = boto3.client("s3", region_name=REGION)
        try:
            s3.create_bucket(
                Bucket=BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
            print(f"Bucket {BUCKET} created.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
                print(f"Bucket {BUCKET} already exists and is owned by you. Proceeding.")
            else:
                raise e

        yield {
            "table": table,
            "s3": s3
        }
        table.delete()
        table.wait_until_not_exists()