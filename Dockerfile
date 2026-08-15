# =============================================================================
# Dockerfile — B3 Quote API (otimizado para produção)
# Build em 2 estágios: reduz o tamanho final da imagem e melhora o cache.
# =============================================================================

# ---------- Estágio 1: builder (instala dependências) ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Evita .pyc e força stdout sem buffer (logs em tempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copia apenas o requirements primeiro (aproveita cache de camadas)
COPY requirements.txt .

RUN pip install --prefix=/install -r requirements.txt

# ---------- Estágio 2: runtime (imagem final enxuta) ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# curl é necessário apenas para o HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copia as dependências instaladas no estágio builder
COPY --from=builder /install /usr/local

# Copia o código-fonte
COPY main.py .

# Usuário não-root (boa prática de segurança)
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Healthcheck nativo do Docker (usa o endpoint /health da API)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
