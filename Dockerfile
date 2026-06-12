FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ocrmypdf \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    ghostscript \
    unpaper \
    qpdf \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn python-multipart

WORKDIR /app

COPY app.py /app/app.py

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
