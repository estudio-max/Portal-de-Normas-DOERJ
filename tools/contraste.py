"""Confere o contraste das combinações de cor que a tela usa de verdade.

    python tools/contraste.py

Lê os tokens do `public/assets/css/base.css` e mede cada par contra a WCAG 2.1.
Falha com código de saída 1 quando algum par reprova.


POR QUE ISTO É UM TESTE, E NÃO UMA CONFERÊNCIA DE UMA VEZ

Contraste é o tipo de coisa que passa no dia em que se escreve e quebra seis
meses depois, quando alguém clareia um token "só um pouquinho" para a tela ficar
mais leve. Ninguém percebe, porque quem escolhe a cor costuma enxergar bem.

Num serviço público isso não é detalhe de gosto: é a diferença entre a pessoa
conseguir ler o que o Estado decidiu sobre ela, ou não.

O mínimo da WCAG 2.1 AA é 4,5:1 para texto normal e 3:1 para texto grande e para
elemento de interface. Aqui os pares vão com o mínimo que cada um precisa, e não
com um número só para todos.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parent.parent / "public" / "assets" / "css" / "base.css"

# (frente, fundo, mínimo exigido, onde aparece)
#
# Cor escrita à mão no par é cor que está escrita à mão no CSS também: o
# cabeçalho e o rodapé usam alguns cinzas literais, e eles precisam ser medidos
# como os tokens.
PARES = [
    ("--tinta", "--fundo", 4.5, "texto da página"),
    ("--tinta", "--superficie", 4.5, "texto sobre cartão"),
    ("--tinta", "--superficie-2", 4.5, "texto sobre cabeçalho de tabela"),
    ("--tinta-suave", "--fundo", 4.5, "texto secundário"),
    ("--acento", "--fundo", 4.5, "link no corpo"),
    ("--acento", "--superficie", 4.5, "link sobre cartão"),
    ("--ressalva-tinta", "--ressalva-fundo", 4.5, "texto da ressalva"),
    ("--perigo", "--fundo", 4.5, "texto de erro"),
    ("--alerta", "--fundo", 4.5, "texto de alerta"),
    ("#ffffff", "--noite", 4.5, "título no cabeçalho"),
    ("#dfe8ea", "--noite", 4.5, "links do menu"),
    ("#9fb4bb", "--noite", 4.5, "subtítulo do cabeçalho"),
    ("#c4d2d6", "--noite", 4.5, "texto do rodapé"),
    ("--realce", "--noite", 4.5, "item ativo do menu"),
    ("--acento-no-escuro", "--noite", 4.5, "link no rodapé"),
    ("--borda-forte", "--fundo", 3.0, "borda tracejada"),
    ("--foco", "--fundo", 3.0, "anel de foco"),
    ("--foco", "--superficie", 3.0, "anel de foco sobre cartão"),
    # Os selos de vigência: a cor diz tanto quanto a palavra, e as duas
    # precisam ser legíveis.
    ("#146245", "#e6f4ee", 4.5, "selo Vigente"),
    ("--ressalva-tinta", "--ressalva-fundo", 4.5, "selo Alterado"),
    ("--perigo", "#fbecea", 4.5, "selo Revogado"),
    ("--tinta-suave", "--superficie", 4.5, "órgão na tabela"),
    ("--tinta-suave", "--superficie-2", 4.5, "órgão na linha sob o cursor"),
    # A lista no desenho da UFF, de 2026-09-23.
    ("#ffffff", "--acento", 4.5, "botão Buscar e página atual"),
    ("--noite", "--acento-claro", 4.5, "etiqueta de filtro"),
    ("--tinta", "--acento-claro", 4.5, "Mais filtros aberto"),
    ("--acento", "--superficie-2", 4.5, "processo na linha sob o cursor"),
]


def tokens(css: str) -> dict[str, str]:
    raiz = re.search(r":root\s*\{(.*?)\}", css, re.S)
    if not raiz:
        raise SystemExit("Não achei o bloco :root no CSS.")
    return {
        m.group(1): m.group(2).strip()
        for m in re.finditer(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;", raiz.group(1))
    }


def rgb(cor: str) -> tuple[int, int, int]:
    c = cor.lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def luminancia(cor: str) -> float:
    def canal(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = rgb(cor)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(frente: str, fundo: str) -> float:
    a, b = luminancia(frente), luminancia(fundo)
    claro, escuro = max(a, b), min(a, b)
    return (claro + 0.05) / (escuro + 0.05)


def main() -> int:
    if not CSS.exists():
        raise SystemExit(f"{CSS} não existe.")
    achados = tokens(CSS.read_text(encoding="utf-8"))

    def cor(nome: str) -> str:
        if nome.startswith("#"):
            return nome
        if nome not in achados:
            raise SystemExit(f"O token {nome} não está no :root do CSS.")
        return achados[nome]

    reprovados = []
    print(f"{len(PARES)} pares, contra a WCAG 2.1 AA\n")
    for frente, fundo, minimo, onde in PARES:
        razao = contraste(cor(frente), cor(fundo))
        passa = razao >= minimo
        marca = "ok  " if passa else "FALHA"
        print(f"  {marca} {razao:5.2f}:1  (mín {minimo})  {onde}")
        if not passa:
            reprovados.append((onde, frente, fundo, razao, minimo))

    print()
    if reprovados:
        print(f"{len(reprovados)} par(es) abaixo do mínimo:", file=sys.stderr)
        for onde, f, b, r, m in reprovados:
            print(f"  {onde}: {f} sobre {b} dá {r:.2f}:1, precisa de {m}", file=sys.stderr)
        return 1

    print("todos passam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
