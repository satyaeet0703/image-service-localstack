import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    "Content-Type": "application/json"
}


def success(status_code=200, body=None):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body or {})
    }


def error(status_code, message, detail=None):
    payload = {"message": message}
    if detail:
        payload["detail"] = detail

    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(payload)
    }
