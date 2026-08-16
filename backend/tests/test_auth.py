import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_and_login():
    resp = client.post(
        "/auth/register",
        json={
            "name": "Test Admin",
            "email": "testadmin@routexai.com",
            "password": "TestPass123",
            "role": "admin",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["role"] == "admin"
    assert "access_token" in data

    resp = client.post(
        "/auth/login",
        json={"email": "testadmin@routexai.com", "password": "TestPass123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "testadmin@routexai.com"


def test_login_wrong_password_fails():
    client.post(
        "/auth/register",
        json={
            "name": "Test Rider",
            "email": "testrider@routexai.com",
            "password": "RiderPass123",
            "role": "rider",
        },
    )
    resp = client.post(
        "/auth/login",
        json={"email": "testrider@routexai.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_protected_route_requires_token():
    resp = client.get("/orders")
    assert resp.status_code == 401


def test_duplicate_registration_rejected():
    client.post(
        "/auth/register",
        json={
            "name": "Dup",
            "email": "dup@routexai.com",
            "password": "DupPass123",
            "role": "dispatcher",
        },
    )
    resp = client.post(
        "/auth/register",
        json={
            "name": "Dup2",
            "email": "dup@routexai.com",
            "password": "DupPass123",
            "role": "dispatcher",
        },
    )
    assert resp.status_code == 400
