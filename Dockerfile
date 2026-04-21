FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY serpzilla_client.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Запуск MCP сервера
CMD ["python", "-u", "server.py"]

