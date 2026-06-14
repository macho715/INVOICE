from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, uuid, json
from celery.result import AsyncResult
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@broker:5672//")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

celery_app = Celery("hybrid", broker=BROKER_URL, backend=RESULT_BACKEND)

app = FastAPI(title="Hybrid Doc API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SubmitResponse(BaseModel):
    task_id: str
    filename: str

@app.post("/upload", response_model=SubmitResponse)
async def upload(file: UploadFile = File(...)):
    # Save to disk
    ext = os.path.splitext(file.filename)[1]
    doc_id = str(uuid.uuid4())[:8]
    dest = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
    with open(dest, "wb") as f:
        f.write(await file.read())

    # Enqueue task
    task = celery_app.send_task("worker.parse_document", args=[dest], kwargs={})
    return SubmitResponse(task_id=task.id, filename=file.filename)

@app.get("/status/{task_id}")
def status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": res.status}

@app.get("/result/{task_id}")
def result(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    if not res.ready():
        return JSONResponse({"task_id": task_id, "status": res.status})
    if res.failed():
        raise HTTPException(status_code=500, detail=str(res.result))
    return JSONResponse({"task_id": task_id, "status": "SUCCESS", "data": res.result})
