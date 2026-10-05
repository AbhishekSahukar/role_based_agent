import os
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.environ["TENANT_ID"]
API_CLIENT_ID = os.environ["API_CLIENT_ID"]
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "access_as_user")

# v2.0 issuer and signing-key endpoint for your tenant.
# Open the openid-configuration URL in a browser once and confirm
# that "issuer" and "jwks_uri" match these two values.
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"