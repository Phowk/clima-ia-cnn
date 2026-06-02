from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from services.predictor import get_model,predict_image

router = APIRouter(
    prefix="/deforestacion",
    tags=["Deforestacion"]
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

    resultado = predict_image(ruta)

    return resultado

@router.get("/test-model")
def test_model():

    model = get_model()

    return {
        "status": "ok",
        "input_shape": str(model.input_shape)
    }