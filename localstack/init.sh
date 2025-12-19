#!/bin/bash
set -e


echo "Initializing LocalStack resources..."

export AWS_REGION=ap-south-1
export AWS_DEFAULT_REGION=ap-south-1
export ACCOUNT_ID=000000000000
export BUCKET=image-bucket

# Create S3 bucket
awslocal s3api create-bucket \
  --bucket $BUCKET \
  --create-bucket-configuration LocationConstraint=ap-south-1 \
  || true

awslocal s3 ls


# Create DynamoDB table
awslocal dynamodb create-table \
  --table-name ImagesMetadata \
  --attribute-definitions \
    AttributeName=image_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=image_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[
    {
      "IndexName": "user_id-created_at-index",
      "KeySchema": [
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "created_at", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ]' || true

# Create Lambda
zip -j /tmp/function.zip \
  /lambdas/handler.py \
  /lambdas/upload.py \
  /lambdas/list_images.py \
  /lambdas/get_image.py \
  /lambdas/delete_image.py \
  /lambdas/config.py \
  /lambdas/utils.py

awslocal lambda create-function \
  --function-name image-service-lambda \
  --runtime python3.8 \
  --handler handler.lambda_handler \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --zip-file fileb:///tmp/function.zip \
  --timeout 30
  --environment Variables="{AWS_ENDPOINT_URL=http://localhost:4566}" \
  || true

# Create API Gateway
API_ID=$(awslocal apigateway create-rest-api --name image-api --query id --output text)

ROOT_ID=$(awslocal apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

IMAGES_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part images \
  --query id --output text)

UPLOAD_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $IMAGES_ID \
  --path-part upload-url \
  --query id --output text)

IMAGE_ID=$(awslocal apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $IMAGES_ID \
  --path-part "{id}" \
  --query id --output text)


awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $IMAGES_ID \
  --http-method GET \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $IMAGES_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-south-1:000000000000:function:image-service-lambda/invocations


awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $UPLOAD_ID \
  --http-method POST \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $UPLOAD_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-south-1:000000000000:function:image-service-lambda/invocations

awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $IMAGE_ID \
  --http-method GET \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $IMAGE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-south-1:000000000000:function:image-service-lambda/invocations

awslocal apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $IMAGE_ID \
  --http-method DELETE \
  --authorization-type NONE

awslocal apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $IMAGE_ID \
  --http-method DELETE \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-south-1:000000000000:function:image-service-lambda/invocations


add_cors_to_method() {
  local RESOURCE_ID=$1
  local METHOD=$2

  # Declare headers
  awslocal apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method $METHOD \
    --status-code 200 \
    --response-parameters \
      "method.response.header.Access-Control-Allow-Origin=true,\
       method.response.header.Access-Control-Allow-Headers=true,\
      method.response.header.Access-Control-Allow-Methods=true"

  awslocal apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method $METHOD \
    --status-code 200 \
    --response-parameters '{
      "method.response.header.Access-Control-Allow-Origin": "'\''*'\''",
      "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''",
      "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,DELETE,OPTIONS'\''"
    }' \
    || true
}

declare -A API_METHODS=(
  ["$IMAGES_ID"]="GET"
  ["$UPLOAD_ID"]="POST"
  ["$IMAGE_ID"]="GET DELETE"
)



for RESOURCE_ID in "${!API_METHODS[@]}"; do
  for METHOD in ${API_METHODS[$RESOURCE_ID]}; do
    add_cors_to_method "$RESOURCE_ID" "$METHOD"
  done
done


add_cors_to_resource() {
  local RESOURCE_ID=$1

  echo "Adding CORS to resource $RESOURCE_ID"

  # 1. Create OPTIONS method (idempotent)
  awslocal apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    || true

  # 2. Method response (declare headers)
  awslocal apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters \
      "method.response.header.Access-Control-Allow-Origin=true,\
       method.response.header.Access-Control-Allow-Headers=true,\
       method.response.header.Access-Control-Allow-Methods=true" \
    || true

  # 3. Mock integration
  awslocal apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\":200}"}' \
    || true

  # 4. Integration response (actual header values)
  awslocal apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
      "method.response.header.Access-Control-Allow-Origin": "'\''*'\''",
      "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,Authorization'\''",
      "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,DELETE,OPTIONS'\''"
    }' \
    || true
}

for RESOURCE_ID in $IMAGES_ID $IMAGE_ID $UPLOAD_ID; do
  add_cors_to_resource $RESOURCE_ID
done


awslocal apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name dev

echo "Adding S3 event notification..."


zip -j /tmp/upload_complete.zip /lambdas/upload_complete.py /lambdas/config.py

awslocal lambda create-function \
  --function-name upload-complete-lambda \
  --runtime python3.8 \
  --handler upload_complete.lambda_handler \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --zip-file fileb:///tmp/upload_complete.zip \
  --timeout 30 \
  --environment Variables="{AWS_REGION=ap-south-1}" \
  || true

awslocal lambda wait function-active-v2 --function-name upload-complete-lambda

awslocal lambda get-function \
  --function-name upload-complete-lambda


LAMBDA_ARN=$(awslocal lambda get-function \
  --function-name upload-complete-lambda \
  --query 'Configuration.FunctionArn' \
  --output text)
echo $LAMBDA_ARN


awslocal lambda add-permission \
  --function-name upload-complete-lambda \
  --statement-id s3invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::image-bucket \
  --source-account 000000000000 \
  || true


awslocal s3api put-bucket-notification-configuration \
  --bucket image-bucket \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [
      {
        \"LambdaFunctionArn\": \"$LAMBDA_ARN\",
        \"Events\": [\"s3:ObjectCreated:*\"]
      }
    ]
  }"
awslocal s3api get-bucket-notification-configuration \
  --bucket image-bucket



echo $API_ID
echo "LocalStack initialized"


