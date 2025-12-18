import os
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
LOCALSTACK_P = os.environ.get("LOCALSTACK_P", "http://localhost:4566")
os.environ.get("LOCALSTACK_HOSTNAME", "http://localhost:4566")

REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")

BUCKET_NAME = os.environ.get("IMAGE_BUCKET", "image-bucket")
TABLE_NAME = os.environ.get("IMAGE_TABLE", "ImagesMetadata")
