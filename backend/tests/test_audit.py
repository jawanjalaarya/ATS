import pytest
from fastapi.testclient import TestClient

def test_audit_logs_unauthorized(client: TestClient):
    # Only admin can access, unauthenticated returns 401
    response = client.get("/api/v1/audit/")
    assert response.status_code == 401
