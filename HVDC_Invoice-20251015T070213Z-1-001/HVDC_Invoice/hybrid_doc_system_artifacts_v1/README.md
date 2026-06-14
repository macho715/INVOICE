# Hybrid FastAPI + Celery + KEDA (RabbitMQ)

- **FastAPI** upload → Celery enqueue → Worker parse → status/result API.
- **RabbitMQ** broker / **Redis** backend.
- **KEDA** scales `worker` by **queue length**.

## Build & Run (Compose)
```bash
docker compose build
docker compose up -d
curl -F "file=@sample.pdf" http://localhost:8080/upload
```

## KEDA (Kubernetes)
```bash
kubectl apply -f k8s/50-keda-rabbitmq.yaml
# Requires KEDA installed and deployments/services present
```
