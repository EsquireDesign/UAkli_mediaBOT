FROM python:3.12-slim
WORKDIR /opt/app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd -r -u 10001 appuser && mkdir -p /opt/app/data && chown -R appuser:appuser /opt/app/data
USER appuser
CMD ["python", "-m", "app.main"]
