import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import db
import seed
from embeddings import DIMENSOES, MODEL_NAME, embedding_documento, embedding_pergunta, get_model

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.get_pool()
    get_model()
    if os.getenv("AUTO_SEED", "true") == "true" and db.contar_documentos() == 0:
        print("Base vazia: carregando FAQ inicial")
        seed.carregar_faq()
    yield


app = FastAPI(title="Grupo 3 - Busca Vetorial com Oracle", lifespan=lifespan)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class Documento(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    texto: str = Field(min_length=1)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/search")
def search(body: Pergunta):
    t0 = time.perf_counter()
    embedding = embedding_pergunta(body.pergunta)
    t1 = time.perf_counter()
    resultados = db.buscar_similares(embedding, body.top_k)
    t2 = time.perf_counter()

    melhor = db.obter_embedding(resultados[0]["id"]) if resultados else None
    return {
        "pergunta": body.pergunta,
        "modelo": MODEL_NAME,
        "dimensoes": len(embedding),
        "embedding": [round(x, 5) for x in embedding],
        "embedding_melhor_resultado": [round(x, 5) for x in melhor] if melhor else None,
        "tempos_ms": {"embedding": round((t1 - t0) * 1000, 1), "oracle": round((t2 - t1) * 1000, 1)},
        "resultados": resultados,
    }


@app.get("/stats")
def stats():
    return {"documentos": db.contar_documentos(), "modelo": MODEL_NAME, "dimensoes": DIMENSOES}


@app.post("/documents", status_code=201)
def criar_documento(body: Documento):
    embedding = embedding_documento(body.titulo, body.texto)
    novo_id = db.inserir_documento(body.titulo, body.texto, embedding)
    return {"id": novo_id, "titulo": body.titulo}


@app.get("/documents")
def listar_documentos():
    return db.listar_documentos()
