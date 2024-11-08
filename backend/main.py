# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from core.configs import settings
from routes.api import api_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os



app = FastAPI(
    title='vIAbilize - API',
    version='1.0.0',
    license="Licença Comercial vIAbilize"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    content = {"mensagem": "Bem-vindo à vIAbilize!"}
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")


app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))