# Republicações do IOERJ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Preservar cada matéria republicada pelo Diário Oficial, mesmo quando ela repete o mesmo `Id:` editorial.

**Architecture:** `id_ioerj` continua sendo a transcrição fiel da fonte, mas a identidade de origem passa a ser `(edicao_id, id_ioerj)`. O MySQL impõe essa chave composta e o carregador consulta o mesmo par: uma recarga atualiza a matéria da própria edição; uma republicação em outra edição cria uma nova ocorrência.

**Tech Stack:** Python 3.9+, PyMySQL, MySQL 8.4, SQL, JSONL e PowerShell.

## Global Constraints

- Não alterar o `id_ioerj` publicado pelo IOERJ.
- Não descartar nem fundir republicações.
- Recarregar a mesma edição não pode duplicar linhas.
- A migração deve funcionar em instalação limpa e sobre a produção existente.
- Publicar somente após a base limpa, relações, prazos e toda a suíte passarem.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `backend/db/011-identidade-da-publicacao.sql` | Troca a unicidade global pela chave da edição. |
| `backend/db/instalar.sql` | Instala do zero as migrações 001–011. |
| `backend/db/provar_esquema.py` | Prova a chave composta contra MySQL real. |
| `tools/doerj_carregar.py` | Carrega por edição + ID e protege a URL pública contra colisão. |
| `tools/doerj_extrair.py` | Mantém os testes de marcador editorial isolado. |
| `ARCHITECTURE.md`, `REQUIREMENTS.md`, `STEPS.md` | Registram a identidade real e os números medidos. |

### Task 1: Migrar a identidade de origem

**Files:**

- Create: `backend/db/011-identidade-da-publicacao.sql`
- Modify: `backend/db/002-materias-sem-numero.sql`
- Modify: `backend/db/instalar.sql`
- Modify: `backend/db/provar_esquema.py`

**Interfaces:**

- Consumes: o índice `uq_ioerj` e as colunas `atos.edicao_id`, `atos.id_ioerj`.
- Produces: `uq_edicao_ioerj (edicao_id, id_ioerj)`.

- [x] **Step 1: Escrever o caso que falha com a chave atual**

Depois da inserção da edição extra, definir `eid_extra` com `SELECT id FROM edicoes WHERE sequencia=2;`; depois acrescentar:

```python
roda("INSERT INTO atos (id, edicao_id, id_ioerj, data_pub, orgao_slug) "
     f"VALUES ('repub-original', {eid}, '2623228', '2026-09-22', 'teste');")
roda("INSERT INTO atos (id, edicao_id, id_ioerj, data_pub, orgao_slug) "
     f"VALUES ('repub-republicado', {eid_extra}, '2623228', '2026-09-22', 'teste');")
roda("INSERT INTO atos (id, edicao_id, id_ioerj, data_pub, orgao_slug) "
     f"VALUES ('repub-duplicado', {eid_extra}, '2623228', '2026-09-22', 'teste');",
     esperar_erro=True)
assert roda("SELECT COUNT(*) FROM atos WHERE id_ioerj='2623228';").split()[-1] == "2"
```

- [x] **Step 2: Confirmar a falha**

Run:

```powershell
$env:DOERJ_MYSQL='C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe'; $env:DOERJ_PORT='3307'; uv run --with-requirements requirements.txt python backend/db/provar_esquema.py
```

Expected: a segunda inserção é recusada por `uq_ioerj`.

- [x] **Step 3: Aplicar a migração mínima**

Create `backend/db/011-identidade-da-publicacao.sql`:

```sql
-- Uma republicação conserva o Id editorial, mas pertence a outra edição.
ALTER TABLE atos
  DROP INDEX uq_ioerj,
  ADD UNIQUE KEY uq_edicao_ioerj (edicao_id, id_ioerj);
```

Acrescentar o mesmo bloco, sob o cabeçalho `011-identidade-da-publicacao.sql`, depois de 010 no `backend/db/instalar.sql`. Atualizar em 002 e no instalador a explicação: `id_ioerj` é único dentro da edição.

- [x] **Step 4: Confirmar a passagem**

Run the command from Step 2.

Expected: `11 migrações aplicadas`, a republicação é aceita, a duplicação na mesma edição é barrada e o fim diz `TUDO PASSOU`.

- [x] **Step 5: Commit**

```powershell
git add backend/db/002-materias-sem-numero.sql backend/db/011-identidade-da-publicacao.sql backend/db/instalar.sql backend/db/provar_esquema.py
git commit -m "fix: preserve IOERJ republications per edition"
```

### Task 2: Tornar o carregador idempotente pela dupla

**Files:**

- Modify: `tools/doerj_carregar.py`

**Interfaces:**

- Consumes: `edicao_id` retornado por `gravar_edicao` e cada `registro["id_ioerj"]`.
- Produces: `identificador_com_edicao(registro: dict) -> str` e `identificador_disponivel(cursor, registro) -> str`.

- [x] **Step 1: Escrever o teste de URL em colisão**

No `autoteste()`, acrescentar:

```python
base = {"data_pub": "2026-09-22", "id_ioerj": "2623228", "tipo": "Edital",
        "numero": "1", "caderno": "parte-i", "sequencia": 1}
outro = {**base, "caderno": "parte-ib", "sequencia": 2}
assert identificador(base) == "2026-09-22-edital-1-2623228"
assert identificador_com_edicao(outro).endswith("-parte-ib-2")
```

- [x] **Step 2: Confirmar a falha**

Run:

```powershell
uv run --with-requirements requirements.txt python tools/doerj_carregar.py --autoteste
```

Expected: `NameError` para `identificador_com_edicao`.

- [x] **Step 3: Implementar consulta e fallback**

Após `identificador`, adicionar:

```python
def identificador_com_edicao(registro: dict) -> str:
    sufixo = f"-{apelido(registro.get('caderno')) or 'caderno'}-{registro.get('sequencia') or 1}"
    return f"{identificador(registro)[:191 - len(sufixo)]}{sufixo}"


def identificador_disponivel(cursor, registro: dict) -> str:
    base = identificador(registro)
    cursor.execute("SELECT id FROM atos WHERE id=%s", (base,))
    return base if cursor.fetchone() is None else identificador_com_edicao(registro)
```

Em `carregar`, substituir a busca por `id_ioerj` por:

```python
c.execute("SELECT id FROM atos WHERE edicao_id=%s AND id_ioerj=%s",
          (edicao_id, r["id_ioerj"]))
ja = c.fetchone()
ident = ja[0] if ja else identificador_disponivel(c, r)
```

Atualizar a docstring para dizer que a dupla é a chave idempotente.

- [x] **Step 4: Rodar os testes**

Run:

```powershell
uv run --with-requirements requirements.txt python tools/doerj_carregar.py --autoteste
$env:DOERJ_MYSQL='C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe'; $env:DOERJ_PORT='3307'; uv run --with-requirements requirements.txt python backend/db/provar_esquema.py
```

Expected: `autoteste: tudo certo` e `TUDO PASSOU`.

- [x] **Step 5: Commit**

```powershell
git add tools/doerj_carregar.py
git commit -m "fix: load IOERJ acts by edition and source id"
```

### Task 3: Reconstruir e provar o acervo

**Files:**

- Modify: `ARCHITECTURE.md`, `REQUIREMENTS.md`, `STEPS.md`, `tools/doerj_extrair.py`
- Generated, ignored: `extraido/*.jsonl` e banco local `doerj`

**Interfaces:**

- Consumes: 547 PDFs de `dados/` e o esquema 001–011.
- Produces: banco local com 121.022 ocorrências de matéria, inclusive republicações.

- [x] **Step 1: Rodar os autotestes da fonte**

Run:

```powershell
uv run --with-requirements requirements.txt python tools/doerj_extrair.py --autoteste
python tools/vocabulario.py
python tools/doerj_temas.py --autoteste
python tools/lgpd.py
```

Expected: todos terminam com código zero.

- [x] **Step 2: Reclassificar os JSONL**

Run:

```powershell
Get-ChildItem extraido -Filter '*.jsonl' | Group-Object { $_.Name.Substring(0,7) } | ForEach-Object { python tools/doerj_temas.py $_.Group.FullName }
```

Expected: cada mês termina sem erro.

- [x] **Step 3: Instalar banco local limpo e carregar**

Run:

```powershell
$mysql='C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe'
& $mysql -uroot -h127.0.0.1 -P3307 -e "DROP DATABASE IF EXISTS doerj; CREATE DATABASE doerj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
& $mysql -uroot -h127.0.0.1 -P3307 doerj < backend/db/instalar.sql
$env:DOERJ_PORT='3307'
Get-ChildItem extraido -Filter '*.jsonl' | Group-Object { $_.Name.Substring(0,7) } | ForEach-Object { uv run --with-requirements requirements.txt python tools/doerj_carregar.py $_.Group.FullName --pdf dados }
uv run --with-requirements requirements.txt python tools/doerj_relacoes.py
uv run --with-requirements requirements.txt python tools/doerj_prazos.py
```

Expected: 121.022 linhas (121.028 registros; 6 são a mesma matéria impressa duas vezes na mesma edição) em `atos` e nenhuma falha na carga.

- [x] **Step 4: Conferir explicitamente a republicação**

Run:

```powershell
& $mysql -uroot -h127.0.0.1 -P3307 doerj -e "SELECT COUNT(*) AS atos FROM atos; SELECT a.id, e.data_pub, e.sequencia FROM atos a JOIN edicoes e ON e.id=a.edicao_id WHERE a.id_ioerj='2623228' ORDER BY e.data_pub;"
```

Expected: `atos=121022`; duas linhas para `2623228`, em 31/01 e 03/02 de 2025.

- [x] **Step 5: Atualizar documentação e commit**

Substituir a alegação de unicidade global pela identidade composta em `ARCHITECTURE.md`, `REQUIREMENTS.md` e `STEPS.md`; registrar as 28 republicações medidas. Manter em `tools/doerj_extrair.py` os testes que aceitam somente marcador isolado.

```powershell
git add ARCHITECTURE.md REQUIREMENTS.md STEPS.md tools/doerj_extrair.py
git commit -m "fix: recognize standalone IOERJ publication markers"
```

### Task 4: Quality gate e publicação atômica

**Files:**

- Generated, ignored: pacote de banco e backup local
- Modify: `STEPS.md` se algum número medido divergir

**Interfaces:**

- Consumes: banco local aprovado e o fluxo documentado em `docs/publicacao.md`.
- Produces: produção atualizada uma vez, com backup anterior e contagens conferidas.

- [x] **Step 1: Rodar a suíte inteira**

Run:

```powershell
uv run --with-requirements requirements.txt python tools/doerj_download.py --autoteste
uv run --with-requirements requirements.txt python tools/doerj_extrair.py --autoteste
python tools/doerj_temas.py --autoteste
uv run --with-requirements requirements.txt python tools/doerj_carregar.py --autoteste
uv run --with-requirements requirements.txt python tools/doerj_relacoes.py --autoteste
python tools/doerj_prazos.py --autoteste
python tools/doerj_titulares.py --autoteste
python tools/lgpd.py
python tools/vocabulario.py
python tools/contraste.py
php app/provar_texto.php
```

Expected: todos retornam zero.

- [x] **Step 2: Gerar, validar e publicar o pacote**

Executar o comando de pacote de `docs/publicacao.md`; validar o `.sql.gz` com `tools/provar_backup.py`; copiar o pacote validado para `hostgator-fanara`; e executar `bash ~/doerj/instalar-banco.sh`.

Expected: backup gzip antes da carga, migração 011 aplicada, carga completa e sem configuração interna no pacote.

- [x] **Step 3: Verificar produção e finalizar**

Conferir no MySQL remoto a contagem igual à local, abrir `https://doerj.fanara.com.br/` e confirmar que `/interno/` continua sob autenticação HTTP. Depois:

```powershell
git status --short
git add ARCHITECTURE.md REQUIREMENTS.md STEPS.md
git commit -m "docs: record republication-aware production import"
git push origin main
```

Expected: árvore limpa e `main` sincronizada.

## Revisão do plano

- Cobertura: schema, instalador, carregador, URL pública, acervo, testes, documentação e produção estão nas Tasks 1–4.
- Placeholders: nenhum; cada arquivo, alteração, comando e resultado esperado está explícito.
- Consistência: MySQL e carregador usam `(edicao_id, id_ioerj)`; o sufixo de URL só é usado quando a URL base já existe.
