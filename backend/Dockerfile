FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system regen \
    && useradd --system --gid regen --home-dir /app regen

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY core ./core
COPY agents ./agents
COPY scripts/mission_worker.py ./scripts/
COPY data/*.csv data/*.json ./data/
COPY main.py .

RUN chown -R regen:regen /app

USER regen

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
