# ==========================================
# Multi-stage Dockerfile for FastAPI Service
# ==========================================

# ----------------- Stage 1: Builder -----------------
FROM python:3.11-slim as builder

WORKDIR /build

# Установка системных зависимостей для сборки (gcc, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка виртуального окружения и зависимостей приложения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ----------------- Stage 2: Runtime -----------------
FROM python:3.11-slim as runner

WORKDIR /app

# Установка только runtime-библиотек (libpq5 для postgres) и curl для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя для безопасности (best practice)
RUN groupadd -g 1001 appuser && \
    useradd -u 1001 -g appuser -s /bin/sh appuser

# Копируем установленные зависимости из стадии builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем исходный код приложения
COPY app /app/app

# Назначаем права пользователю
RUN chown -R appuser:appuser /app
USER appuser

# Открываем порт микросервиса
EXPOSE 8000

# Healthcheck контейнера
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Запуск Uvicorn ASGI сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
