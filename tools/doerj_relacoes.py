"""Acha o que cada ato altera, revoga ou regulamenta.

    python tools/doerj_relacoes.py
    python tools/doerj_relacoes.py --ensaio
    python tools/doerj_relacoes.py --autoteste

Lê o que já está no banco, escreve em `ato_relacoes`. Ligação pelo ambiente,
igual ao `doerj_carregar.py`.


ISTO RESPONDE A ÚNICA PERGUNTA QUE IMPORTA
------------------------------------------

Quem procura uma norma não quer o texto: quer saber se ela ainda vale. Sem a
cadeia de alterações e revogações, o portal devolve com toda a confiança um
texto que pode estar morto há seis anos, e quem lê não tem como saber.


POR QUE ELE ACHA MENOS DO QUE PODERIA, DE PROPÓSITO
---------------------------------------------------

Nas 850 matérias das três primeiras edições, 78 mencionam alguma relação. Mas
menção não é ação, e a diferença é tudo:

    "ALTERA A PORTARIA SEDES Nº 102 DE 14 DE AGOSTO DE 2026"
        -> este ato altera aquela portaria. É relação.

    "o valor estabelecido no Anexo I do Decreto Estadual nº 50.240, alterado..."
        -> o decreto foi alterado por outra coisa, em outro momento. É contexto.

    "regulamentada pelo Decreto nº 43.510"
        -> quem regulamenta é o outro. É contexto.

Um extrator que pegue as três avisa que normas vivas foram revogadas. Num portal
de normas, esse é o pior erro possível: alguém deixa de cumprir uma regra que
vale, ou cumpre uma que não vale mais, e o erro tem a nossa assinatura.

Então aqui só entram as construções em que **o ato declara o que ele mesmo
faz**: a ementa começando pelo verbo, e as fórmulas "fica revogado" e
"revoga-se", que são performativas e não descritivas. Voz passiva e oração
adjetiva ficam de fora.

Deixar relação verdadeira escapar custa um campo vazio. Inventar relação falsa
custa a credibilidade do portal inteiro. Os dois erros não têm o mesmo peso, e o
código reflete isso.

Tudo que sai daqui entra com `origem='automatico'`. Quem conferir com o olho
muda para `'conferido'`, e o portal mostra a diferença para quem lê.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import pymysql
except ImportError:  # pragma: no cover
    sys.exit("Falta o PyMySQL. Instale com: pip install pymysql")


TIPOS = (
    r"DECRETO[- ]LEI|DECRETO|LEI COMPLEMENTAR|LEI|RESOLU[ÇC][ÃA]O CONJUNTA|"
    r"RESOLU[ÇC][ÃA]O|PORTARIA|DELIBERA[ÇC][ÃA]O|INSTRU[ÇC][ÃA]O NORMATIVA|"
    r"ATO NORMATIVO|ORDEM DE SERVI[ÇC]O|PROVIMENTO"
)

# A sigla do órgão vem em caixa alta e pode ter mais de uma palavra:
# "PORTARIA DER SEI Nº 136", "RESOLUÇÃO CONJUNTA SES/SMS RJ Nº 56". Preposição
# e conjunção ficam de fora, senão "PORTARIA DE 17 DE SETEMBRO" vira sigla.
PALAVRA_DA_SIGLA = r"(?!DE\b|DA\b|DO\b|DAS\b|DOS\b|E\b|EM\b|QUE\b|N[ºo°])[A-ZÀ-Ü][A-ZÀ-Ü\-/\.]{1,20}"

# "Decreto Estadual nº 50.240, de 20 de março de 2026"
# "Portaria SEFAZ/SUPCC nº 1005 de 13 de abril de 2026"
# "Resolução SEFAZ nº 182/2017"  ·  "Portaria SESP/SUBEXEC N.º 31"
NORMA = (
    r"(?P<tipo>" + TIPOS + r")"
    r"(?:\s+(?:ESTADUAL|FEDERAL))?"
    r"(?P<sigla>(?:\s+" + PALAVRA_DA_SIGLA + r"){0,3})"
    r"[,\s]*N\.?[ºo°]?\s*(?P<numero>\d[\d\.]*)"
    r"(?:\s*/\s*(?P<ano_barra>\d{4}))?"
    r"(?:[,\s]+DE\s+(?P<data>\d{1,2}\s+DE\s+[A-ZÀ-Üa-zà-ü]+\s+DE\s+(?P<ano_data>\d{4})"
    r"|\d{1,2}/\d{1,2}/(?P<ano_curto>\d{2,4})))?"
)

# Entre o verbo e a norma cabe pouca coisa, e cada uma dessas foi vista no
# Diário: ", EM PARTE,", "O ART. 1º DA", "DISPOSITIVOS DO".
ARTIGO = r"(?:[OA]S?|D[OA]S?)"

# `dispositivo` diz se o ato atinge um artigo, e não a norma inteira. Revogar o
# art. 2º de uma resolução não revoga a resolução, e confundir as duas faria o
# portal declarar morta uma norma viva. Ver `003-relacao-parcial.sql`.
ENTRE = (
    r"(?:[,\s]+(?:EM PARTE|PARCIALMENTE|EM SUA TOTALIDADE))?"
    r"[,\s]+(?:" + ARTIGO + r"\s+)?"
    r"(?:(?P<dispositivo>ART(?:IGO)?S?\.?\s*[\dºo°,\s]{1,20}|DISPOSITIVOS?|INCISOS?|ANEXOS?)"
    r"\s+D[AEO]S?\s+(?:" + ARTIGO + r"\s+)?)?"
)

# O Diário às vezes emenda a data do ato na frente da ementa.
DATA_COLADA = r"(?:DE\s+\d{1,2}\s+DE\s+[A-ZÀ-Üa-zà-ü]+\s+DE\s+\d{4}\s+)?"

# As construções em que o ato fala do que ele próprio faz.
DECLARACOES = [
    # "ALTERA A RESOLUÇÃO SEFAZ Nº 182/2017, QUE..."
    ("ementa", re.compile(
        r"^\s*" + DATA_COLADA +
        r"(?P<verbo>ALTERA|REVOGA|REGULAMENTA|RETIFICA|REPUBLICA)[MR]?"
        r"(?:[- ]SE)?" + ENTRE + NORMA, re.I)),

    # "DISPÕE SOBRE A ALTERAÇÃO DA RESOLUÇÃO SECC Nº 163 DE 12 DE AGOSTO DE 2025"
    ("ementa", re.compile(
        r"^\s*" + DATA_COLADA +
        r"DISP[ÕO]E\s+SOBRE\s+A\s+(?P<verbo>ALTERA|REVOGA|RETIFICA|REPUBLICA)[ÇC][ÃA]O"
        + ENTRE + NORMA, re.I)),

    # "Art. 1º - Fica revogado o Decreto n° 45.452, de 17 de novembro de 2015"
    ("artigo", re.compile(
        r"\bFICA(?:M)?\s+(?P<verbo>REVOGAD|ALTERAD|RETIFICAD|REPUBLICAD)[OA]S?"
        + ENTRE + NORMA, re.I)),

    # "Revoga-se a Portaria SEFAZ/SUPCC nº 1005 de 13 de abril de 2026"
    ("artigo", re.compile(
        r"\b(?P<verbo>REVOGA|ALTERA|RETIFICA|REPUBLICA)[- ]SE" + ENTRE + NORMA, re.I)),
]

# Depois de "QUE" ou "PARA" a ementa passa a descrever a norma alvo, e não o que
# este ato faz: "ALTERA A RESOLUÇÃO Nº 182, QUE REGULAMENTA A LEI Nº 7.000".
# A Lei 7.000 não é alterada por ninguém aqui.
FIM_DA_ACAO = re.compile(r"\b(QUE|PARA|NA FORMA|CONFORME|DISPONDO)\b", re.I)

# Uma ementa pode ter dois alvos: "ALTERA A PORTARIA DER SEI Nº 136, DE 26 DE
# FEVEREIRO DE 2026, E A PORTARIA DER SEI Nº 140".
ALVO_EXTRA = re.compile(r"[,\s]+E\s+(?:" + ARTIGO + r"\s+)?" + NORMA, re.I)

RELACAO_DO_VERBO = {
    "ALTERA": "Altera", "ALTERAD": "Altera",
    "REVOGA": "Revoga", "REVOGAD": "Revoga",
    "RETIFICA": "Retifica", "RETIFICAD": "Retifica",
    "REPUBLICA": "Republica", "REPUBLICAD": "Republica",
    "REGULAMENTA": "Regulamenta",
}

# Tipo que o Estado não publica no seu Diário: a relação aponta para fora.
EXTERNOS = ("LEI COMPLEMENTAR", "LEI", "DECRETO-LEI", "DECRETO LEI")


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


def normalizar_numero(bruto: str) -> str:
    """'50.485' e '50485' são o mesmo número, e têm que casar na busca."""
    return bruto.replace(".", "").lstrip("0") or "0"


def achar(ementa: str | None, texto: str | None) -> list[dict]:
    """As relações declaradas. Ver o cabeçalho para o que fica de fora."""
    achados: list[dict] = []
    vistos: set[tuple] = set()

    fontes = []
    if ementa:
        fontes.append(("ementa", re.sub(r"\s+", " ", ementa)))
    if texto:
        fontes.append(("artigo", re.sub(r"\s+", " ", texto)))

    for onde, padrao in DECLARACOES:
        for origem, conteudo in fontes:
            if origem != onde:
                continue
            for m in padrao.finditer(conteudo):
                verbo = m.group("verbo").upper()
                relacao = RELACAO_DO_VERBO.get(verbo)
                if not relacao:
                    continue

                # Um artigo da norma, ou a norma inteira? A diferença decide
                # se o alvo continua valendo.
                dispositivo = (m.groupdict().get("dispositivo") or "").strip(" ,")
                alvos = [m]

                # Um segundo alvo ligado por "e", mas só antes de "que": depois
                # do "que" a ementa descreve a norma alvo em vez de agir sobre
                # ela, e o que vem ali não é alterado por este ato.
                resto = conteudo[m.end():]
                corte = FIM_DA_ACAO.search(resto)
                if corte:
                    resto = resto[:corte.start()]
                extra = ALVO_EXTRA.match(resto)
                while extra:
                    alvos.append(extra)
                    resto = resto[extra.end():]
                    extra = ALVO_EXTRA.match(resto)

                for alvo in alvos:
                    tipo = re.sub(r"\s+", " ", alvo.group("tipo")).upper()
                    numero = alvo.group("numero").rstrip(".")
                    sigla = re.sub(r"\s+", " ", alvo.group("sigla") or "").strip()
                    ano = (alvo.group("ano_barra") or alvo.group("ano_data")
                           or alvo.group("ano_curto"))

                    chave = (relacao, tipo, normalizar_numero(numero))
                    if chave in vistos:
                        continue
                    vistos.add(chave)

                    rotulo = " ".join(
                        x for x in (tipo.title(), sigla, f"nº {numero}") if x
                    )
                    if ano:
                        rotulo += f"/{ano}"

                    achados.append({
                        "tipo_relacao": relacao,
                        "tipo_alvo": tipo,
                        "numero_alvo": numero,
                        "ano_alvo": int(ano) if ano and len(ano) == 4 else None,
                        "texto": rotulo[:200],
                        "externo": 1 if tipo in EXTERNOS else 0,
                        "parcial": 1 if dispositivo else 0,
                        "dispositivo": re.sub(r"\s+", " ", dispositivo)[:60] or None,
                        "trecho": alvo.group(0)[:255],
                    })
    return achados


def resolver(cursor, rel: dict) -> str | None:
    """O alvo já está no nosso acervo? Quase nunca está, e tudo bem."""
    if rel["externo"]:
        return None
    cursor.execute(
        "SELECT id FROM atos WHERE UPPER(tipo)=%s"
        " AND REPLACE(numero,'.','')=%s"
        + (" AND ano=%s" if rel["ano_alvo"] else "")
        + " LIMIT 2",
        (rel["tipo_alvo"].title().upper(), rel["numero_alvo"].replace(".", ""))
        + ((rel["ano_alvo"],) if rel["ano_alvo"] else ()),
    )
    achados = cursor.fetchall()
    # Dois candidatos é ambiguidade, e ambiguidade resolvida na sorte é pior que
    # ambiguidade declarada: fica nulo, e a curadoria decide.
    return achados[0][0] if len(achados) == 1 else None


def processar(ensaio: bool) -> tuple[int, int, int]:
    ligacao = ligar()
    gravadas = resolvidas = 0
    atos_com = 0
    try:
        with ligacao.cursor() as c:
            c.execute(
                "SELECT a.id, a.ementa, p.texto FROM atos a"
                " LEFT JOIN ato_corpo p ON p.ato_id = a.id"
            )
            linhas = c.fetchall()

            if not ensaio:
                c.execute("DELETE FROM ato_relacoes WHERE origem = 'automatico'")

            for ato_id, ementa, texto in linhas:
                relacoes = achar(ementa, texto)
                if not relacoes:
                    continue
                atos_com += 1
                for r in relacoes:
                    destino = resolver(c, r)
                    if destino:
                        resolvidas += 1
                    if ensaio:
                        marca = f" (só {r['dispositivo']})" if r["parcial"] else ""
                        print(f"  {ato_id[:44]:46} {r['tipo_relacao']:12} "
                              f"{(r['texto'][:36] + marca)[:52]:54} {destino or '—'}")
                    else:
                        c.execute(
                            "INSERT INTO ato_relacoes (ato_id, tipo_relacao,"
                            " ato_destino_texto, ato_destino_id, externo, parcial,"
                            " dispositivo, origem, detalhes)"
                            " VALUES (%s,%s,%s,%s,%s,%s,%s,'automatico',%s)",
                            (ato_id, r["tipo_relacao"], r["texto"], destino,
                             r["externo"], r["parcial"], r["dispositivo"],
                             r["trecho"]),
                        )
                    gravadas += 1

        if ensaio:
            ligacao.rollback()
        else:
            ligacao.commit()
    except Exception:
        ligacao.rollback()
        raise
    finally:
        ligacao.close()
    return gravadas, resolvidas, atos_com


def autoteste() -> int:
    # --- o que TEM que ser achado ---
    r = achar("REVOGA O DECRETO N° 45.452, DE 17 DE NOVEMBRO DE 2015, E DÁ OUTRAS PROVIDÊNCIAS.", None)
    assert len(r) == 1, r
    assert r[0]["tipo_relacao"] == "Revoga"
    assert r[0]["numero_alvo"] == "45.452", r[0]
    assert r[0]["ano_alvo"] == 2015, r[0]
    assert r[0]["externo"] == 0

    r = achar("ALTERA A RESOLUÇÃO SEFAZ Nº 182/2017, QUE REGULAMENTA A LEI Nº 7.000", None)
    assert r[0]["tipo_relacao"] == "Altera" and r[0]["numero_alvo"] == "182", r[0]
    assert r[0]["ano_alvo"] == 2017, r[0]

    r = achar("REGULAMENTA A LEI Nº 11.236, DE 22 DE JUNHO DE 2026", None)
    assert r[0]["tipo_relacao"] == "Regulamenta"
    # Lei é do Legislativo: a relação aponta para fora do nosso acervo.
    assert r[0]["externo"] == 1, r[0]

    r = achar(None, "Art. 1º - Fica revogado o Decreto n° 45.452, de 17 de novembro de 2015.")
    assert r and r[0]["tipo_relacao"] == "Revoga" and r[0]["numero_alvo"] == "45.452", r
    assert r[0]["parcial"] == 0, "revogação da norma inteira virou parcial"

    # --- a distinção que impede o portal de matar norma viva ---
    #
    # Caso real: a Resolução SES/SMS 4.281 altera o art. 1º e revoga o art. 2º
    # da Resolução Conjunta 564/2018. A 564 continua em vigor, e um portal que
    # leia só "Revoga" diz a quem consulta que ela morreu.
    r = achar(None,
              "Fica alterado o art. 1º da Resolução Conjunta SES/SMS/RJ nº 564, "
              "de 17 de outubro de 2018, que passa a vigorar. "
              "Fica revogado o art. 2º da Resolução Conjunta SES/SMS/RJ nº 564, "
              "de 17 de outubro de 2018.")
    assert len(r) == 2, r
    assert {x["tipo_relacao"] for x in r} == {"Altera", "Revoga"}, r
    assert all(x["parcial"] == 1 for x in r), r
    assert all(x["numero_alvo"] == "564" for x in r), r
    revoga = next(x for x in r if x["tipo_relacao"] == "Revoga")
    assert "2" in (revoga["dispositivo"] or ""), revoga

    r = achar(None, "Revoga-se a Portaria SEFAZ/SUPCC nº 1005 de 13 de abril de 2026.")
    assert r and r[0]["tipo_relacao"] == "Revoga" and r[0]["numero_alvo"] == "1005", r

    # --- o que NÃO PODE ser achado, e é o ponto desta ferramenta ---
    assert achar(None, "o valor estabelecido no Anexo I do Decreto Estadual nº 50.240, "
                       "alterado pela Portaria nº 3") == [], "voz passiva virou relação"
    assert achar(None, "a matéria regulamentada pelo Decreto nº 43.510 dispõe") == [], \
        "oração adjetiva virou relação"
    assert achar(None, "revogadas as disposições em contrário") == [], \
        "fórmula de estilo sem alvo virou relação"
    assert achar(None, "nos termos do Decreto nº 2479, de 08/03/79") == [], \
        "simples citação virou relação"
    assert achar(None, "revogando a Portaria LOTERJ/GP nº 743") == [], \
        "gerúndio descritivo virou relação"

    # Repetição no mesmo ato não vira duas linhas.
    r = achar("REVOGA O DECRETO Nº 45.452",
              "Fica revogado o Decreto nº 45452. Revoga-se o Decreto n° 45.452.")
    assert len(r) == 1, r

    # --- as cinco construções que escapavam, achadas no Diário de verdade ---
    r = achar("ALTERA O ART. 1º DA PORTARIA SECC/DGF Nº 44 DE 2 DE MARÇO DE 2026", None)
    assert r and r[0]["numero_alvo"] == "44", r

    r = achar("ALTERA, EM PARTE, A PORTARIA FUNARJ SEI Nº 1432, DE 13 DE JULHO DE 2026", None)
    assert r and r[0]["numero_alvo"] == "1432", r

    # Sigla de duas palavras: "PORTARIA DER SEI Nº 136".
    r = achar("ALTERA A PORTARIA DER SEI Nº 136, DE 26 DE FEVEREIRO DE 2026, "
              "E A PORTARIA DER SEI Nº 140, DE 18 DE MARÇO DE 2026", None)
    assert len(r) == 2, r
    assert {x["numero_alvo"] for x in r} == {"136", "140"}, r

    r = achar("DE 17 DE SETEMBRO DE 2026 ALTERA A PORTARIA SESP/SUBEXEC N.º 31 "
              "DE 15 DE DEZEMBRO DE 2025", None)
    assert r and r[0]["numero_alvo"] == "31", r

    r = achar("DISPÕE SOBRE A ALTERAÇÃO DA RESOLUÇÃO SECC Nº 163 DE 12 DE AGOSTO DE 2025", None)
    assert r and r[0]["tipo_relacao"] == "Altera" and r[0]["numero_alvo"] == "163", r

    # O que vem depois de "QUE" descreve o alvo, e não é alterado por este ato.
    r = achar("ALTERA A RESOLUÇÃO SEFAZ Nº 182/2017, QUE REGULAMENTA A LEI Nº 7.000 "
              "E A LEI Nº 2.657", None)
    assert len(r) == 1 and r[0]["numero_alvo"] == "182", r

    # Alterar coisa que não é norma continua não sendo relação.
    for nao in ("ALTERA O AUXÍLIO-ADOÇÃO NA FORMA QUE MENCIONA.",
                "ALTERA A LOTAÇÃO DO PROCURADOR DO ESTADO QUE MENCIONA.",
                "ALTERA DISPOSITIVOS DO DECRETO"):
        assert achar(nao, None) == [], (nao, achar(nao, None))

    assert normalizar_numero("50.485") == normalizar_numero("50485") == "50485"
    assert normalizar_numero("0012") == "12"

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--ensaio", action="store_true",
                   help="mostra o que faria, sem gravar nada")
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()

    gravadas, resolvidas, atos = processar(o.ensaio)
    verbo = "achadas" if o.ensaio else "gravadas"
    print()
    print(f"{gravadas} relações {verbo}, em {atos} atos")
    print(f"{resolvidas} apontam para ato que já está no acervo")
    print(f"{gravadas - resolvidas} ficam em prosa, à espera da curadoria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
