# V86 Alias Engine - Production Docker Image
FROM python:3.11-slim

WORKDIR /app

COPY startup/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY v86_alias_engine_prototype.py .
COPY alias_task_adapter.py .
COPY alias_engine_warmup_optimize.py .
COPY alias_gate_auto_check.py .
COPY v86_alias_full_replay.py .

COPY --from=v85-base /v85/ /v85/

RUN mkdir -p /var/cache/v86-alias /var/log/v86-alias

COPY startup/start_alias_engine.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start_alias_engine.sh

ENV V86_ALIAS_MODE=f3+f4
ENV V86_CACHE_DIR=/var/cache/v86-alias
ENV V86_LOG_DIR=/var/log/v86-alias
ENV V86_HEALTH_PORT=8080
ENV V86_METRICS_PORT=8081

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/usr/local/bin/start_alias_engine.sh"]
