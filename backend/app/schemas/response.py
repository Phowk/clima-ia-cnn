from pydantic import BaseModel

class PredictionResponse(BaseModel):

    porcentaje: float

    riesgo: str

    grid: list