from fastapi import FastAPI
from routes import router

app = FastAPI()

# Incluir rutas
app.include_router(router)

