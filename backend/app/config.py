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


# --- Entra ID ---
TENANT_ID = _required("TENANT_ID")
API_CLIENT_ID = _required("API_CLIENT_ID")
WEB_CLIENT_ID = _required("WEB_CLIENT_ID")
REQUIRED_SCOPE = os.getenv("REQUIRED_SCOPE", "access_as_user")
API_SCOPE = f"api://{API_CLIENT_ID}/{REQUIRED_SCOPE}"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
ISSUER = f"{AUTHORITY}/v2.0"
JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"

# App role Values defined on askhr-api. Must match exactly (case matters).
KNOWN_ROLES = frozenset({"HR", "Employee", "IT"})

# --- On-behalf-of (askhr-api as a confidential client) ---
API_CLIENT_SECRET = _required("API_CLIENT_SECRET")  # Phase 6: from Key Vault
GRAPH_SCOPES = ["https://graph.microsoft.com/User.Read"]
GRAPH_ME_URL = (
    "https://graph.microsoft.com/v1.0/me"
    "?$select=displayName,userPrincipalName,mail,jobTitle,department"
)

# --- MCP server (mounted inside this app) ---
MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/tools/mcp")

# --- LLM (OpenRouter) ---
OPENROUTER_API_KEY = _required("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-v4-flash:free")
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "8"))

# --- Azure AI Search (keyless: Entra ID via DefaultAzureCredential) ---
SEARCH_ENDPOINT = _required("SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("SEARCH_INDEX", "policies")
SEARCH_TOP = int(os.getenv("SEARCH_TOP", "3"))

# --- Tracing (optional: tracing is off if keys are missing) ---
LANGFUSE_ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

# --- Front end ---
FRONTEND_DIR = ROOT_DIR / "frontend"