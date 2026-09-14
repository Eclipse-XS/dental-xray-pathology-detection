FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0 torchvision==0.26.0 \
    && pip install .
RUN mkdir -p /runtime/uploads && chown -R app:app /runtime
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn dental_xray_service.main:app --host 0.0.0.0 --port 8000"]
