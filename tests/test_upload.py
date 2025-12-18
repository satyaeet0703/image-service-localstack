from lambdas.upload import generate_upload_url

def test_upload_success(aws_env):
    table = aws_env["table"]
    event = {
        "body": '{"user_id":"u1","content_type":"image/jpeg"}'
    }

    response = generate_upload_url(event)
    print(response)
    assert response["statusCode"] == 200


def test_upload_missing_field():
    event = {
        "body": '{"user_id":"u1"}'
    }

    response = generate_upload_url(event)
    assert response["statusCode"] == 400
