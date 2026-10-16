# Roteiro da apresentação (~10 min)

Antes de começar: `docker compose up -d` e abrir http://localhost:8000.

## 1. Problema escolhido (1 min)
- FAQ de suporte de um ERP fictício (**Órbita ERP**), com 30 perguntas e respostas.
- Problema: o cliente descreve o erro com as próprias palavras ("errei a senha várias vezes e não entra mais"), mas a resposta está cadastrada com outro título ("Usuário bloqueado após tentativas de login"). Uma busca por palavra-chave (`LIKE '%errei%'`) não encontra.
- Solução: busca por **significado**, usando embeddings e o Oracle como banco vetorial.

## 2. O que é embedding e como foi gerado (2 min)
- Embedding é um vetor de números que representa o significado do texto.
- Modelo `intfloat/multilingual-e5-small`:
  - roda **localmente**, em CPU, via `sentence-transformers` (arquivo `app/embeddings.py`);
  - gera **384 dimensões**.
- Por que esse modelo:
  - é multilíngue (português);
  - é treinado para busca;
  - comparamos com outro modelo e ele acertou 12 de 16 perguntas em 1º lugar, contra 8 de 16 (tabela no README).
- Prefixos: `query:` na pergunta e `passage:` no documento.
- Na tela, abra "Como essa busca funcionou" para mostrar os 8 primeiros números do vetor.

## 3. Tabela no Oracle (1 min)
- Mostrar `sql/01-create-table.sql`, com destaque para `embedding VECTOR(384, FLOAT32)`.
- Infra (parte de DBA), em `docker/oracle/startup/01-init.sh`:
  - Oracle AI Database 26ai Free em Docker;
  - PDB `FREEPDB1`;
  - tablespace dedicado `GRUPO3_DATA`;
  - usuário `grupo3` com `DB_DEVELOPER_ROLE`.
- Coerência: modelo = 384, coluna = 384, `TO_VECTOR(..., 384, FLOAT32)` = 384.

## 4. Insert (1 min)
- Mostrar `sql/02-inserts.sql`, com `TO_VECTOR('[0.045, -0.017, ...]', 384, FLOAT32)`.
- Executar ao vivo:
  ```bash
  docker exec -i grupo3-oracle sqlplus -s grupo3/grupo3@//localhost:1521/FREEPDB1 < sql/02-inserts.sql
  ```
- Na aplicação, o mesmo insert é feito por `db.inserir_documento()`. O vetor vai como binário (`array('f')`).

## 5. Consulta por similaridade (2 min)
- Mostrar `sql/03-search.sql`: `VECTOR_DISTANCE(embedding, :pergunta, COSINE)` + `ORDER BY` + `FETCH FIRST 5 ROWS ONLY`.
- Executar ao vivo:
  ```bash
  docker exec -i grupo3-oracle sqlplus -s grupo3/grupo3@//localhost:1521/FREEPDB1 < sql/03-search.sql
  ```
- Leitura: quanto menor a distância, mais parecido o significado.
- A consulta 2 do arquivo mostra documentos parecidos com outro documento, só com vetores que já estão no banco.

## 6. Demonstração (3 min)
Perguntas que funcionam bem:

| Pergunta | Encontra |
|---|---|
| esqueci minha senha | Como redefinir minha senha |
| errei a senha várias vezes e não entra mais | Usuário bloqueado após tentativas de login |
| a SEFAZ recusou minha nota | Nota fiscal rejeitada pela SEFAZ |
| como mando cobrança pro cliente | Emitir boleto para um cliente |
| quero tirar um relatório em planilha | Exportar relatórios para Excel ou PDF |
| quanto tempo tenho pra desfazer uma NF | Cancelar uma nota fiscal emitida |
| o banco mostra um valor e o sistema outro | Conciliação bancária |

Momentos para destacar:
- Cadastrar um documento novo pela tela ("Cadastrar novo documento") e buscar por ele em seguida.
- Mostrar que os documentos inseridos via SQL (idioma, impressora de etiquetas) também aparecem na busca: perguntar "quero o sistema em inglês".

## Possíveis perguntas do professor
- **E se trocar o modelo?** É preciso regenerar todos os embeddings (`python seed.py`). Vetores de modelos diferentes não são comparáveis, e a dimensão da coluna precisa ser a mesma do modelo.
- **Por que COSINE?** O modelo foi treinado para similaridade de cosseno, e os vetores são normalizados.
- **Escala?** Com muitos documentos, criaríamos um índice vetorial (`CREATE VECTOR INDEX ... ORGANIZATION INMEMORY NEIGHBOR GRAPH` para HNSW) e a busca passaria a ser aproximada. Com 30 documentos, a busca exata é instantânea.
- **Onde entraria um LLM?** Os top 3 resultados virariam contexto de um prompt para um modelo gerar a resposta em linguagem natural (RAG). Ficou fora do escopo para manter a solução simples.
