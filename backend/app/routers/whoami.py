from fastapi import APIRouter, Depends
from app.auth import CurrentUser, get_current_user

router = APIRouter()


@router.get("/whoami")
def whoami(user: CurrentUser = Depends(get_current_user)):
    return {"oid": user.oid, "name": user.name, "roles": user.roles}
