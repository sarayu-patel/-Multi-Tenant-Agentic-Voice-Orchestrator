# Stage 1: install dependencies into a clean layer
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: final image — copy only what's needed
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

# Cloud Run injects PORT at runtime; default to 8080 locally
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
