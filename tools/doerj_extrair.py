"""Separa o PDF do Diário em matérias, e identifica os atos numerados.

    python tools/doerj_extrair.py dados/2026/09/2026-09-22-parte-i-poder-executivo.pdf
    python tools/doerj_extrair.py dados/2026/09/*.pdf --saida extraido/
    python tools/doerj_extrair.py --autoteste

Escreve um JSONL por PDF, uma linha por matéria. Não toca no banco: carregar é
outra etapa, e separar as duas deixa reprocessar sem mexer em dado publicado.


COMO O DIÁRIO É FEITO POR DENTRO
--------------------------------

Três colunas, numa página de 822 por 1276 pontos. Os blocos de texto começam em
x ≈ 50, 295 e 535, e o agrupamento é limpo o bastante para separar por onde fica
o centro do bloco.

**Cada matéria publicada termina com `Id: 2765345`.** É o identificador da
própria Imprensa Oficial, e é o que torna a separação mecânica em vez de
adivinhada. Foram 265 matérias na edição de 22/09/2026, todos os identificadores
distintos. Guardamos esse número: ele é a chave natural da matéria e faz a
reimportação ser idempotente de graça.

As fontes dizem o papel de cada bloco:

| Fonte | O que é |
|---|---|
| `ArialMT`, `Arial-BoldMT` | o texto das matérias |
| `GalliardITCbyBT-Bold` 10pt | nome do órgão |
| `GalliardITCbyBT-Bold` 7pt | "ADMINISTRAÇÃO VINCULADA" |
| `UniversLTStd*` | o expediente do IOERJ, que não é matéria |
| `FilosofiaBold` | o cabeçalho decorativo, que sai como lixo de codificação |

As duas últimas são descartadas. Sem isso, o expediente da página 2 vaza para
dentro do primeiro decreto, o que aconteceu na primeira versão desta ferramenta.


UMA MATÉRIA NÃO É UM ATO, E ESSA É A PARTE DIFÍCIL
--------------------------------------------------

Matéria é unidade de publicação. Uma pode trazer um decreto só, outra pode trazer
sete nomeações em sequência, e outra pode não ter ato numerado nenhum.

Medido em três edições de setembro de 2026, somando 850 matérias:

- **13% a 23%** trazem ato numerado (`DECRETO Nº 50.484 DE 21 DE...`);
- o resto não traz número: "ATOS DO SECRETÁRIO", "DESPACHOS DO SECRETÁRIO",
  "RETIFICAÇÃO", e sobretudo movimentação de pessoal, que é o grosso do Diário.

Cabeçalho de ato publicado sai em caixa alta. Norma **citada** dentro do texto
sai em caixa mista: "na forma do Decreto nº 25.299, de 19/05/99". Sem essa
distinção, um decreto de 1999 mencionado de passagem virava ato publicado hoje.
Citação é assunto do `ato_relacoes`, não do `atos`.

Por isso esta ferramenta **não descarta o que não reconhece**. Toda matéria vira
uma linha, com `tipo` e `numero` preenchidos quando dá, e `reconhecido: false`
quando não dá. Quem decide se movimentação de pessoal entra no portal é a DP-05,
e essa decisão não cabe a uma ferramenta de extração.

O que é deduzido vai marcado. Ementa deduzida não é ementa publicada, e um portal
que confunde as duas afirma o que ninguém escreveu.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")


# Onde uma coluna acaba e a outra começa, numa página de 822 pontos de largura.
BORDAS = (270, 510)

# Blocos cuja fonte predominante é uma destas não são matéria: são o expediente
# do IOERJ e o cabeçalho decorativo da capa.
FONTES_FORA = ("UniversLTStd", "FilosofiaBold")

# Nome de órgão sai em Galliard 10pt, e o marcador de seção da capa em 12pt.
# A mesma fonte em 7pt é a divisória "ADMINISTRAÇÃO VINCULADA", que não é órgão.
TAMANHO_DO_ORGAO = (9.0, 13.0)

# O sumário da capa é escrito com linha pontilhada: "Casa Civil ..........".
# Nada no corpo do Diário faz isso, o que torna a linha pontilhada um sinal
# confiável de onde a capa está.
SUMARIO = re.compile(r"\.{6,}")

# O título do sumário, que só existe na capa e é o que autoriza o corte.
TITULO_DO_SUMARIO = re.compile(r"^S\s*U\s*M\s*Á\s*R\s*I\s*O\s*$", re.I)

# O que não é órgão, embora saia na mesma fonte.
NAO_E_ORGAO = re.compile(r"^(S\s*U\s*M\s*Á\s*R\s*I\s*O|www\.|ADMINISTRAÇÃO VINCULADA)", re.I)

MARCADOR = re.compile(r"Id:\s*(\d+)")

TIPOS = (
    r"DECRETO|RESOLU[ÇC][ÃA]O CONJUNTA|RESOLU[ÇC][ÃA]O|PORTARIA|DELIBERA[ÇC][ÃA]O|"
    r"INSTRU[ÇC][ÃA]O NORMATIVA|ATO NORMATIVO|ORDEM DE SERVI[ÇC]O|AVISO|EDITAL|"
    r"DECIS[ÃA]O|PROVIMENTO|CIRCULAR|COMUNICADO|CONVOCA[ÇC][ÃA]O"
)

CABECALHO = re.compile(
    r"^(?P<tipo>" + TIPOS + r")"
    r"(?P<sigla>[ /][A-ZÀ-Ü][A-ZÀ-Ü\-/\.]{1,20})?"
    r"\s*N[ºo°]?\s*(?P<numero>\d[\d\.\-/]*)"
    r"(?:[,\s]+DE\s+(?P<data>\d{1,2}\s+DE\s+[A-ZÀ-Üa-zà-ü]+\s+DE\s+\d{4}"
    r"|\d{1,2}/\d{1,2}/\d{2,4}))?",
    re.IGNORECASE,
)

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}

# Onde a ementa acaba e o ato começa a falar.
FIM_DA_EMENTA = re.compile(
    r"^\s*(O|A)\s+(GOVERNADOR|SECRET[ÁA]RI|PRESIDENTE|DIRETOR|CHEFE|MINISTR|"
    r"SUBSECRET|PROCURADOR|CONTROLADOR|CONSELHO|COMISS)",
    re.IGNORECASE,
)

NOME_DO_ARQUIVO = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+?)(?:-(\d+))?$")


def sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def juntar_hifen(texto: str) -> str:
    """'PROVI-\\nDÊNCIAS' vira 'PROVIDÊNCIAS'.

    O Diário é justificado em coluna estreita e quebra palavra o tempo todo. Sem
    isto, a busca por "providências" não acha o decreto que fala de providências.
    """
    return re.sub(r"(\w)-\n(\w)", r"\1\2", texto)


def virar_data(bruto: str | None) -> str | None:
    if not bruto:
        return None
    bruto = bruto.strip()

    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", bruto)
    if m:
        dia, mes, ano = (int(g) for g in m.groups())
        if ano < 100:
            # O Diário escreve 08/03/79 e 19/05/99. Ano de dois dígitos alto é
            # século XX: não existe decreto estadual de 2079.
            ano += 1900 if ano > 50 else 2000
        try:
            return date(ano, mes, dia).isoformat()
        except ValueError:
            return None

    m = re.match(r"^(\d{1,2})\s+DE\s+([A-Za-zÀ-Üà-ü]+)\s+DE\s+(\d{4})$", bruto, re.I)
    if m:
        dia, mes_nome, ano = m.group(1), m.group(2).lower(), m.group(3)
        mes = MESES.get(sem_acento(mes_nome), MESES.get(mes_nome))
        if mes:
            try:
                return date(int(ano), mes, int(dia)).isoformat()
            except ValueError:
                return None
    return None


def coluna(bbox) -> int:
    meio = (bbox[0] + bbox[2]) / 2
    if meio < BORDAS[0]:
        return 0
    return 1 if meio < BORDAS[1] else 2


def blocos_da_pagina(pagina) -> list[tuple[int, float, str, bool]]:
    """Os blocos de matéria, na ordem em que uma pessoa leria."""
    achados = []
    for bl in pagina.get_text("dict")["blocks"]:
        if "lines" not in bl:
            continue

        marcas = [
            (sp["font"], round(sp["size"], 1))
            for ln in bl["lines"]
            for sp in ln["spans"]
            if sp["text"].strip()
        ]
        if not marcas:
            continue
        if sum(1 for f, _ in marcas if f.startswith(FONTES_FORA)) > len(marcas) / 2:
            continue

        # O texto vem por recorte da área, e não da soma dos spans: somados, os
        # spans perdem os espaços e sai "SecretariadeEstado".
        texto = pagina.get_text("text", clip=fitz.Rect(bl["bbox"])).strip()
        if not texto:
            continue

        # Só o corpo em 10pt é nome de órgão. Em 7pt é "ADMINISTRAÇÃO VINCULADA",
        # e em 12pt é a capa, onde moram "S U M Á R I O" e "www.rj.gov.br" — que
        # viraram órgão na primeira versão desta ferramenta.
        e_orgao = any(
            f.startswith("Galliard") and TAMANHO_DO_ORGAO[0] <= t <= TAMANHO_DO_ORGAO[1]
            for f, t in marcas
        )
        achados.append((coluna(bl["bbox"]), bl["bbox"][1], bl["bbox"][3], texto, e_orgao))

    achados = cortar_capa(achados)
    achados.sort(key=lambda b: (b[0], b[1]))
    return [(c, y0, txt, org) for c, y0, _, txt, org in achados]


def cortar_capa(blocos: list[tuple]) -> list[tuple]:
    """Tira brasão, lista de secretários e sumário, quando a página é a capa.

    Os blocos chegam como `(coluna, y0, y1, texto, é_órgão)`.

    O jeito errado de fazer isto é por número de página: a capa não ocupa a
    página 1 inteira. O Diário começa a publicar atos na metade de baixo da
    mesma página em que traz o brasão e o sumário.

    Pior: o sumário fica na terceira coluna, **acima** do texto do primeiro
    decreto. Lido por coluna, ele cai no meio do decreto. Foi o que esta
    ferramenta fez até existir esta função: o registro do Decreto 50.483 vinha
    com a capa inteira dentro.

    O corte sai do próprio sumário: onde acaba a última linha pontilhada, acaba
    a capa.

    **A linha pontilhada sozinha não serve de sinal.** Resolução que altera
    outra norma cita artigo com reticências: `"Art. 7º ............"`. Usando só
    as reticências, a página 35 da edição de 18/09/2026 virou capa e cinco
    matérias reais evaporaram sem aviso nenhum. O sinal é a linha pontilhada
    **junto do título do sumário**, que só existe na capa.
    """
    if not any(b[4] and TITULO_DO_SUMARIO.match(b[3].strip()) for b in blocos):
        return blocos
    fim = max((b[2] for b in blocos if SUMARIO.search(b[3])), default=None)
    if fim is None:
        return blocos
    return [b for b in blocos if b[1] >= fim - 1]


def ler_pdf(caminho: Path) -> tuple[list[tuple[int, str, str | None]], int]:
    """Devolve (página, texto, órgão corrente) por bloco, e o total de páginas."""
    documento = fitz.open(caminho)
    saida = []
    orgao = None
    for numero, pagina in enumerate(documento, start=1):
        for _, _, texto, e_orgao in blocos_da_pagina(pagina):
            if e_orgao:
                limpo = re.sub(r"\s+", " ", texto).strip()
                if not NAO_E_ORGAO.match(limpo) and len(limpo) > 5:
                    orgao = limpo
                continue
            saida.append((numero, texto, orgao))
    total = documento.page_count
    documento.close()
    return saida, total


def em_caixa_alta(linha: str, minimo: float = 0.8) -> bool:
    letras = [c for c in linha if c.isalpha()]
    if not letras:
        return False
    return sum(1 for c in letras if c.isupper()) / len(letras) >= minimo


def achar_atos(texto: str) -> list[dict]:
    atos = []
    for linha in texto.split("\n"):
        linha = linha.strip()
        m = CABECALHO.match(linha)
        if not m:
            continue

        # Cabeçalho de ato publicado sai em caixa alta. Norma citada dentro do
        # texto sai em caixa mista: "na forma do Decreto nº 25.299, de 19/05/99".
        #
        # Sem esta conferência, um decreto de 1999 mencionado de passagem num ato
        # de pessoal virava ato publicado hoje — que foi o que aconteceu antes de
        # esta linha existir. Citação é assunto do ato_relacoes, não do atos.
        if not em_caixa_alta(linha):
            continue

        tipo = re.sub(r"\s+", " ", m.group("tipo")).title()
        atos.append({
            "tipo": tipo,
            "sigla": (m.group("sigla") or "").strip(" /") or None,
            "numero": m.group("numero").rstrip(".,"),
            "data_ato": virar_data(m.group("data")),
            "cabecalho": linha,
        })
    return atos


def achar_ementa(texto: str, cabecalho: str) -> str | None:
    """A ementa é o bloco em caixa alta logo depois do cabeçalho.

    Devolve `None` quando não há esse bloco, que é o caso da maioria dos atos de
    pessoal. `None` é resposta honesta; texto inventado não é.
    """
    linhas = [l.strip() for l in texto.split("\n")]
    try:
        inicio = linhas.index(cabecalho) + 1
    except ValueError:
        return None

    juntadas = []
    for linha in linhas[inicio:]:
        if not linha:
            if juntadas:
                break
            continue
        if FIM_DA_EMENTA.match(linha):
            break
        if not em_caixa_alta(linha):
            break
        juntadas.append(linha)
        if linha.endswith("."):
            break

    if not juntadas:
        return None
    ementa = juntar_hifen("\n".join(juntadas)).replace("\n", " ")
    ementa = re.sub(r"\s+", " ", ementa).strip()
    return ementa if len(ementa) > 12 else None


def dados_do_nome(caminho: Path) -> tuple[str | None, str | None, int]:
    m = NOME_DO_ARQUIVO.match(caminho.stem)
    if not m:
        return None, None, 1
    return m.group(1), m.group(2), int(m.group(3) or 1)


def extrair(caminho: Path) -> list[dict]:
    blocos, _ = ler_pdf(caminho)
    data_pub, caderno, sequencia = dados_do_nome(caminho)

    materias = []
    acumulado: list[str] = []
    primeira_pagina = None
    orgao_atual = None

    for pagina, texto, orgao in blocos:
        if primeira_pagina is None:
            primeira_pagina = pagina
        if orgao:
            orgao_atual = orgao

        pedaços = MARCADOR.split(texto)
        # split com grupo devolve [antes, id, depois, id, depois...]
        for i, pedaço in enumerate(pedaços):
            if i % 2 == 1:
                acumulado.append("")
                materias.append({
                    "id_ioerj": pedaço,
                    "pagina": primeira_pagina,
                    "orgao": orgao_atual,
                    "texto": "\n".join(acumulado).strip(),
                })
                acumulado = []
                primeira_pagina = pagina
            elif pedaço.strip():
                acumulado.append(pedaço.strip())

    registros = []
    for m in materias:
        texto = juntar_hifen(m["texto"])
        atos = achar_atos(texto)
        primeiro = atos[0] if atos else {}

        cabecalho = primeiro.get("cabecalho")
        ementa = achar_ementa(texto, cabecalho) if cabecalho else None

        registros.append({
            "id_ioerj": m["id_ioerj"],
            "data_pub": data_pub,
            "caderno": caderno,
            "sequencia": sequencia,
            "pagina": m["pagina"],
            "orgao": m["orgao"],
            "reconhecido": bool(atos),
            "tipo": primeiro.get("tipo"),
            "sigla": primeiro.get("sigla"),
            "numero": primeiro.get("numero"),
            "data_ato": primeiro.get("data_ato"),
            "cabecalho": cabecalho,
            "ementa": ementa,
            # Marcado porque é deduzido do bloco em caixa alta, e não de um
            # campo que o Diário publique como ementa. Ver o cabeçalho.
            "ementa_inferida": bool(ementa),
            "atos_no_texto": len(atos),
            "outros_atos": atos[1:] if len(atos) > 1 else [],
            "texto": re.sub(r"\n{3,}", "\n\n", texto).strip(),
        })
    return registros


def resumir(registros: list[dict], nome: str) -> None:
    total = len(registros)
    if not total:
        print(f"{nome}: nenhuma matéria. O PDF é do Diário mesmo?", file=sys.stderr)
        return
    com = sum(1 for r in registros if r["reconhecido"])
    atos = sum(r["atos_no_texto"] for r in registros)
    com_ementa = sum(1 for r in registros if r["ementa"])
    sem_orgao = sum(1 for r in registros if not r["orgao"])

    print(f"{nome}")
    print(f"  {total:4} matérias")
    print(f"  {com:4} com ato numerado  ({com * 100 // total}%), somando {atos} atos")
    print(f"  {total - com:4} sem número: pessoal, despacho, retificação")
    print(f"  {com_ementa:4} com ementa deduzida")
    if sem_orgao:
        print(f"  {sem_orgao:4} sem órgão identificado")


def autoteste() -> int:
    assert virar_data("21 DE SETEMBRO DE 2026") == "2026-09-21"
    assert virar_data("08/03/79") == "1979-03-08"
    assert virar_data("19/05/99") == "1999-05-19"
    assert virar_data("15/09/2026") == "2026-09-15"
    assert virar_data("30 DE FEVEREIRO DE 2026") is None, "data impossível passou"
    assert virar_data(None) is None

    assert juntar_hifen("PROVI-\nDÊNCIAS") == "PROVIDÊNCIAS"
    assert juntar_hifen("fim.\nOutra") == "fim.\nOutra"

    m = CABECALHO.match("DECRETO Nº 50.485 DE 21 DE SETEMBRO DE 2026")
    assert m and m.group("numero") == "50.485", m
    assert virar_data(m.group("data")) == "2026-09-21"

    m = CABECALHO.match("RESOLUÇÃO/SEPM Nº 9362 DE 10 DE SETEMBRO DE 2026")
    assert m and m.group("sigla").strip(" /") == "SEPM", m and m.group("sigla")
    assert m.group("numero") == "9362"

    m = CABECALHO.match("RESOLUÇÃO SECC Nº 205 DE 18 DE SETEMBRO DE 2026")
    assert m and m.group("numero") == "205"

    # Não é ato numerado, e não pode virar um.
    for nao in ("ATOS DO SECRETÁRIO", "RETIFICAÇÃO", "DESPACHOS DO SECRETÁRIO",
                "SECRETARIA DE ESTADO DE EDUCAÇÃO"):
        assert not CABECALHO.match(nao), nao

    # Norma citada dentro do texto não é ato publicado. O regex casa com ela; a
    # caixa alta é o que separa as duas.
    citada = ("Decreto nº 2479, de 08/03/79, com a nova redação dada pelo "
              "Decreto nº 25.299, de 19/05/99, o Assessor ANDRÉ DE SOUZA")
    assert CABECALHO.match(citada), "o regex mudou e o teste perdeu o sentido"
    assert achar_atos(citada) == [], achar_atos(citada)
    assert not em_caixa_alta(citada)
    assert em_caixa_alta("DECRETO Nº 50.485 DE 21 DE SETEMBRO DE 2026")
    assert achar_atos("DECRETO Nº 50.485 DE 21 DE SETEMBRO DE 2026")

    texto = (
        "DECRETO Nº 50.485 DE 21 DE SETEMBRO DE 2026\n"
        "REVOGA O DECRETO N° 45.452, DE 17 DE\nNOVEMBRO DE 2015, E DÁ OUTRAS PROVI-\nDÊNCIAS.\n"
        "O GOVERNADOR DO ESTADO DO RIO DE JANEIRO, no uso de suas atribuições"
    )
    e = achar_ementa(juntar_hifen(texto), "DECRETO Nº 50.485 DE 21 DE SETEMBRO DE 2026")
    assert e == "REVOGA O DECRETO N° 45.452, DE 17 DE NOVEMBRO DE 2015, E DÁ OUTRAS PROVIDÊNCIAS.", e

    # Sem bloco em caixa alta, a ementa é None, e não uma frase qualquer.
    sem = "PORTARIA Nº 1 DE 1 DE JANEIRO DE 2026\nO Secretário resolve nomear Fulano."
    assert achar_ementa(sem, "PORTARIA Nº 1 DE 1 DE JANEIRO DE 2026") is None

    # A capa: sumário na coluna 2, acima do texto do decreto na mesma coluna.
    # Os blocos são (coluna, y0, y1, texto, é_órgão).
    capa = [
        (0, 117, 140, "ESTA PARTE É EDITADA", False),
        (0, 642, 652, "www.rj.gov.br", True),
        (0, 692, 705, "ATOS DO PODER EXECUTIVO", True),
        (0, 710, 725, "DECRETO Nº 50.483 DE 21 DE SETEMBRO DE 2026", False),
        (2, 226, 240, "S U M Á R I O", True),
        (2, 254, 265, "Atos do Poder Executivo.........................", False),
        (2, 643, 651, "REPARTIÇÕES FEDERAIS............................", False),
        (2, 667, 690, "2º deste Decreto e publicar anualmente", False),
    ]
    ficou = {b[3] for b in cortar_capa(capa)}
    assert "ESTA PARTE É EDITADA" not in ficou, ficou
    assert "S U M Á R I O" not in ficou, ficou
    assert "Atos do Poder Executivo........................." not in ficou
    assert "DECRETO Nº 50.483 DE 21 DE SETEMBRO DE 2026" in ficou, ficou
    assert "ATOS DO PODER EXECUTIVO" in ficou, ficou
    # O texto do decreto na coluna 2 fica logo abaixo do sumário, e é o que
    # some quando o corte é feito com mão pesada.
    assert "2º deste Decreto e publicar anualmente" in ficou, ficou

    # Página comum que cita artigo com reticências não é capa, e nada se corta.
    citacao = [
        (0, 400, 420, "RESOLUÇÃO SEFAZ Nº 1 DE 1 DE JANEIRO DE 2026", False),
        (0, 558, 575, '"Art. 7º ......................................"', False),
        (0, 600, 620, "Art. 2º - Esta Resolução entra em vigor.", False),
    ]
    assert len(cortar_capa(citacao)) == 3, cortar_capa(citacao)

    assert dados_do_nome(Path("2026-09-22-parte-i-poder-executivo.pdf")) == (
        "2026-09-22", "parte-i-poder-executivo", 1)
    assert dados_do_nome(Path("2024-01-15-parte-i-poder-executivo-2.pdf")) == (
        "2024-01-15", "parte-i-poder-executivo", 2)

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("pdfs", nargs="*", type=Path)
    p.add_argument("--saida", type=Path, default=Path("extraido"))
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.pdfs:
        p.error("informe ao menos um PDF, ou --autoteste")

    o.saida.mkdir(parents=True, exist_ok=True)
    falhas = 0

    for caminho in o.pdfs:
        if not caminho.exists():
            print(f"{caminho}: não existe", file=sys.stderr)
            falhas += 1
            continue
        try:
            registros = extrair(caminho)
        except Exception as e:
            print(f"{caminho}: FALHOU, {e}", file=sys.stderr)
            falhas += 1
            continue

        destino = o.saida / f"{caminho.stem}.jsonl"
        with destino.open("w", encoding="utf-8") as f:
            for r in registros:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        resumir(registros, str(destino))

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
