"""Lê a capa do Diário e devolve quem comandava cada pasta naquele dia.

    python tools/doerj_titulares.py dados/2026/09/*.pdf
    python tools/doerj_titulares.py dados/**/*.pdf --csv titulares.csv
    python tools/doerj_titulares.py --autoteste


POR QUE ISTO EXISTE, E POR QUE É BARATO

Para montar a linha do tempo da SECTI é preciso saber quem esteve à frente da
pasta e, mais difícil, **como a pasta se chamava em cada época**. Ela já foi
Secretaria de Ciência e Tecnologia, já foi SECTIDS com Desenvolvimento Social
junto, e em 2026 chegou a ser unificada com Desenvolvimento Econômico antes de
ser recriada.

O caminho óbvio seria caçar decreto de nomeação, um por um. Não precisa: **a
capa de toda edição traz a lista completa dos titulares**, com o nome da pasta
como ele era naquele dia. Uma edição por semestre desde 2010 são cerca de 33
downloads, e daí sai a linha do tempo inteira.

O extrator principal descarta a capa de propósito, porque ela não é matéria.
Esta ferramenta lê só ela.


O QUE ELE NÃO FAZ

Não deduz período. Ele diz "nesta data, esta pasta tinha este titular", e nada
mais. Juntar as datas numa linha do tempo é outro trabalho, e envolve escolher o
que fazer com interinidade e com pasta que muda de nome — decisões que não cabem
a um leitor de PDF.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doerj_extrair import texto_da_linha  # noqa: E402

# O cargo vem em caixa alta e o nome da pessoa logo abaixo, em caixa mista.
CARGO = re.compile(
    r"^(SECRETARIA|SECRETARIA EXTRAORDIN[ÁA]RIA|GABINETE|PROCURADORIA|"
    r"CONTROLADORIA|DEFENSORIA|GOVERNADOR|VICE-GOVERNADOR|CHEFIA)\b"
)

# Linha pontilhada é sumário, não titular.
SUMARIO = re.compile(r"\.{6,}")

# O nome de uma pessoa tem minúsculas. Cargo e divisória não têm.
#
# O ponto é permitido, porque existe "J. Silva", mas a sequência de pontos não:
# "Casa Civil ........." é linha de sumário, e sem o veto ela passaria por nome.
PESSOA = re.compile(r"^(?!.*\.{3})[A-ZÀ-Ü][\wÀ-ÿ'\.\- ]{6,60}$")

DATA_DO_NOME = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def tem_minusculas(texto: str) -> bool:
    return any(c.islower() for c in texto)


def linhas_da_capa(pagina) -> list[str]:
    """As linhas da primeira página, na ordem em que aparecem em cada coluna."""
    blocos = []
    for bl in pagina.get_text("rawdict")["blocks"]:
        if "lines" not in bl:
            continue
        for ln in bl["lines"]:
            chars = [(c, sp["size"]) for sp in ln["spans"] for c in sp["chars"]]
            texto = texto_da_linha(chars).strip()
            if texto:
                # A coluna vem antes do y, senão a leitura pula de coluna em
                # coluna e o nome da pessoa se separa do cargo dela.
                meio = (bl["bbox"][0] + bl["bbox"][2]) / 2
                coluna = 0 if meio < 270 else (1 if meio < 510 else 2)
                blocos.append((coluna, ln["bbox"][1], texto))
    blocos.sort(key=lambda b: (b[0], b[1]))
    return [t for _, _, t in blocos]


def titulares(caminho: Path) -> list[dict]:
    documento = fitz.open(caminho)
    linhas = linhas_da_capa(documento[0])
    documento.close()

    m = DATA_DO_NOME.match(caminho.stem)
    data = m.group(1) if m else None

    achados = []
    vistos = set()
    for i, linha in enumerate(linhas[:-1]):
        if SUMARIO.search(linha) or not CARGO.match(linha):
            continue

        # O nome pode estar uma ou duas linhas abaixo, porque o cargo às vezes
        # quebra em duas ("SECRETARIA DE ESTADO DE DESENVOLVIMENTO SOCIAL E" /
        # "DIREITOS HUMANOS" / "Patrícia Cardoso Maciel Tavares").
        cargo, nome = linha, None
        for seguinte in linhas[i + 1:i + 4]:
            if SUMARIO.search(seguinte):
                break
            if tem_minusculas(seguinte) and PESSOA.match(seguinte):
                nome = seguinte
                break
            if seguinte.isupper() and len(cargo) < 90:
                cargo = f"{cargo} {seguinte}"
            else:
                break

        if not nome:
            continue
        chave = re.sub(r"\s+", " ", cargo).strip()
        if chave in vistos:
            continue
        vistos.add(chave)

        interino = "interin" in nome.lower()
        achados.append({
            "data_pub": data,
            "pasta": chave,
            "titular": re.sub(r"\s*\(?[Ii]nterin[oa]\)?\.?\s*$", "", nome).strip(),
            "interino": interino,
            "arquivo": caminho.name,
        })
    return achados


def autoteste() -> int:
    assert tem_minusculas("Ricardo Couto de Castro")
    assert not tem_minusculas("SECRETARIA DE ESTADO")

    assert CARGO.match("SECRETARIA DE ESTADO DE CIÊNCIA, TECNOLOGIA E INOVAÇÃO")
    assert CARGO.match("GOVERNADOR EM EXERCÍCIO")
    assert not CARGO.match("Antonio Claudio Lucas da Nóbrega")
    assert not CARGO.match("ATOS DO PODER EXECUTIVO")

    assert PESSOA.match("Antonio Claudio Lucas da Nóbrega")
    assert PESSOA.match("Flávio de Araújo Willeman")
    assert not PESSOA.match("Casa Civil ...........................")

    assert SUMARIO.search("Casa Civil ......................")
    assert not SUMARIO.search("Antonio Claudio Lucas da Nóbrega")

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("pdfs", nargs="*", type=Path)
    p.add_argument("--csv", type=Path, help="grava em CSV em vez de mostrar")
    p.add_argument("--json", type=Path, help="grava em JSON")
    p.add_argument("--pasta", help="filtra por trecho do nome da pasta, ex: CIÊNCIA")
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.pdfs:
        p.error("informe ao menos um PDF, ou --autoteste")

    todos = []
    for caminho in sorted(o.pdfs):
        if not caminho.exists():
            print(f"{caminho}: não existe", file=sys.stderr)
            continue
        try:
            achados = titulares(caminho)
        except Exception as e:
            print(f"{caminho.name}: FALHOU, {e}", file=sys.stderr)
            continue
        if o.pasta:
            alvo = o.pasta.upper()
            achados = [a for a in achados if alvo in a["pasta"].upper()]
        todos.extend(achados)
        print(f"{caminho.name}: {len(achados)} titulares", file=sys.stderr)

    if o.csv:
        with o.csv.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(
                f, fieldnames=["data_pub", "pasta", "titular", "interino", "arquivo"]
            )
            escritor.writeheader()
            escritor.writerows(todos)
        print(f"{o.csv}: {len(todos)} linhas")
    elif o.json:
        o.json.write_text(
            json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"{o.json}: {len(todos)} linhas")
    else:
        for a in todos:
            marca = " (interino)" if a["interino"] else ""
            print(f"  {a['data_pub']}  {a['pasta'][:58]:60} {a['titular']}{marca}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
