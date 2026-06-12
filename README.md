# OCR PDF Service

Servicio HTTP stateless para aplicar OCR a PDFs usando OCRmyPDF.

## Endpoint

POST /ocr

Campos multipart:

- file: PDF
- lang: idioma OCR, por defecto spa+eng
- force: true/false, por defecto false

## Ejemplo

curl -X POST https://ocr.example.com/ocr \
  -F "file=@documento.pdf" \
  -F "lang=spa+eng" \
  -F "force=false" \
  -o documento-ocr.pdf
