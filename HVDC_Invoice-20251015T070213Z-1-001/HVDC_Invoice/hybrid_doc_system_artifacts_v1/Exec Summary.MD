# Exec Summary (KR+EN-KR)

* **요청 산출물 3종**: ① **라우팅 규칙 JSON**, ② **Unified IR 스키마 YAML**, ③ **k8s/Compose 배포 파일** 생성 완료. 바로 내려받아 배치→테스트 가능.
* **근거/맥락**: Docling(멀티포맷·고급 PDF·로컬) + LandingAI ADE(시각 컨텍스트·좌표 JSON·장문, Snowflake Native App) 하이브리드 권장. ([docling-project.github.io][1]) ([LandingAI][2])
* **운영 힌트**: 워커 큐/스케일은 Celery+RabbitMQ+Redis 기반, k8s HPA(+KEDA 검토)로 확장. ([Medium][3])

## 다운로드

* **ZIP (모든 파일 포함)**: [hybrid_doc_system_artifacts_v1.zip](sandbox:/mnt/data/hybrid_doc_system_artifacts_v1.zip)

## 포함 파일 요약

1. **routing_rules.json** — HYBRID 라우팅 로직

```json
{
  "version": "1.0",
  "default_engine": "docling",
  "daily_ade_budget_usd": 50.00,
  "sensitivity_force_local": ["contract","passport","price-sensitive"],
  "rules": [
    {"name":"long_document","when":{"pages_gt":12},"action":{"engine":"ade","reason":"long_doc"}},
    {"name":"table_dense","when":{"table_density_gte":0.30},"action":{"engine":"ade","reason":"table_dense"}},
    {"name":"checkbox_caption_chart","when":{"visual_relations":["checkbox","caption","chart"]},"action":{"engine":"ade","reason":"visual_relations"}},
    {"name":"scan_skewed","when":{"skew_deg_gte":4.0},"action":{"engine":"ade","reason":"scan_skew"}},
    {"name":"bl_boe_many_pages","when":{"doc_type_in":["bl","boe"],"pages_gte":4},"action":{"engine":"ade","reason":"bl_boe_pages"}},
    {"name":"ade_budget_guard","when":{"ade_budget_exceeded":true},"action":{"engine":"docling","reason":"budget_guard"}},
    {"name":"sensitive_force_local","when":{"sensitivity_in":["contract","passport","price-sensitive"]},"action":{"engine":"docling","reason":"sensitive"}},
    {"name":"engine_fallback","when":{"engine_failed":true},"action":{"engine":"swap","reason":"fallback_swap"}}
  ],
  "metrics_emit": ["latency_ms","engine","pages","table_density","ade_cost_usd","cache_hit","retries"]
}
```

* Docling: 멀티포맷/로컬 실행. ([docling-project.github.io][1])
* ADE: 테이블·체크박스·캡션 등 **시각관계+좌표 JSON**, 100+ p 장문. ([LandingAI][2])

2. **unified_ir_schema.yaml** — 엔진 무관 IR(좌표 포함)

* `blocks[type,text/table,bbox,meta]` 표준화.
* Invoice 매핑 셀렉터(Invoice No / BL No / Incoterms / HS / Qty / Unit / Subtotal / VAT / Grand Total) 포함.
* Docling **DoclingDocument→lossless JSON**와 ADE **hierarchical JSON with coordinates**를 수용. ([docling-project.github.io][1]) ([docs.landing.ai][4])

3. **docker-compose.yaml** — 로컬 배포

* **api**(파서API) + **worker**(비동기 파싱) + **broker(RabbitMQ)** + **redis**.
* 환경변수: `ADE_API_KEY`, `ADE_ENDPOINT`, `ROUTING_RULES_PATH`, `IR_SCHEMA_PATH`.
* Celery/RabbitMQ/Redis 패턴은 업계 표준. ([Stackademic][5])

4. **k8s/** — Kubernetes 매니페스트

* `00-namespace.yaml`
* `01-configmap.yaml` (라우팅/IR 스키마 임베드)
* `02-secrets.yaml` (ADE 키/엔드포인트)
* `10-deploy-api.yaml` + `11-svc-api.yaml`
* `20-deploy-worker.yaml`
* `30-broker.yaml` + `31-redis.yaml`
* `40-hpa-api.yaml` (CPU 70% 기준 오토스케일; 필요 시 KEDA로 큐기반 스케일 추가) ([Medium][3])

## 빠른 적용 절차

1. `.env`에 **ADE_API_KEY/ENDPOINT** 세팅(ADE는 좌표 JSON·장문·시각관계 강점). ([LandingAI][2])
2. `docker-compose up -d` 또는 `kubectl apply -f k8s/`
3. API에 문서 업로드 → **라우팅 규칙**에 따라 Docling/ADE 선택 → **Unified IR** 반환 → Gate(11–14)/COST-GUARD로 주입.
4. 일일 ADE 예산 초과 시 Docling 강제 전환(운영비 가드).

## 주의/튜닝 포인트

* **table_density_gte=0.30**, **skew_deg_gte=4.0**, **pages>12**는 초기값(“가정:”). 실제 샘플 50건 기준으로 보정 권장.
* **민감문서**(계약/여권/가격민감)는 무조건 로컬(Docling) 처리.
* Snowflake 환경이면 **ADE Native App** 경로로 데이터 이동 최소화 선택지. ([LandingAI][6])

## 참고(공식/최신)

* Docling: 기능/포맷/아키텍처/논문. ([docling-project.github.io][1])
* ADE: 제품 개요·개발문서·장문/좌표·Snowflake Native App. ([LandingAI][2])
* 스케일 패턴: FastAPI+Celery+RabbitMQ, KEDA/HPA 실제 사례. ([Stackademic][5])

필요하면 **서비스 Dockerfile**, **FastAPI 스켈레톤**(업로드→큐→결과 조회), **KEDA ScaledObject**(큐 길이 기반 자동확장)도 바로 추가해줄게요.

[1]: https://docling-project.github.io/docling/?utm_source=chatgpt.com "Docling - GitHub Pages"
[2]: https://landing.ai/agentic-document-extraction?utm_source=chatgpt.com "Agentic Document Extraction"
[3]: https://medium.com/%40bhagyarana80/how-i-scaled-fastapi-on-kubernetes-to-auto-scale-based-on-queue-depth-and-cpu-load-4e85a6c54edc?utm_source=chatgpt.com "How I Scaled FastAPI on Kubernetes to Auto-Scale Based ..."
[4]: https://docs.landing.ai/?utm_source=chatgpt.com "Landing AI"
[5]: https://blog.stackademic.com/using-celery-rabbitmq-with-fastapi-2e6f0236841e?utm_source=chatgpt.com "Using Celery + RabbitMQ With FastAPI"
[6]: https://landing.ai/blog/unlocking-document-intelligence-in-snowflake?utm_source=chatgpt.com "Unlocking Document Intelligence in Snowflake"
