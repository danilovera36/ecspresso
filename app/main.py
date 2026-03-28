import time
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import engine, Base, get_db
from .routers import variables, secrets, task_definitions, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="ecspresso API", version="0.1.0")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(variables.router)
app.include_router(secrets.router)
app.include_router(task_definitions.router)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"status": "error", "database": "disconnected"}

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("app/static/index.html", "r") as f:
        return f.read()
