from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Request

from .llm.settings import load_project_dotenv

USER_ID_HEADER = "x-geo-user-id"
USER_EMAIL_HEADER = "x-geo-user-email"
USER_NAME_HEADER = "x-geo-user-name"


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: UUID
    email: str
    display_name: str | None = None


class UserIdentityError(ValueError):
    pass


class AuthenticatedUserResolver:
    def __init__(self, default_user: AuthenticatedUser | None = None) -> None:
        self._default_user = default_user

    @classmethod
    def from_env(cls) -> "AuthenticatedUserResolver":
        dotenv = load_project_dotenv()
        raw_user_id = os.environ.get("GEO_DEFAULT_USER_ID") or dotenv.get("GEO_DEFAULT_USER_ID") or ""
        raw_email = os.environ.get("GEO_DEFAULT_USER_EMAIL") or dotenv.get("GEO_DEFAULT_USER_EMAIL") or ""
        raw_name = os.environ.get("GEO_DEFAULT_USER_DISPLAY_NAME") or dotenv.get("GEO_DEFAULT_USER_DISPLAY_NAME")
        if not raw_user_id and not raw_email:
            return cls()
        if not raw_user_id or not raw_email:
            raise UserIdentityError("default user identity requires both GEO_DEFAULT_USER_ID and GEO_DEFAULT_USER_EMAIL")
        return cls(
            default_user=AuthenticatedUser(
                user_id=UUID(raw_user_id),
                email=raw_email.strip(),
                display_name=raw_name.strip() if raw_name else None,
            )
        )

    def resolve_request_user(self, request: Request) -> AuthenticatedUser | None:
        header_user_id = request.headers.get(USER_ID_HEADER)
        header_email = request.headers.get(USER_EMAIL_HEADER)
        header_name = request.headers.get(USER_NAME_HEADER)
        if not header_user_id and not header_email:
            return self._default_user
        if not header_user_id or not header_email:
            raise UserIdentityError("request user identity requires both X-GEO-User-Id and X-GEO-User-Email")
        return AuthenticatedUser(
            user_id=UUID(header_user_id),
            email=header_email.strip(),
            display_name=header_name.strip() if header_name else None,
        )
