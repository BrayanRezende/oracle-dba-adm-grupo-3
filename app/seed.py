import json
from pathlib import Path

import db
from embeddings import embedding_documento

ARQUIVO = Path(__file__).parent / "data" / "faq.json"


def carregar_faq() -> int:
    docs = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    db.apagar_todos()
    for doc in docs:
        embedding = embedding_documento(doc["titulo"], doc["texto"])
        novo_id = db.inserir_documento(doc["titulo"], doc["texto"], embedding)
        print(f"[{novo_id:>3}] {doc['titulo']}")
    return len(docs)


if __name__ == "__main__":
    total = carregar_faq()
    print(f"{total} documentos gravados em kb_docs")
