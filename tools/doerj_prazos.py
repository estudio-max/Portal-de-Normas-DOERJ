"""Lê o prazo de cada instrumento publicado em extrato, e grava em `ato_prazo`.

    python tools/doerj_prazos.py              # a SECTI, as vinculadas e o recorte de CT&I
    python tools/doerj_prazos.py --autoteste

Ligação pelo ambiente, como o `doerj_carregar.py` (DOERJ_HOST, DOERJ_PORT...).


POR QUE ISTO EXISTE

Pedido do João em 2026-09-23: acordos e metas da SECTI têm data, a gestão atual
pode não saber o que foi combinado antes dela, e perder o prazo. O Diário publica
o extrato de cada contrato, convênio e termo aditivo com a vigência. É a única
fonte pública que diz, de cada compromisso, quando ele acaba.


COMO O PRAZO VEM, e em que ordem é lido

Um extrato é uma fila de campos em caixa alta: INSTRUMENTO, PARTES, OBJETO,
PRAZO ou VIGÊNCIA, VALOR, DATA DA ASSINATURA. Uma mesma matéria empilha vários
instrumentos, e cada um vira uma linha.

O fim sai da primeira destas que der certo:

1. Datas explícitas — "de 14/03/2026 a 14/09/2026", "a partir de 6 de setembro
   de 2026 até 5 de setembro de 2027". É o caso mais confiável: o próprio
   extrato fez a conta.
2. Duração somada a um início — "12 (doze) meses", "5 anos". O início é o que o
   texto disser ("a contar de 18/05/2026", "a contar da publicação", "da
   assinatura"); se não disser, a data da assinatura; se não houver, a da
   publicação. O campo `como` guarda qual foi, porque "início presumido" é menos
   firme que "a contar de 18/05/2026", e quem lê o painel precisa saber.

Somar meses mantém o dia: 12 meses a partir de 14/03/2026 terminam em
14/03/2027. É a convenção que os próprios extratos usam — o aditivo da UERJ diz
"prorrogado por mais 6 meses [...] de 14/03/2026 a 14/09/2026".


O QUE FICA DE FORA, e é honesto dizer

A quebra de coluna às vezes enfia outro campo no meio do prazo — "VIGÊNCIA: 5
FUNDAMENTO DE ATO: (cinco) anos". Aí a duração se perde e o instrumento não entra.
É melhor faltar um prazo do que inventar um.
"""

from __future__ import annotations

import argparse
import calendar
import os
import re
import sys
from datetime import date, timedelta

MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5,
    "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}
_NOMES = "|".join(MESES)
DATA_NUM = r"(\d{1,2})[./-](\d{1,2})[./-](\d{4}|\d{2})\b"
DATA_EXT = r"(\d{1,2})[ºo°]?\s+de\s+(" + _NOMES + r")\s+de\s+(\d{4})"
DATA = re.compile(DATA_NUM + "|" + DATA_EXT, re.I)

# Um intervalo: "de D1 a D2", "D1 até D2", "a partir de D1 até D2".
INTERVALO = re.compile(
    r"(" + DATA_NUM + "|" + DATA_EXT + r")\s*(?:a|at[ée]|e)\s+(?:o dia\s+)?(" + DATA_NUM + "|" + DATA_EXT + r")",
    re.I,
)
DURACAO = re.compile(
    r"(\d{1,3})\s*(?:\([^)]{2,40}\))?\s*(meses|m[êe]s|anos?|dias)\b", re.I
)
INICIO_CITADO = re.compile(
    r"(?:a\s+contar\s+de|a\s+partir\s+de|contados?\s+(?:a\s+partir\s+)?de)\s+(" + DATA_NUM + "|" + DATA_EXT + ")",
    re.I,
)

# Um rótulo de campo: palavras em caixa alta seguidas de dois-pontos. É o que
# separa um campo do seguinte no extrato.
ROTULO = re.compile(r"\*?\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{2,40}?)\s*:")
INICIO_DE_INSTRUMENTO = re.compile(r"\*?\bINSTRUMENTO\s*:", re.I)
PROCESSO = re.compile(r"\b(SEI[- ]?\d{6}/\d{6}/\d{4}|E-\d{2}/\d{3}/\d{1,7}/\d{4})", re.I)


def para_data(g: tuple) -> date | None:
    """Os seis grupos de DATA (três numéricos, três por extenso) viram data."""
    d1, m1, a1, d2, m2, a2 = g
    try:
        if d1:
            ano = int(a1) + (2000 if len(a1) == 2 else 0)
            return date(ano, int(m1), int(d1))
        if d2:
            return date(int(a2), MESES[m2.lower()], int(d2))
    except (ValueError, KeyError):
        return None
    return None


def primeira_data(txt: str) -> date | None:
    m = DATA.search(txt or "")
    return para_data(m.groups()) if m else None


def somar(inicio: date, n: int, unidade: str) -> date:
    u = unidade.lower()
    if u.startswith("dia"):
        return inicio + timedelta(days=n)
    meses = n * 12 if u.startswith("ano") else n
    total = inicio.month - 1 + meses
    ano, mes = inicio.year + total // 12, total % 12 + 1
    return date(ano, mes, min(inicio.day, calendar.monthrange(ano, mes)[1]))


def campos(bloco: str) -> dict[str, str]:
    """Os campos do extrato, pelo rótulo em caixa alta. O primeiro vence."""
    marcas = list(ROTULO.finditer(bloco))
    saida: dict[str, str] = {}
    for i, m in enumerate(marcas):
        nome = " ".join(m.group(1).split())
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(bloco)
        saida.setdefault(nome, bloco[m.end():fim].strip(" .;"))
    return saida


def blocos(texto: str) -> list[str]:
    """Cada instrumento da matéria, do seu "INSTRUMENTO:" até o próximo."""
    t = " ".join(texto.split())
    marcas = [m.start() for m in INICIO_DE_INSTRUMENTO.finditer(t)]
    return [t[a:b] for a, b in zip(marcas, marcas[1:] + [len(t)])]


def ler(bloco: str, data_pub: date) -> dict | None:
    c = campos(bloco)
    pega = lambda *nomes: next((c[n] for n in nomes if n in c), "")  # noqa: E731
    prazo = pega("PRAZO", "VIGÊNCIA", "VIGENCIA", "PRAZO DE VIGÊNCIA", "PRAZO DE VIGENCIA")
    objeto = pega("OBJETO")
    assinatura = primeira_data(pega("DATA DA ASSINATURA", "DATA DE ASSINATURA", "ASSINATURA"))
    registro = {
        "instrumento": pega("INSTRUMENTO")[:300] or None,
        "partes": pega("PARTES")[:500] or None,
        "objeto": objeto[:700] or None,
        "valor": pega("VALOR", "VALOR TOTAL", "VALOR GLOBAL")[:160] or None,
        "processo": (PROCESSO.search(bloco).group(1) if PROCESSO.search(bloco) else None),
        "assinatura": assinatura,
    }

    # 1. Datas explícitas, no prazo ou — nos aditivos — no objeto.
    for onde in (prazo, objeto):
        m = INTERVALO.search(onde)
        if m:
            g = m.groups()
            ini, fim = para_data(g[1:7]), para_data(g[8:14])
            if ini and fim and fim > ini:
                return {**registro, "inicio": ini, "fim": fim, "como": "datas explícitas"}

    # 2. Duração somada a um início.
    for onde in (prazo, objeto if re.search(r"prorrog", objeto, re.I) else ""):
        d = DURACAO.search(onde)
        if not d:
            continue
        n, unidade = int(d.group(1)), d.group(2)
        citado = INICIO_CITADO.search(onde)
        if citado and primeira_data(citado.group(1)):
            ini, como = primeira_data(citado.group(1)), "duração a partir de data citada"
        elif re.search(r"publica", onde, re.I):
            ini, como = data_pub, "duração a partir da publicação"
        elif assinatura:
            ini, como = assinatura, "duração a partir da assinatura"
        else:
            ini, como = data_pub, "duração, início presumido na publicação"
        return {**registro, "inicio": ini, "fim": somar(ini, n, unidade), "como": como}
    return None


def ler_materia(texto: str, data_pub: date) -> list[dict]:
    saida = []
    for i, b in enumerate(blocos(texto)):
        r = ler(b, data_pub)
        if r:
            saida.append({**r, "ordem": i})
    return saida


# ----------------------------------------------------------------- banco

def ligar():
    import pymysql
    return pymysql.connect(
        host=os.environ.get("DOERJ_HOST", "127.0.0.1"),
        port=int(os.environ.get("DOERJ_PORT", "3306")),
        user=os.environ.get("DOERJ_USER", "root"),
        password=os.environ.get("DOERJ_SENHA", ""),
        database=os.environ.get("DOERJ_BANCO", "doerj"),
        charset="utf8mb4",
        autocommit=False,
    )


def gravar() -> int:
    c = ligar()
    with c.cursor() as cur:
        # Só onde o painel vai olhar: a SECTI, as vinculadas e o recorte de CT&I.
        # E só matéria que tem um "INSTRUMENTO:", que é o que marca um extrato.
        cur.execute(
            "SELECT a.id, a.data_pub, b.texto FROM atos a JOIN ato_corpo b ON b.ato_id = a.id"
            " WHERE (a.entidade_sistema IS NOT NULL OR a.e_cti = 1)"
            " AND b.texto LIKE '%%INSTRUMENTO%%'"
        )
        linhas = cur.fetchall()
        # Recalcula tudo: prazo é derivado do texto, e texto novo pode trazer
        # aditivo que muda o fim de um instrumento antigo.
        cur.execute("DELETE FROM ato_prazo")
        n = 0
        materias = 0
        for ato, data_pub, texto in linhas:
            achados = ler_materia(texto, data_pub)
            materias += bool(achados)
            for r in achados:
                cur.execute(
                    "INSERT INTO ato_prazo (ato_id, ordem, instrumento, partes, objeto, valor,"
                    " processo, assinatura, inicio, fim, como)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (ato, r["ordem"], r["instrumento"], r["partes"], r["objeto"], r["valor"],
                     r["processo"], r["assinatura"], r["inicio"], r["fim"], r["como"]),
                )
                n += 1
    c.commit()
    c.close()
    print(f"{len(linhas)} matérias com extrato; {materias} com prazo legível; {n} instrumentos gravados")
    return 0


# ------------------------------------------------------------- autoteste

def autoteste() -> int:
    pub = date(2026, 9, 22)

    # Os casos são extratos reais do acervo, de 2026.
    uerj = ("INSTRUMENTO: Termo Aditivo 06 ao Contrato 49/2023. PARTES: UERJ e ECOLD "
            "CLIMATIZAÇÃO E SERVIÇOS DE ENGENHARIA LTDA. OBJETO: Fica prorrogado por mais 6 "
            "meses o prazo de vigência e execução contratual, sendo o novo período contado de "
            "14/03/2026 a 14/09/2026. VALOR: Sem acréscimo de valores. DATA DA ASSINATURA: "
            "14/03/2026. FUNDAMENTO DO ATO: Processo nº SEI260007/039619/2022.")
    r = ler_materia(uerj, pub)
    assert len(r) == 1 and r[0]["fim"] == date(2026, 9, 14), r
    assert r[0]["como"] == "datas explícitas", r
    assert r[0]["valor"] == "Sem acréscimo de valores", r

    uenf = ("INSTRUMENTO: Convênio nº G002/2026. PARTES: Universidade Estadual do Norte "
            "Fluminense Darcy Ribeiro - UENF e FLUX ESTRUTURAS INTELIGENTES LTDA. OBJETO: "
            "Concessão de estágio. PRAZO: 05 (cinco) anos a contar da data de assinatura. "
            "DATA DA ASSINATURA: 07/01/2026. FUNDAMENTO: Processo nº SEI-260002/000116/2026.")
    r = ler_materia(uenf, pub)
    assert r and r[0]["fim"] == date(2031, 1, 7) and r[0]["como"] == "duração a partir da assinatura", r
    assert r[0]["processo"] == "SEI-260002/000116/2026", r

    # Data por extenso, com o fim escrito pelo próprio extrato.
    faperj = ("INSTRUMENTO: 2º Termo Aditivo ao Contrato nº 001/2024 PARTES: FAPERJ e FUNDAÇÃO "
              "SANTA CABRINI - FSC. OBJETO: prorrogação do prazo de vigência. PRAZO: Fica "
              "prorrogado o prazo de vigência do contrato por 12 (doze) meses, a partir de 6 de "
              "Setembro de 2026 até 5 de Setembro de 2027.")
    r = ler_materia(faperj, pub)
    assert r and r[0]["fim"] == date(2027, 9, 5) and r[0]["como"] == "datas explícitas", r

    # Duração "a contar da publicação".
    pub_txt = ("INSTRUMENTO: Contrato 14/2026. PARTES: X e Y. OBJETO: serviço. "
               "PRAZO: 14 (catorze) meses a contar da sua publicação. VALOR: R$ 1,00.")
    r = ler_materia(pub_txt, pub)
    assert r and r[0]["fim"] == date(2027, 11, 22) and r[0]["como"] == "duração a partir da publicação", r

    # Dois instrumentos na mesma matéria viram duas linhas.
    dois = ("EXTRATOS DE TERMOS INSTRUMENTO: Acordo de Cooperação. PARTES: A e B. OBJETO: x. "
            "VIGÊNCIA: 24 (vinte e quatro) meses. DATA DA ASSINATURA: 11 de março de 2026. "
            "INSTRUMENTO: Convênio 3/2026. PARTES: C e D. OBJETO: y. PRAZO: 1 ano. "
            "DATA DA ASSINATURA: 02/02/2026.")
    r = ler_materia(dois, pub)
    assert [x["fim"] for x in r] == [date(2028, 3, 11), date(2027, 2, 2)], r

    # A quebra de coluna que enfia outro campo no meio: fica de fora, não inventa.
    quebrado = ("INSTRUMENTO: Memorando de entendimento. PARTES: X e UERJ. OBJETO: cooperação. "
                "DATA DE ASSINATURA: 05/05/2026. VIGÊNCIA: 5 FUNDAMENTO DE ATO: (cinco) anos.")
    assert ler_materia(quebrado, pub) == [], ler_materia(quebrado, pub)

    # Somar meses no fim do mês não passa do último dia.
    assert somar(date(2026, 1, 31), 1, "mes") == date(2026, 2, 28)

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--autoteste", action="store_true")
    a = p.parse_args()
    return autoteste() if a.autoteste else gravar()


if __name__ == "__main__":
    raise SystemExit(main())
