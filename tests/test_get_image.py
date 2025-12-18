from lambdas.get_image import get_image

def test_get_image_found(aws_env):
    table = aws_env["table"]

    table.put_item(Item={
        "image_id": "img1",
        "s3_key": "img1.jpg"
    })

    event = {
        "pathParameters": {"id": "img1"}
    }

    response = get_image(event)
    assert response["statusCode"] == 200


def test_get_image_not_found(aws_env):
    event = {
        "pathParameters": {"id": "404"}
    }

    response = get_image(event)
    assert response["statusCode"] == 404
