from lambdas.upload_complete import lambda_handler

def test_upload_complete():
    event = {
        "Records": [{
            "s3": {
                "bucket": {"name": "test"},
                "object": {"key": "abc.jpg"}
            }
        }]
    }

    resp = lambda_handler(event, None)
    assert resp["statusCode"] == 200
