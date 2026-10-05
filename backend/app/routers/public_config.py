from fastapi import APIRouter
from app import config

router = APIRouter()


@router.get("/config")
def public_config():
    # Public identifiers only. The browser needs them to start sign-in.
    # Never put a secret here: everything this returns is visible to anyone.
    return {
        "tenantId": config.TENANT_ID,
        "webClientId": config.WEB_CLIENT_ID,
        "apiScope": config.API_SCOPE,
    }