import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DIMENSOES = 384


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_embedding_dimension()
    if dim != DIMENSOES:
        raise RuntimeError(f"Modelo {MODEL_NAME} gera {dim} dimensões, a tabela espera {DIMENSOES}")
    return model


def _encode(texto: str) -> list[float]:
    return get_model().encode(texto, normalize_embeddings=True).tolist()


def embedding_pergunta(pergunta: str) -> list[float]:
    return _encode(f"query: {pergunta}")


def embedding_documento(titulo: str, texto: str) -> list[float]:
    return _encode(f"passage: {titulo}\n{texto}")
