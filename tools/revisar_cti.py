"""Põe o filtro de CT&I na mesa para conferência humana, um ato por linha.

    python tools/revisar_cti.py                    # o relatório na tela
    python tools/revisar_cti.py --csv revisao.csv  # para abrir numa planilha
    python tools/revisar_cti.py --fora             # só as de fora do sistema

Para cada matéria marcada, mostra **o trecho que a trouxe**, com a expressão
casada entre `>>>` e `<<<`.


POR QUE O TRECHO, E NÃO SÓ A EMENTA

Sem o trecho não dá para conferir nada. Na auditoria de 2026-09-23, o banco
dizia "cita fatec" ou "termo de SUBINOV", e as duas coisas pareciam razoáveis —
até se ver que o "NIT" de Núcleo de Inovação Tecnológica era o Hospital da
Polícia Militar de **Nit**erói. O motivo estava certo e o resultado errado, e só
o trecho mostra a diferença.

A conferência é humana de propósito. O vocabulário sai do regimento, mas se um
termo do regimento pega a coisa errada no Diário, quem sabe é quem conhece a
pasta. Cada erro apontado aqui vira um caso no `doerj_temas.py --autoteste`, que
é como um erro conferido uma vez deixa de voltar.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pymysql

from vocabulario import ANCORAS, ENTIDADES, GENERICOS, POR_RAMO, RAMOS, limpar

LARGURA = 95


def ligar():
    return pymysql.connect(
        host=os.environ.get("DOERJ_HOST", "127.0.0.1"),
        port=int(os.environ.get("DOERJ_PORT", "3306")),
        user=os.environ.get("DOERJ_USER", "root"),
        password=os.environ.get("DOERJ_SENHA", ""),
        database=os.environ.get("DOERJ_BANCO", "doerj"),
        charset="utf8mb4",
    )


def o_que_casou(alvo: str) -> tuple[str, re.Match | None]:
    """A primeira expressão que marcou a matéria, na ordem em que o classificador
    decide: âncora, entidade, ramo, genérico."""
    for nome, padrao in ANCORAS.items():
        m = re.search(padrao, alvo, re.I)
        if m:
            return f"âncora: {nome}", m
    for nome, padrao in ENTIDADES.items():
        m = re.search(padrao, alvo, re.I)
        if m:
            return f"entidade: {nome}", m
    for chave, padrao in POR_RAMO.items():
        m = padrao.search(alvo)
        if m:
            return f"ramo: {RAMOS[chave]['subsecretaria']}", m
    for g in GENERICOS:
        m = re.search(g, alvo, re.I)
        if m:
            return "genérico", m
    return "não reproduzido", None


def trecho(alvo: str, m: re.Match | None, largura: int = LARGURA) -> str:
    if not m:
        return ""
    ini = max(0, m.start() - largura)
    return (f"…{alvo[ini:m.start()]}>>>{m.group(0)}<<<"
            f"{alvo[m.end():m.end() + largura]}…")


def coletar(so_fora: bool) -> list[dict]:
    c = ligar()
    with c.cursor() as cur:
        cur.execute(
            "SELECT a.id, a.data_pub, a.orgao, a.unidade, a.rotulo, a.tipo, a.numero,"
            " a.confianca, a.porque_cti, a.entidade_sistema, b.texto"
            " FROM atos a JOIN ato_corpo b ON b.ato_id = a.id"
            " WHERE a.e_cti"
            + (" AND (a.entidade_sistema IS NULL OR a.entidade_sistema = '')" if so_fora else "")
            + " ORDER BY a.entidade_sistema IS NULL DESC, a.confianca, a.data_pub"
        )
        linhas = cur.fetchall()
    c.close()

    saida = []
    for (ato, data, orgao, unidade, rotulo, tipo, numero, confianca, porque,
         entidade, texto) in linhas:
        alvo = limpar(texto)
        nome, m = o_que_casou(alvo)
        saida.append({
            "id": ato,
            "data": str(data),
            "onde": (unidade or orgao or "").strip(),
            "ato": f"{tipo} {numero}" if tipo and numero else (rotulo or ""),
            "confianca": confianca or "",
            "sistema": entidade or "(outra pasta)",
            "casou": nome,
            "trecho": trecho(alvo, m),
            "url": f"https://doerj.fanara.com.br/ato/{ato}",
        })
    return saida


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", help="grava numa planilha em vez da tela")
    p.add_argument("--fora", action="store_true",
                   help="só as matérias de fora do sistema SECTI")
    a = p.parse_args()

    itens = coletar(a.fora)
    if not itens:
        print("Nada marcado como CT&I. O banco está carregado?")
        return 1

    if a.csv:
        destino = Path(a.csv)
        with destino.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(itens[0]) + ["confere?", "observação"])
            w.writeheader()
            for i in itens:
                w.writerow({**i, "confere?": "", "observação": ""})
        print(f"{len(itens)} linhas em {destino}")
        print("As colunas 'confere?' e 'observação' estão em branco de propósito.")
        return 0

    print(f"{len(itens)} matérias no filtro de CT&I\n")
    atual = None
    for i in itens:
        if i["sistema"] != atual:
            atual = i["sistema"]
            print(f"\n{'=' * 78}\n{atual}\n{'=' * 78}")
        print(f"\n  {i['data']}  {i['onde'][:44]}")
        print(f"  {i['ato'][:60]}")
        print(f"  [{i['confianca']}] {i['casou']}")
        if i["trecho"]:
            print(f"     {i['trecho']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
