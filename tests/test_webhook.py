from fastapi.testclient import TestClient

from aicaller.main import app

client = TestClient(app)


def test_webhook_rejects_unverified_request():
    response = client.post(
        "/api/webhooks/telephony",
        content=b'{"event_type":"INCOMING_CALL","call_id":"call-1"}',
    )
    assert response.status_code == 401
