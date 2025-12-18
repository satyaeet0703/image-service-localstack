import json
from lambdas.list_images import list_images

def test_list_all_images(aws_env):
    table = aws_env["table"]

    table.put_item(Item={"image_id": "1", "user_id": "u1"})
    table.put_item(Item={"image_id": "2", "user_id": "u2"})

    event = {"queryStringParameters": None}

    response = list_images(event)
    data = json.loads(response["body"])
    print(data)

    # If `data` is a list, assert its length directly
    assert len(data) == 2


def test_list_by_user_id(aws_env):
    table = aws_env["table"]

    table.put_item(Item={"image_id": "1", "user_id": "u1"})
    table.put_item(Item={"image_id": "2", "user_id": "u2"})

    event = {
        "queryStringParameters": {"user_id": "u1"}
    }

    response = list_images(event)
    data = json.loads(response["body"])

    # If `data` is a list, assert its length directly
    assert len(data) == 1


def test_list_by_user_id(aws_env):
    table = aws_env["table"]

    table.put_item(Item={
        "image_id": "img1",
        "user_id": "u1",
        "created_at": "2025-01-01"
    })

    table.put_item(Item={
        "image_id": "img2",
        "user_id": "u2",
        "created_at": "2025-01-02"
    })

    event = {
        "queryStringParameters": {"user_id": "u1"}
    }

    response = list_images(event)
    body = json.loads(response["body"])

    assert len(body) == 1
    assert body[0]["user_id"] == "u1"