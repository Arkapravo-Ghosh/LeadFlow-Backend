"""Internal authentication routes also require the private service API key."""

from fastapi import APIRouter, Response

from backend.auth.dependencies import CurrentUser, Token
from backend.auth.schemas import LoginRequest, LoginResult, UserRead
from backend.auth.service import sign_in, sign_out
from backend.core.dependencies import Database, Now

router = APIRouter(prefix="/auth", tags=["auth"])


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
