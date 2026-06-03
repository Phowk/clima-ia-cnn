from fastapi import FastAPI
from routers import deforestacion
from routers import deshielo

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="ClimaIA"
)

app.include_router(deforestacion.router)
app.include_router(deshielo.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)