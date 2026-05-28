from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
def read_current_user() -> dict[str, str]:
    return {"detail": "not implemented"}


@router.get("/")
def list_users() -> list[dict[str, str]]:
    return []
