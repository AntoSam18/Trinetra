from datetime import datetime, timezone
import hashlib
import logging
import re

import bcrypt
from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from common_gateway_service.core.config import settings
from common_gateway_service.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    create_session_token,
    get_session_user_id,
)
from common_gateway_service.database.mongo import get_users_collection
from common_gateway_service.utils.phone import format_valid_phone_number


router = APIRouter()
logger = logging.getLogger("trinetra.auth")

SALT_ROUNDS = 12
MIN_PASSWORD_LENGTH = 8
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class SignupBody(BaseModel):
    email: str | None = None
    name: str | None = None
    company: str | None = None
    countryCode: str | None = None
    mobile: str | None = None
    password: str | None = None
    address: str | None = None
    agreeToTerms: bool | None = None


class LoginBody(BaseModel):
    email: str | None = None
    password: str | None = None


def normalize(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ""


def json_error(message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"message": message})


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=SESSION_TTL_SECONDS,
        path="/",
        domain=settings.cookie_domain or None,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        domain=settings.cookie_domain or None,
    )


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise json_error(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long",
            status.HTTP_400_BAD_REQUEST,
        )


def validate_email(email: str) -> None:
    if not EMAIL_REGEX.match(email):
        raise json_error("Invalid email address", status.HTTP_400_BAD_REQUEST)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=SALT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def email_to_gravatar(email: str) -> str:
    email_norm = normalize(email).lower()
    digest = hashlib.md5(email_norm.encode("utf-8")).hexdigest()  # noqa: S324
    return f"https://www.gravatar.com/avatar/{digest}?d=identicon"


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: SignupBody) -> dict[str, object]:
    email = normalize(body.email).lower()
    password = normalize(body.password)
    name = normalize(body.name)
    company = normalize(body.company)
    address = normalize(body.address)

    if not body.agreeToTerms:
        raise json_error("Please accept the terms and conditions", status.HTTP_400_BAD_REQUEST)

    if not email:
        raise json_error("Email is required", status.HTTP_400_BAD_REQUEST)
    validate_email(email)

    if not password:
        raise json_error("Password is required", status.HTTP_400_BAD_REQUEST)
    validate_password(password)

    mobile = format_valid_phone_number(body.countryCode, body.mobile)

    user_doc = {
        "email": email,
        "name": name,
        "company": company,
        "mobile": mobile,
        "address": address,
        "passwordHash": hash_password(password),
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "avatarUrl": email_to_gravatar(email),
    }

    users = get_users_collection()
    try:
        result = users.insert_one(user_doc)
    except DuplicateKeyError:
        raise json_error("User already exists", status.HTTP_409_CONFLICT)

    return {"id": str(result.inserted_id), "email": email}


@router.post("/login")
async def login(body: LoginBody, response: Response) -> dict[str, object]:
    email = normalize(body.email).lower()
    password = normalize(body.password)

    if not email or not password:
        raise json_error("Email and password are required", status.HTTP_400_BAD_REQUEST)

    users = get_users_collection()
    user = users.find_one({"email": email})
    if not user:
        raise json_error("Invalid email or password", status.HTTP_401_UNAUTHORIZED)

    if not verify_password(password, user.get("passwordHash", "")):
        raise json_error("Invalid email or password", status.HTTP_401_UNAUTHORIZED)

    token = create_session_token(str(user["_id"]))
    set_session_cookie(response, token)

    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "company": user.get("company"),
        "avatarUrl": user.get("avatarUrl"),
    }


@router.get("/session")
async def get_session(trinetra_session: str | None = Cookie(default=None)) -> dict[str, object]:
    user_id = get_session_user_id(trinetra_session)
    if not user_id:
        raise json_error("Not authenticated", status.HTTP_401_UNAUTHORIZED)

    users = get_users_collection()
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise json_error("User not found", status.HTTP_404_NOT_FOUND)

    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "company": user.get("company"),
        "avatarUrl": user.get("avatarUrl"),
    }


@router.post("/logout")
async def logout(response: Response) -> dict[str, object]:
    clear_session_cookie(response)
    return {"success": True}
