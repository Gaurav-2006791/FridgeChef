from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

import main
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_recipe_requires_ingredients():
    response = client.post(
        "/generate",
        json={
            "ingredients": "",
            "cuisine": "Italian",
            "meal_type": "Dinner",
            "diet": "None",
            "cooking_time": "20",
            "spice_level": "Mild",
            "servings": "2",
        },
    )
    assert response.status_code == 422


def test_root_serves_frontend_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Fridge Chef" in response.text


def test_stylesheet_is_served():
    response = client.get("/style.css")
    assert response.status_code == 200
    assert "--primary" in response.text


def test_auth_page_is_served():
    response = client.get("/auth.html")
    assert response.status_code == 200
    assert "Sign In" in response.text


def test_dashboard_html_page_is_served():
    response = client.get("/dashboard.html")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_signup_page_is_served():
    response = client.get("/signup.html")
    assert response.status_code == 200
    assert "Create Account" in response.text


def test_signup_creates_user_and_returns_success():
    response = client.post(
        "/signup",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Account created successfully"


def test_signin_returns_success_for_existing_user():
    response = client.post(
        "/signin",
        json={
            "email": "test@example.com",
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Signed in successfully"


def test_signin_accepts_form_submission_and_redirects():
    client.post(
        "/signup",
        data={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
        },
        follow_redirects=False,
    )
    response = client.post(
        "/signin",
        data={"email": "test@example.com", "password": "StrongPass123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_dashboard_requires_authentication():
    fresh_client = TestClient(app)
    response = fresh_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 307


def test_generate_recipe_falls_back_cleanly_for_non_numeric_cooking_time(monkeypatch):
    class DummyCompletions:
        @staticmethod
        def create(*args, **kwargs):
            raise RuntimeError("simulated OpenAI failure")

    class DummyChat:
        completions = DummyCompletions()

    class DummyClient:
        chat = DummyChat()

    monkeypatch.setattr(main, "OpenAI", lambda api_key: DummyClient())
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    response = client.post(
        "/generate",
        json={
            "ingredients": "tomato, basil",
            "cuisine": "Italian",
            "meal_type": "Dinner",
            "diet": "None",
            "cooking_time": "quick",
            "spice_level": "Mild",
            "servings": "2",
        },
    )

    assert response.status_code == 200
    assert response.json()["recipe_name"]


def test_generate_recipe_uses_fallback_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/generate",
        json={
            "ingredients": "egg, spinach",
            "cuisine": "Mediterranean",
            "meal_type": "Breakfast",
            "diet": "None",
            "cooking_time": "15",
            "spice_level": "Mild",
            "servings": "1",
        },
    )

    assert response.status_code == 200
    assert response.json()["recipe_name"]
