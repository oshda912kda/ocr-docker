import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

app = FastAPI(title="OCR PDF Service")

# Limita trabajos simultáneos. OCR consume bastante CPU/RAM.
OCR_CONCURRENCY = 1
semaphore = asyncio.Semaphore(OCR_CONCURRENCY)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr")
async def ocr_pdf(
    file: UploadFile = File(...),
    lang: str = Form("spa+eng"),
    force: bool = Form(False),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    async with semaphore:
        workdir = Path(tempfile.mkdtemp(prefix="ocr-"))
        input_pdf = workdir / "input.pdf"
        output_pdf = workdir / "output.pdf"

        try:
            with input_pdf.open("wb") as f:
                shutil.copyfileobj(file.file, f)

            cmd = [
                "ocrmypdf",
                "-l",
                lang,
                "--rotate-pages",
                "--deskew",
                "--optimize",
                "1",
                "--jobs",
                "2",
            ]

            if force:
                cmd.append("--force-ocr")
            else:
                cmd.append("--skip-text")

            cmd.extend([str(input_pdf), str(output_pdf)])

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=900,
            )

            if result.returncode != 0:
                shutil.rmtree(workdir, ignore_errors=True)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "OCR falló",
                        "stderr": result.stderr[-4000:],
                    },
                )

            return FileResponse(
                output_pdf,
                media_type="application/pdf",
                filename=f"ocr-{file.filename}",
                background=BackgroundTask(
                    lambda: shutil.rmtree(workdir, ignore_errors=True)
                ),
            )

        except subprocess.TimeoutExpired:
            shutil.rmtree(workdir, ignore_errors=True)
            raise HTTPException(status_code=504, detail="OCR timeout")
