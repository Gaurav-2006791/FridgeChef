"""FastAPI backend for the Fridge Chef application.

This module serves the frontend, health endpoints, and recipe generation logic
for the Fridge Chef experience.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field
import hashlib

from passlib.context import CryptContext

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fridgechef")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI(title="Fridge Chef API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class RecipeRequest(BaseModel):
    """Request payload for recipe generation."""

    ingredients: str = Field(..., min_length=1, description="Available ingredients")
    cuisine: str = Field(default="Any")
    meal_type: str = Field(default="Dinner")
    diet: str = Field(default="None")
    cooking_time: str = Field(default="30")
    spice_level: str = Field(default="Mild")
    servings: str = Field(default="2")


class RecipeResponse(BaseModel):
    """Structured recipe response returned to the frontend."""

    recipe_name: str
    preparation_time: str
    cooking_time: str
    ingredients: list[str]
    instructions: list[str]
    calories: str
    protein: str
    carbohydrates: str
    fat: str
    difficulty: str
    serving_suggestions: list[str]
    chef_tips: list[str]
    healthy_alternatives: list[str]
    food_pairing: list[str]
    cuisine_style: str


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


class SigninRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class UserRecord(BaseModel):
    full_name: str
    email: str
    password_hash: str


users_db: dict[str, UserRecord] = {}
session_store: dict[str, str] = {}


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/")
def serve_index() -> FileResponse:
    """Serve the landing page at the application root."""
    return FileResponse(FRONTEND_DIR / "landing.html")


@app.get("/index.html")
def serve_index_html() -> FileResponse:
    """Serve the landing page at the classic index.html route."""
    return FileResponse(FRONTEND_DIR / "landing.html")


@app.post("/signup", response_model=None)
async def signup(request: Request) -> JSONResponse | RedirectResponse:
    """Create a user account and set an authenticated session cookie."""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        payload_data = await request.json()
        payload = SignupRequest(**payload_data)
        full_name = payload.full_name
        email = payload.email
        password = payload.password
        confirm_password = payload.confirm_password
    else:
        try:
            form_data = await request.form()
            full_name = form_data.get("full_name", "") or form_data.get("fullName", "")
            email = form_data.get("email", "")
            password = form_data.get("password", "")
            confirm_password = form_data.get("confirm_password", "") or form_data.get("confirmPassword", "")
        except Exception:
            full_name = ""
            email = ""
            password = ""
            confirm_password = ""

    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    normalized_email = email.lower().strip()
    if normalized_email in users_db:
        raise HTTPException(status_code=400, detail="An account with that email already exists")

    password_hash = pwd_context.hash(password)
    user = UserRecord(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=password_hash,
    )
    users_db[normalized_email] = user

    session_id = os.urandom(24).hex()
    session_store[session_id] = normalized_email
    is_form_submission = "application/x-www-form-urlencoded" in request.headers.get("content-type", "")
    response = RedirectResponse(url="/dashboard", status_code=303) if is_form_submission else JSONResponse({"message": "Account created successfully"})
    response.set_cookie("session_token", session_id, httponly=True, samesite="lax", secure=False)
    return response


@app.post("/signin", response_model=None)
async def signin(request: Request) -> JSONResponse | RedirectResponse:
    """Sign in an existing user and set an authenticated session cookie."""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        payload_data = await request.json()
        payload = SigninRequest(**payload_data)
    else:
        try:
            form_data = await request.form()
            email = form_data.get("email", "")
            password = form_data.get("password", "")
        except Exception:
            email = ""
            password = ""

    normalized_email = payload.email.lower().strip() if "payload" in locals() else email.lower().strip()
    password_value = payload.password if "payload" in locals() else password
    user = users_db.get(normalized_email)
    if not user or not pwd_context.verify(password_value, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_id = os.urandom(24).hex()
    session_store[session_id] = normalized_email
    is_form_submission = "application/x-www-form-urlencoded" in request.headers.get("content-type", "")
    response = RedirectResponse(url="/dashboard", status_code=303) if is_form_submission else JSONResponse({"message": "Signed in successfully"})
    response.set_cookie("session_token", session_id, httponly=True, samesite="lax", secure=False)
    return response


@app.get("/logout")
def logout(request: Request) -> RedirectResponse:
    """Clear the current session and redirect the user to the sign-in page."""
    session_token = request.cookies.get("session_token")
    if session_token:
        session_store.pop(session_token, None)
    response = RedirectResponse(url="/auth.html", status_code=307)
    response.delete_cookie("session_token")
    return response


@app.get("/dashboard", response_model=None)
def serve_dashboard(request: Request) -> FileResponse | RedirectResponse:
    """Serve the dashboard to authenticated users and redirect unauthenticated users."""
    session_token = request.cookies.get("session_token")
    if not session_token or session_store.get(session_token) not in users_db:
        return RedirectResponse(url="/auth.html", status_code=307)

    user_email = session_store[session_token]
    if user_email not in users_db:
        return RedirectResponse(url="/auth.html", status_code=307)

    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/me")
def current_user(request: Request) -> JSONResponse:
    """Return the current authenticated user's profile details."""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_email = session_store.get(session_token)
    if not user_email or user_email not in users_db:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = users_db[user_email]
    return JSONResponse({"full_name": user.full_name, "email": user.email})


@app.get("/style.css")
def serve_stylesheet() -> FileResponse:
    """Serve the stylesheet used by the frontend."""
    return FileResponse(FRONTEND_DIR / "style.css")


@app.get("/script.js")
def serve_script() -> FileResponse:
    """Serve the JavaScript used by the frontend."""
    return FileResponse(FRONTEND_DIR / "script.js")


@app.get("/auth.html")
def serve_auth_page() -> FileResponse:
    """Serve the sign-in page."""
    return FileResponse(FRONTEND_DIR / "auth.html")


@app.get("/signup.html")
def serve_signup_page() -> FileResponse:
    """Serve the sign-up page."""
    return FileResponse(FRONTEND_DIR / "signup.html")


@app.get("/dashboard.html")
def serve_dashboard_page() -> FileResponse:
    """Serve the dashboard HTML page directly for browser navigation."""
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.post("/generate", response_model=RecipeResponse)
def generate_recipe(payload: RecipeRequest) -> RecipeResponse:
    """Generate a recipe using the OpenAI API, or fall back locally when unavailable."""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        logger.warning("OpenAI API key is not configured; using built-in fallback recipe")
        return RecipeResponse(**build_fallback_recipe(payload))

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a professional chef, nutritionist, and food scientist.
Create a practical recipe based on the user's available ingredients and preferences.
Use only the available ingredients whenever possible and keep the recipe realistic.

User inputs:
- Ingredients: {payload.ingredients}
- Cuisine: {payload.cuisine}
- Meal Type: {payload.meal_type}
- Diet: {payload.diet}
- Cooking Time: {payload.cooking_time}
- Spice Level: {payload.spice_level}
- Servings: {payload.servings}

Return a valid JSON object with the following fields:
recipe_name
preparation_time
cooking_time
ingredients
instructions
calories
protein
carbohydrates
fat
difficulty
serving_suggestions
chef_tips
healthy_alternatives
food_pairing
cuisine_style

Rules:
- Keep the recipe delicious, practical, and family-friendly.
- Use the available ingredients whenever possible.
- If any ingredient is missing, suggest a minimal pantry substitute.
- Format ingredients and instructions as arrays.
- Respond only with JSON.
"""

    try:
        logger.info("Calling OpenAI for recipe generation")
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a professional chef, nutritionist, and food scientist."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        content = completion.choices[0].message.content or "{}"
    except Exception as exc:  # pragma: no cover - network and API errors
        logger.exception("OpenAI request failed")
        fallback_recipe = build_fallback_recipe(payload)
        return RecipeResponse(**fallback_recipe)

    try:
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            parsed = content
        return RecipeResponse(**parsed)
    except Exception as exc:  # pragma: no cover - defensive parsing
        logger.exception("OpenAI response parsing failed")
        fallback_recipe = build_fallback_recipe(payload)
        return RecipeResponse(**fallback_recipe)


def build_fallback_recipe(payload: RecipeRequest) -> dict[str, Any]:
    """Return a practical fallback recipe when the AI service is unavailable."""
    ingredients = [item.strip() for item in payload.ingredients.split(",") if item.strip()]
    if not ingredients:
        ingredients = ["fresh vegetables"]

    cooking_time_value = payload.cooking_time
    if isinstance(cooking_time_value, str):
        digits = "".join(char for char in cooking_time_value if char.isdigit())
        if digits:
            cooking_minutes = int(digits)
        else:
            cooking_minutes = 20
    else:
        cooking_minutes = int(cooking_time_value)

    cooking_minutes = max(10, min(cooking_minutes, 180))

    return {
        "recipe_name": f"{payload.cuisine} Style Stir-Fry",
        "preparation_time": "10 minutes",
        "cooking_time": f"{cooking_minutes} minutes",
        "ingredients": ingredients + ["olive oil", "salt", "pepper"],
        "instructions": [
            "Chop the ingredients into bite-sized pieces.",
            "Sauté them in a hot pan with a little oil.",
            "Season with salt, pepper, and your preferred spices.",
            "Serve warm and enjoy.",
        ],
        "calories": "450 kcal",
        "protein": "20 g",
        "carbohydrates": "35 g",
        "fat": "18 g",
        "difficulty": "Easy",
        "serving_suggestions": ["Serve with rice or toast."],
        "chef_tips": ["Use fresh herbs to brighten the flavor."],
        "healthy_alternatives": ["Swap oil for a light spray if desired."],
        "food_pairing": ["A crisp green salad or roasted vegetables."],
        "cuisine_style": payload.cuisine,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return a consistent JSON payload for HTTP errors."""
    logger.warning("HTTP error %s for %s", exc.status_code, request.url.path)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
