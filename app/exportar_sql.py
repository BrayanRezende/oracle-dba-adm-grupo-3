import sys

from embeddings import DIMENSOES, MODEL_NAME, embedding_documento, embedding_pergunta

NOVOS_DOCS = [
    ("Trocar o idioma do sistema",
     "O Órbita ERP está disponível em português, inglês e espanhol. Para trocar o idioma, "
     "acesse Meu Perfil > Preferências > Idioma e salve. A alteração vale apenas para o seu usuário."),
    ("Configurar impressora de etiquetas",
     "Para imprimir etiquetas de código de barras, instale o agente de impressão disponível em "
     "Configurações > Impressão, selecione a impressora térmica e o tamanho da etiqueta. "
     "Teste a impressão antes de usar em produção."),
]

PERGUNTA = "esqueci minha senha"


def literal(vetor: list[float]) -> str:
    nums = [f"{x:.5f}" for x in vetor]
    linhas = [",".join(nums[i:i + 16]) for i in range(0, len(nums), 16)]
    return "'[" + ",\n".join(linhas) + "]'"


def sql_literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def inserts() -> str:
    out = [
        f"-- Embeddings gerados com {MODEL_NAME} ({DIMENSOES} dims)",
        "",
    ]
    for titulo, texto in NOVOS_DOCS:
        vetor = embedding_documento(titulo, texto)
        out += [
            "INSERT INTO kb_docs (titulo, texto, embedding)",
            "VALUES (",
            f"  {sql_literal(titulo)},",
            f"  {sql_literal(texto)},",
            f"  TO_VECTOR({literal(vetor)}, {DIMENSOES}, FLOAT32)",
            ");",
            "",
        ]
    out += ["COMMIT;", ""]
    return "\n".join(out)


def search() -> str:
    vetor = embedding_pergunta(PERGUNTA)
    return "\n".join([
        f"-- Pergunta: '{PERGUNTA}' ({MODEL_NAME}, {DIMENSOES} dims)",
        "",
        "SET LINESIZE 200",
        "COLUMN titulo FORMAT A45",
        "COLUMN formato FORMAT A10",
        "COLUMN inicio_do_vetor FORMAT A90",
        "",
        "-- Top 5 mais próximos da pergunta",
        "WITH pergunta AS (",
        f"  SELECT TO_VECTOR({literal(vetor)}, {DIMENSOES}, FLOAT32) AS v",
        "  FROM dual",
        ")",
        "SELECT d.id,",
        "       d.titulo,",
        "       ROUND(VECTOR_DISTANCE(d.embedding, p.v, COSINE), 4) AS distancia",
        "FROM kb_docs d CROSS JOIN pergunta p",
        "ORDER BY distancia",
        "FETCH FIRST 5 ROWS ONLY;",
        "",
        "-- Documentos parecidos com um documento da base",
        "SELECT d.id,",
        "       d.titulo,",
        "       ROUND(VECTOR_DISTANCE(d.embedding, ref.embedding, COSINE), 4) AS distancia",
        "FROM kb_docs d",
        "JOIN kb_docs ref ON ref.titulo = 'Nota fiscal rejeitada pela SEFAZ'",
        "WHERE d.id <> ref.id",
        "ORDER BY distancia",
        "FETCH FIRST 5 ROWS ONLY;",
        "",
        "-- Vetor gravado",
        "SELECT id,",
        "       VECTOR_DIMENSION_COUNT(embedding) AS dimensoes,",
        "       VECTOR_DIMENSION_FORMAT(embedding) AS formato,",
        "       DBMS_LOB.SUBSTR(FROM_VECTOR(embedding RETURNING CLOB), 80, 1) || '...' AS inicio_do_vetor",
        "FROM kb_docs",
        "WHERE id <= 3;",
        "",
    ])


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo == "inserts":
        print(inserts())
    elif modo == "search":
        print(search())
    else:
        sys.exit("uso: python exportar_sql.py inserts|search")
