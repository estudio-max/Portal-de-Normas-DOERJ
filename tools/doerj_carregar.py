"""Carrega o JSONL da extração no banco.

    python tools/doerj_carregar.py extraido/*.jsonl
    python tools/doerj_carregar.py extraido/*.jsonl --pdf dados
    python tools/doerj_carregar.py --autoteste

Ligação pelo ambiente, com padrão de desenvolvimento local:

    DOERJ_HOST    127.0.0.1
    DOERJ_PORT    3306
    DOERJ_USER    root
    DOERJ_SENHA   vazia
    DOERJ_BANCO   doerj

Nunca senha em linha de comando: ela fica no histórico do shell e na lista de
processos da máquina.


IDEMPOTENTE, E DE GRAÇA
-----------------------

O IOERJ fecha cada matéria publicada com um `Id: 2765345`. Esse número é dele,
não nosso, e é único. Como `atos.id_ioerj` é `UNIQUE`, recarregar a mesma edição
atualiza as mesmas linhas em vez de duplicar o Diário do dia.

Isso importa mais do que parece: a extração vai ser refeita muitas vezes
conforme o reconhecimento melhora, e cada refazer precisa ser seguro.


O QUE ELE NÃO DECIDE
--------------------

Carrega **toda** matéria, com número ou sem. Se movimentação de pessoal entra no
portal é a DP-05, e a resposta pertence a quem responde pelo produto — não ao
programa que escreve no banco. O que ele faz é marcar `reconhecido`, para a
decisão poder ser tomada depois com um `WHERE` em vez de uma recoleta.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

try:
    import pymysql
except ImportError:  # pragma: no cover
    sys.exit("Falta o PyMySQL. Instale com: pip install pymysql")

BASE_DO_PDF = "https://www.ioerj.com.br/portal/modules/conteudoonline/mostra_edicao.php?k="


def ligar():
    return pymysql.connect(
        host=os.environ.get("DOERJ_HOST", "127.0.0.1"),
        port=int(os.environ.get("DOERJ_PORT", "3306")),
        user=os.environ.get("DOERJ_USER", "root"),
        password=os.environ.get("DOERJ_SENHA", ""),
        database=os.environ.get("DOERJ_BANCO", "doerj"),
        charset="utf8mb4",
        autocommit=False,
    )


def chave_do_pdf(guid: str) -> str:
    """O GUID com uma letra na posição 12. Ver o `doerj_download.py`."""
    return guid[:12] + "P" + guid[12:]


def apelido(texto: str | None) -> str | None:
    if not texto:
        return None
    sem = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    s = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", sem.lower())).strip("-")
    return s[:120] or None


def identificador(registro: dict) -> str:
    """O endereço público do ato. Legível quando dá, estável sempre.

    Legível importa: é o que vai na URL e o que alguém cola num ofício. Mas
    legibilidade não pode custar unicidade, então o identificador da origem
    entra no fim quando o ato tem número, e sozinho quando não tem.
    """
    data = registro["data_pub"]
    ioerj = registro.get("id_ioerj") or ""
    if registro.get("tipo") and registro.get("numero"):
        miolo = apelido(f"{registro['tipo']}-{registro['numero']}")
        return f"{data}-{miolo}-{ioerj}"[:191]
    return f"{data}-m{ioerj}"[:191]


def ano_de(registro: dict) -> int | None:
    data = registro.get("data_ato") or registro.get("data_pub")
    return int(data[:4]) if data else None


def gravar_edicao(cursor, registro: dict, pdf: Path | None) -> int | None:
    """Garante a linha de `edicoes` e devolve o id. Sem PDF em mãos, devolve o
    que já estiver gravado, porque a edição pode ter vindo de outra execução."""
    data, caderno = registro.get("data_pub"), registro.get("caderno")
    sequencia = registro.get("sequencia") or 1
    if not data or not caderno:
        return None

    cursor.execute(
        "SELECT id FROM edicoes WHERE data_pub=%s AND caderno_slug=%s AND sequencia=%s",
        (data, caderno, sequencia),
    )
    achado = cursor.fetchone()
    if achado:
        return achado[0]

    if pdf is None or not pdf.exists():
        return None

    bytes_ = pdf.read_bytes()
    sha = hashlib.sha256(bytes_).hexdigest()
    paginas = None
    try:
        import fitz

        with fitz.open(stream=bytes_, filetype="pdf") as d:
            paginas = d.page_count
    except Exception:
        pass

    # O GUID não está no JSONL: ele vive na listagem do IOERJ, e o extrator não
    # o vê. Fica nulo até alguém religar as duas pontas, e a URL fica nula
    # junto — nula é melhor que inventada.
    cursor.execute(
        "INSERT INTO edicoes (data_pub, caderno, caderno_slug, sequencia, guid,"
        " url_pdf, paginas, bytes, sha256)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (data, caderno.replace("-", " ").title(), caderno, sequencia,
         f"sem-guid-{data}-{caderno}"[:36], "", paginas, len(bytes_), sha),
    )
    return cursor.lastrowid


def carregar(caminho: Path, pasta_pdf: Path | None) -> tuple[int, int, int]:
    registros = [
        json.loads(linha)
        for linha in caminho.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]
    if not registros:
        return 0, 0, 0

    pdf = None
    if pasta_pdf:
        candidatos = list(pasta_pdf.rglob(f"{caminho.stem}.pdf"))
        pdf = candidatos[0] if candidatos else None

    ligacao = ligar()
    novos = atualizados = pulados = 0
    try:
        with ligacao.cursor() as c:
            edicao_id = gravar_edicao(c, registros[0], pdf)

            for r in registros:
                if not r.get("id_ioerj"):
                    pulados += 1
                    continue

                c.execute("SELECT id FROM atos WHERE id_ioerj=%s", (r["id_ioerj"],))
                ja = c.fetchone()
                ident = ja[0] if ja else identificador(r)

                campos = (
                    edicao_id, r["id_ioerj"], r.get("tipo"), r.get("numero"),
                    ano_de(r), r.get("data_ato"), r["data_pub"],
                    r.get("orgao"), apelido(r.get("orgao")),
                    r.get("ementa"), 1 if r.get("ementa_inferida") else 0,
                    r.get("cabecalho"), 1 if r.get("reconhecido") else 0,
                    r.get("atos_no_texto") or 0,
                    str(r.get("pagina") or "")[:8],
                )

                if ja:
                    c.execute(
                        "UPDATE atos SET edicao_id=%s, id_ioerj=%s, tipo=%s, numero=%s,"
                        " ano=%s, data_ato=%s, data_pub=%s, orgao=%s, orgao_slug=%s,"
                        " ementa=%s, ementa_inferida=%s, cabecalho=%s, reconhecido=%s,"
                        " atos_no_texto=%s, pagina=%s WHERE id=%s",
                        campos + (ident,),
                    )
                    atualizados += 1
                else:
                    c.execute(
                        "INSERT INTO atos (edicao_id, id_ioerj, tipo, numero, ano,"
                        " data_ato, data_pub, orgao, orgao_slug, ementa,"
                        " ementa_inferida, cabecalho, reconhecido, atos_no_texto,"
                        " pagina, id)"
                        " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        campos + (ident,),
                    )
                    novos += 1

                # O corpo mora à parte, e `REPLACE` resolve os dois casos: a
                # primeira carga e a recarga depois de a extração melhorar.
                c.execute(
                    "REPLACE INTO ato_corpo (ato_id, texto) VALUES (%s, %s)",
                    (ident, r.get("texto") or ""),
                )

            if edicao_id:
                c.execute(
                    "UPDATE edicoes SET extraido_em = NOW() WHERE id = %s", (edicao_id,)
                )
        ligacao.commit()
    except Exception:
        # Meia edição no banco é pior que nenhuma: quem consultasse veria um
        # Diário que existe pela metade, sem nada avisando.
        ligacao.rollback()
        raise
    finally:
        ligacao.close()

    return novos, atualizados, pulados


def autoteste() -> int:
    assert chave_do_pdf("B8EA790C-E3E3-4518-BD90-0E237E54B7CA") == \
        "B8EA790C-E3EP3-4518-BD90-0E237E54B7CA"

    assert apelido("Secretaria de Estado de Educação") == "secretaria-de-estado-de-educacao"
    assert apelido("Parte IB - (Tribunal de Contas)") == "parte-ib-tribunal-de-contas"
    assert apelido(None) is None
    assert apelido("") is None

    com = {"data_pub": "2026-09-22", "id_ioerj": "2765346",
           "tipo": "Decreto", "numero": "50.485"}
    assert identificador(com) == "2026-09-22-decreto-50-485-2765346", identificador(com)

    sem = {"data_pub": "2026-09-22", "id_ioerj": "2765353", "tipo": None, "numero": None}
    assert identificador(sem) == "2026-09-22-m2765353", identificador(sem)

    # Dois decretos de mesmo número no mesmo dia não podem colidir: o
    # identificador da origem no fim é o que garante isso.
    a = {"data_pub": "2026-09-22", "id_ioerj": "111", "tipo": "Decreto", "numero": "1"}
    b = {"data_pub": "2026-09-22", "id_ioerj": "222", "tipo": "Decreto", "numero": "1"}
    assert identificador(a) != identificador(b)

    assert len(identificador({"data_pub": "2026-09-22", "id_ioerj": "1",
                              "tipo": "Resolução " * 40, "numero": "1"})) <= 191

    assert ano_de({"data_ato": "2015-11-18", "data_pub": "2026-09-22"}) == 2015
    assert ano_de({"data_ato": None, "data_pub": "2026-09-22"}) == 2026
    assert ano_de({"data_ato": None, "data_pub": None}) is None

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("jsonl", nargs="*", type=Path)
    p.add_argument("--pdf", type=Path, default=None,
                   help="pasta dos PDFs, para preencher páginas e impressão digital")
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.jsonl:
        p.error("informe ao menos um .jsonl, ou --autoteste")

    falhas = 0
    for caminho in o.jsonl:
        try:
            novos, atualizados, pulados = carregar(caminho, o.pdf)
        except Exception as e:
            print(f"{caminho.name}: FALHOU, {e}", file=sys.stderr)
            falhas += 1
            continue
        extra = f", {pulados} sem identificador" if pulados else ""
        print(f"{caminho.name}: {novos} novo(s), {atualizados} atualizado(s){extra}")

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
