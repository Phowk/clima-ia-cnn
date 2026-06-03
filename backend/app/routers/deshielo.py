from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from fastapi import File

from services.deshielo.predictor import predict_glacier

router = APIRouter(
    prefix="/deshielo",
    tags=["Deshielo"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/analizar")
async def analizar(
    imagen: UploadFile = File(...)
):

    ruta = UPLOAD_DIR / imagen.filename

    with open(ruta, "wb") as buffer:
        buffer.write(await imagen.read())

    resultado = predict_glacier(ruta)

    return resultado