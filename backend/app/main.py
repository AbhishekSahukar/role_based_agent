import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.routers import chat, public_config, whoami

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="AskHR API")

app.include_router(public_config.router)
app.include_router(whoami.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Mounted LAST: "/" catches every path not matched above.
app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="frontend")