from fastapi import FastAPI
from routes import router

app = FastAPI()

# Incluir rutas
app.include_router(router)

@app.get('/')
async def read_root():
    return {'message': '¡uvicorn funciona correctamente!'}

