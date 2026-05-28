from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login() -> dict[str, str]:
    return {"detail": "not implemented"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"detail": "not implemented"}
