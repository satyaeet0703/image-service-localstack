from lambdas.handler import lambda_handler

def test_handler_invalid_route():
    event = {
        "resource": "/invalid",
        "httpMethod": "GET"
    }

    resp = lambda_handler(event, None)

    assert resp["statusCode"] == 404
