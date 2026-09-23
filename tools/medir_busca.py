"""Mede o tempo das consultas que o portal faz de verdade.

    python tools/medir_busca.py
    python tools/medir_busca.py --limite 1.5   # falha acima de 1,5 s

Falha com código 1 quando alguma passa do limite.


POR QUE ISTO EXISTE

A busca por texto é `texto LIKE '%termo%'`, que não usa índice nenhum: o MySQL
lê as linhas todas, sempre. Com 1.979 matérias isso não aparece. O acervo está
indo para dezenas de milhares, e o mesmo código passa a varrer centenas de
megabytes a cada tecla de quem pesquisa.

A tabela tem `FULLTEXT KEY ft_texto`, criado desde a primeira migração e nunca
usado, porque `MATCH ... AGAINST` casa palavra inteira e `LIKE` casa pedaço —
e quem procura "5007515" dentro de "ID Funcional nº 5007515-2" precisa do
pedaço. Trocar um pelo outro não é ajuste de desempenho, é mudança de
comportamento, e merece ser decidida com número na mesa em vez de no susto.

Este arquivo é o número na mesa.
"""

from __future__ import annotations

import argparse
import os
import time

import pymysql

# (nome, SQL, parâmetros) — as consultas do portal, não consultas inventadas.
CONSULTAS = [
    ("lista, primeira página",
     "SELECT a.id FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id"
     " ORDER BY a.data_pub DESC, a.numero LIMIT 20", ()),
    ("contagem total",
     "SELECT COUNT(*) FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id", ()),
    ("filtro de CT&I",
     "SELECT COUNT(*) FROM atos a WHERE a.e_cti = 1", ()),
    ("filtro por entidade",
     "SELECT COUNT(*) FROM atos a WHERE a.entidade_sistema = %s", ("faperj",)),
    ("filtro por natureza",
     "SELECT COUNT(*) FROM atos a WHERE EXISTS (SELECT 1 FROM ato_natureza n"
     " WHERE n.ato_id = a.id AND n.natureza = %s)", ("fomento",)),
    ("busca por palavra no texto",
     "SELECT COUNT(*) FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id"
     " WHERE a.ementa LIKE %s OR a.cabecalho LIKE %s OR a.numero LIKE %s"
     " OR c.texto LIKE %s", ("%faperj%",) * 4),
    ("busca por número de processo",
     "SELECT COUNT(*) FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id"
     " WHERE a.ementa LIKE %s OR a.cabecalho LIKE %s OR a.numero LIKE %s"
     " OR c.texto LIKE %s", ("%SEI-260005%",) * 4),
    ("busca por ID funcional",
     "SELECT COUNT(*) FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id"
     " WHERE a.ementa LIKE %s OR a.cabecalho LIKE %s OR a.numero LIKE %s"
     " OR c.texto LIKE %s", ("%5007515%",) * 4),
    ("uma ficha de ato",
     "SELECT a.*, c.texto FROM atos a LEFT JOIN ato_corpo c ON c.ato_id=a.id"
     " ORDER BY a.data_pub DESC LIMIT 1", ()),
]


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
        marca = "ok   " if gasto <= a.limite else "LENTA"
        print(f"  {marca} {gasto:6.3f} s  {nome}")
        if gasto > a.limite:
            lentas.append((nome, gasto))
    c.close()

    print()
    if lentas:
        print(f"{len(lentas)} consulta(s) acima do limite. A busca por texto usa")
        print("LIKE, que lê a tabela inteira: ver o cabeçalho deste arquivo.")
        return 1
    print("todas dentro do limite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
