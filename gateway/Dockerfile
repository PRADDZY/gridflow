FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/models

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --extra vision

VOLUME ["/models"]
ENTRYPOINT ["uv", "run", "--no-sync", "gridflow-gateway"]
CMD ["monitor-reference"]
