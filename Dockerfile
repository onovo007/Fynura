FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
COPY frontend ./frontend
COPY data ./data
RUN pip install --no-cache-dir .
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}

