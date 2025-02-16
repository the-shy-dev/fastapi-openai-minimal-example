from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_login():
    response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

# TBD: Need to fix this test
# def test_generate_sync_unauthorized():
#     response = client.post("/generate_sync", json={"prompt": "Hello", "max_tokens": 50})
#     assert response.status_code == 401

def test_generate_sync():
    login_res = client.post("/login", json={"username": "testuser", "password": "testpass"})
    token = login_res.json()["access_token"]

    response = client.post(
        "/generate_sync",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "Explain black holes", "max_tokens": 50}
    )
    
    assert response.status_code == 200
    assert "response" in response.json()
