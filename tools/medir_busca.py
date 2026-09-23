"""Mede o tempo das consultas que o portal faz de verdade.

    python tools/medir_busca.py
    python tools/medir_busca.py --limite 1.5   # falha acima de 1,5 s

Falha com código 1 quando alguma passa do limite.


POR QUE ISTO EXISTE

A busca por texto era `texto LIKE '%termo%'`, que não usa índice nenhum: o
MySQL lê as linhas todas, sempre. Com 1.979 matérias custava 30 ms. Com 50.062
e 152 milhões de caracteres passou a custar 4,5 segundos.

Hoje o índice `ft_texto` peneira e o `LIKE` confirma, e a mesma busca custa
pouco mais de um décimo de segundo. Este arquivo existe para que a próxima vez
que isso escorregar apareça em número, e não em reclamação de quem usa.

Medido em 2026-09-23, com 50.062 atos:

    busca por palavra       4,50 s -> 0,12 s
    busca por processo      3,81 s -> 0,13 s
    busca por ID funcional  3,54 s -> 0,02 s
    contagem sem filtro     2,20 s -> 0,01 s
"""

from __future__ import annotations

import argparse
import os
import time

import pymysql

# As consultas são as do `app/Acervo.php`, copiadas de lá.
#
# Medidor que mede consulta inventada não mede nada. Quando o Acervo mudar, este
# arquivo muda junto — e a última da lista, sem peneira, fica de propósito para
# mostrar o que o índice está economizando.
LIKE = ("(a.ementa LIKE %s OR a.cabecalho LIKE %s"
        " OR a.numero LIKE %s OR c.texto LIKE %s)")
PENEIRA = "MATCH(c.texto) AGAINST (%s IN BOOLEAN MODE)"
# Com busca de texto o Acervo entra por `ato_corpo`, para o otimizador poder
# usar o índice: por `atos` primeiro, o LEFT JOIN o obriga a varrer tudo.
DE_TEXTO = "ato_corpo c JOIN atos a ON a.id = c.ato_id"
DE = "atos a JOIN ato_corpo c ON c.ato_id = a.id"

CONSULTAS = [
    ("lista, primeira página",
     f"SELECT a.id, LEFT(c.texto, 700) FROM {DE}"
     " ORDER BY a.data_pub DESC, a.numero LIMIT 20", ()),
    ("contagem sem filtro", "SELECT COUNT(*) FROM atos a", ()),
    ("filtro de CT&I", "SELECT COUNT(*) FROM atos a WHERE a.e_cti = 1", ()),
    ("filtro por entidade",
     "SELECT COUNT(*) FROM atos a WHERE a.entidade_sistema = %s", ("faperj",)),
    ("filtro por natureza",
     "SELECT COUNT(*) FROM atos a WHERE EXISTS (SELECT 1 FROM ato_natureza n"
     " WHERE n.ato_id = a.id AND n.natureza = %s)", ("fomento",)),
    ("busca: palavra",
     f"SELECT COUNT(*) FROM {DE_TEXTO} WHERE {PENEIRA} AND {LIKE}",
     ("faperj*",) + ("%faperj%",) * 4),
    ("busca: número de processo",
     f"SELECT COUNT(*) FROM {DE_TEXTO} WHERE {PENEIRA} AND {LIKE}",
     ('"SEI-260005"',) + ("%SEI-260005%",) * 4),
    ("busca: ID funcional",
     f"SELECT COUNT(*) FROM {DE_TEXTO} WHERE {PENEIRA} AND {LIKE}",
     ("5007515*",) + ("%5007515%",) * 4),
    ("busca: a lista que vai à tela",
     f"SELECT a.id, LEFT(c.texto, 700) FROM {DE_TEXTO} WHERE {PENEIRA} AND {LIKE}"
     " ORDER BY a.data_pub DESC, a.numero LIMIT 20",
     ("faperj*",) + ("%faperj%",) * 4),
    # A última página, que a paginação numerada põe a um clique. O Acervo
    # escolhe os vinte ids só com `atos` e busca o texto depois; pedir o texto
    # junto com o OFFSET lia 50 mil textos para jogar fora, e levava 5 s.
    ("última página: escolher os ids",
     "SELECT a.id FROM atos a ORDER BY a.data_pub DESC, a.numero DESC, a.id"
     " LIMIT 20 OFFSET 50040", ()),
    ("uma ficha de ato",
     f"SELECT a.id, c.texto FROM {DE} ORDER BY a.data_pub DESC LIMIT 1", ()),
    # Fora do limite: é o caminho de termo curto demais para o índice ("nº 94",
    # "de"), que vai direto ao LIKE. Lento por definição; fica aqui para
    # mostrar o que o índice economiza no caso comum.
    ("[escape] a mesma busca sem peneira",
     f"SELECT COUNT(*) FROM {DE} WHERE {LIKE}", ("%faperj%",) * 4),
]

SEM_LIMITE = ("[escape] a mesma busca sem peneira",)


def ligar():
    return pymysql.connect(
        host=os.environ.get("DOERJ_HOST", "127.0.0.1"),
        port=int(os.environ.get("DOERJ_PORT", "3306")),
        user=os.environ.get("DOERJ_USER", "root"),
        password=os.environ.get("DOERJ_SENHA", ""),
        database=os.environ.get("DOERJ_BANCO", "doerj"),
        charset="utf8mb4",
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limite", type=float, default=2.0,
                   help="segundos acima dos quais a consulta reprova")
    a = p.parse_args()

    c = ligar()
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM atos")
        atos = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(CHAR_LENGTH(texto)), 0) FROM ato_corpo")
        letras = cur.fetchone()[0]

    print(f"{atos:,}".replace(",", ".")
          + f" atos, {letras / 1_000_000:.1f} milhões de caracteres de texto")
    print(f"limite: {a.limite:.1f} s por consulta\n")

    lentas = []
    for nome, sql, params in CONSULTAS:
        with c.cursor() as cur:
            comeco = time.perf_counter()
            cur.execute(sql, params)
            cur.fetchall()
            gasto = time.perf_counter() - comeco
        livre = nome in SEM_LIMITE
        marca = "  -  " if livre else ("ok   " if gasto <= a.limite else "LENTA")
        print(f"  {marca} {gasto:6.3f} s  {nome}")
        if gasto > a.limite and not livre:
            lentas.append((nome, gasto))
    c.close()

    print()
    if lentas:
        print(f"{len(lentas)} consulta(s) acima do limite.")
        print("Ver o cabeçalho deste arquivo e a junção em Acervo::buscar().")
        return 1
    print("todas dentro do limite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
