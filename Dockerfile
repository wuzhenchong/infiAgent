FROM python:3.12-slim-bookworm

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY
ARG http_proxy
ARG https_proxy
ARG all_proxy

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

RUN HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" ALL_PROXY="${ALL_PROXY}" \
    http_proxy="${http_proxy}" https_proxy="${https_proxy}" all_proxy="${all_proxy}" \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    lsof \
    procps \
    tini \
    && rm -rf /var/lib/apt/lists/*
COPY MANIFEST.in pyproject.toml requirements.txt setup.py README.md start.py /app/
COPY config /app/config
COPY core /app/core
COPY infiagent /app/infiagent
COPY services /app/services
COPY skills /app/skills
COPY tool_server_lite /app/tool_server_lite
COPY utils /app/utils
COPY web_ui /app/web_ui
COPY docker /app/docker

RUN HTTP_PROXY="${HTTP_PROXY}" HTTPS_PROXY="${HTTPS_PROXY}" ALL_PROXY="${ALL_PROXY}" \
    http_proxy="${http_proxy}" https_proxy="${https_proxy}" all_proxy="${all_proxy}" \
    python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install . \
    && python -m pip install -r web_ui/requirements.txt \
    && python -m playwright install --with-deps chromium

RUN chmod +x /app/docker/entrypoint.sh
RUN mkdir -p /workspace /root/mla_v3

EXPOSE 4242

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:4242/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/app/docker/entrypoint.sh"]
CMD ["webui"]
