# Use slim Python image
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

#---------DURING THE RUNTIME---------------------------------------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

#copy only the install packages from builder and then the application code
COPY --from=builder /install /usr/local
COPY . .

# -> Non root user
RUN useradd -m -s /bin/false appuser && chown -R appuser:appuser /app 
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]