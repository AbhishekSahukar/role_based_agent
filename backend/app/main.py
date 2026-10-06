import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.mcp_server import mcp, mcp_http_app
from app.routers import chat, public_config, whoami

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
# Azure SDK logs every HTTP request at INFO; keep only its warnings and errors.
logging.getLogger("azure").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A mounted sub-app's own startup doesn't run, so start the MCP
    # session manager here, for the lifetime of the whole app.
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="AskHR API", lifespan=lifespan)

app.include_router(public_config.router)
app.include_router(whoami.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# MCP server: http://localhost:8000/tools/mcp (token required)
app.mount("/tools", mcp_http_app)

# Mounted LAST: "/" catches every path not matched above.
app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")