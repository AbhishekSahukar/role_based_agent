import os
from pathlib import Path
from dotenv import load_dotenv

# repo root = role_based_agent/ (config.py is in backend/app/)
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required setting {name}. Add it to {ROOT_DIR / '.env'}")
    return value


TENANT_ID = _required("TENANT_ID")
API_CLIENT_ID = _required("API_CLIENT_ID")
WEB_CLIENT_ID = _required("WEB_CLIENT_ID")
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "access_as_user")

# Full scope string the browser requests for our API.
API_SCOPE = f"api://{API_CLIENT_ID}/{REQUIRED_SCOPE}"

# v2.0 issuer and signing-key endpoint for your tenant.
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

FRONTEND_DIR = ROOT_DIR / "frontend"