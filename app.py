import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from starlette.background import BackgroundTask
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()


@app.post("/ocr")
async def ocr_pdf(
    file: UploadFile = File(...),
    lang: str = "spa+eng",
    force: bool = False,
):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    workdir = tempfile.mkdtemp(prefix="ocr-")
    input_pdf = Path(workdir) / "input.pdf"
    output_pdf = Path(workdir) / "output.pdf"

    try:
        with input_pdf.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        cmd = [
            "ocrmypdf",
            "-l", lang,
            "--rotate-pages",
            "--deskew",
            "--optimize", "1",
            "--jobs", "2",
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
            filename=f"ocr-{file.filename or 'document.pdf'}",
            background=BackgroundTask(lambda: shutil.rmtree(workdir, ignore_errors=True)),
        )

    finally:
        # Ojo: FileResponse puede necesitar el archivo hasta terminar de enviarlo.
        # En producción conviene borrar con BackgroundTask.
        pass
