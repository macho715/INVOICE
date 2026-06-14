import os, json, time, hashlib
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@broker:5672//")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
ROUTING_RULES_PATH = os.getenv("ROUTING_RULES_PATH", "/app/config/routing_rules.json")

app = Celery("worker", broker=BROKER_URL, backend=RESULT_BACKEND)

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

@app.task(name="worker.parse_document", bind=True)
def parse_document(self, path: str):
    # Demo: emulate parsing latency and return stub result
    # In real use, import Docling/ADE extractors and route by rules
    t0 = time.time()
    checksum = sha256_file(path)
    time.sleep(0.5)  # simulate
    result = {
        "engine": "docling",  # or "ade" based on routing
        "path": path,
        "checksum": checksum,
        "blocks": [
            {"type": "text", "text": "Hello from worker", "bbox": {"page": 1, "x0": 0, "y0": 0, "x1": 10, "y1": 10}},
            {"type": "table", "table": {"rows": [["Item","Qty","Total"],["A","1","100.00"]]}, "bbox": {"page": 1, "x0": 10, "y0": 10, "x1": 100, "y1": 50}}
        ],
        "latency_ms": int((time.time() - t0)*1000)
    }
    return result
