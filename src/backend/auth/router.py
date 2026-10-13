"""Internal authentication routes also require the private service API key."""

from typing import Annotated

from fastapi import APIRouter, Header, Response

from backend.auth.dependencies import CurrentUser, Token
from backend.auth.registration import sign_up
from backend.auth.schemas import LoginRequest, LoginResult, SignupRequest, UserRead
from backend.auth.service import sign_in, sign_out
from backend.core.dependencies import Database, Now

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=LoginResult, status_code=201)
def signup(
    data: SignupRequest,
    session: Database,
    now: Now,
    response: Response,
    x_registration_source: Annotated[str, Header(max_length=64)] = "shared",
) -> LoginResult:
    response.headers["Cache-Control"] = "no-store"
    return sign_up(session, data, now, x_registration_source)


@router.post("/login", response_model=LoginResult)
def login(
    data: LoginRequest, session: Database, now: Now, response: Response
) -> LoginResult:
    response.headers["Cache-Control"] = "no-store"
    return sign_in(session, data, now)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.post("/logout", status_code=204)
def logout(session: Database, token: Token) -> Response:
    sign_out(session, token)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
