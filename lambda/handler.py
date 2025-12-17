from upload import generate_upload_url
from list_images import list_images
from get_image import get_image
from delete_image import delete_image

def lambda_handler(event, context):
    method = event["httpMethod"]
    path = event["resource"]
    print(method, path)

    if method == "POST" and path == "/images/upload-url":
        return generate_upload_url(event)

    if method == "GET" and path == "/images":
        return list_images(event)

    if method == "GET" and path == "/images/{id}":
        return get_image(event)

    if method == "DELETE" and path == "/images/{id}":
        return delete_image(event)

    return {
        "statusCode": 404,
        "body": "Not Found"
    }
