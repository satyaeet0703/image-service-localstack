import json
from lambdas.delete_image import delete_image

def test_delete_image_success(aws_env):
    table = aws_env["table"]
    s3 = aws_env["s3"]

    table.put_item(Item={
        "image_id": "img1",
        "s3_key": "img1.jpg"
    })
    response = table.get_item(Key={"image_id": "img1"})
    item = response.get("Item")
    print(item)

    s3.put_object(Bucket="image-bucket", Key="img1.jpg", Body=b"data")

    event = {
        "pathParameters": {"id": "img1"}
    }

    response = delete_image(event)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "Image deleted successfully"


def test_delete_image_not_found(aws_env):
    event = {
        "pathParameters": {"id": "missing"}
    }

    response = delete_image(event)

    assert response["statusCode"] == 404
