import logging
from fastapi import FastAPI
from app.routers import whoami

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="AskHR API")
app.include_router(whoami.router)


@app.get("/health")
def health():
    return {"status": "ok"}