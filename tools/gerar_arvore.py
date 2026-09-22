"""Gera `docs/arvore-de-termos.md` a partir do `vocabulario.py`.

    python tools/gerar_arvore.py

O documento é para pessoa ler — curadoria, gestão, quem for questionar por que
um ato entrou na lente. O módulo é para a máquina.

Gerar um do outro é o que impede os dois de divergirem. Documentação de
vocabulário escrita à mão descola do código na terceira alteração, e a partir
daí descreve uma ferramenta que não existe mais.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulario import (  # noqa: E402
    ANCORAS, ENTIDADES, GENERICOS, RAMOS, RUIDO,
)

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "arvore-de-termos.md"


def legivel(padrao: str) -> str:
    """Transforma a expressão regular em algo que se lê.

    Não é um conversor geral — resolve as construções que este vocabulário usa,
    e só elas. Um conversor geral seria mais código para o mesmo resultado.
    """
    t = padrao
    t = re.sub(r"\(\?:", "(", t)          # grupo sem captura vira grupo comum
    t = re.sub(r"\\s\*", " ", t)
    t = re.sub(r"\\s\+", " ", t)
    t = re.sub(r"\\s", " ", t)
    t = re.sub(r"\\b", "", t)
    t = re.sub(r"\\\.", ".", t)
    t = re.sub(r"\\w", "palavra", t)
    t = re.sub(r"\{0,\d+\}", " … ", t)     # distância máxima vira reticência
    t = re.sub(r"n\?\[[^\]]*\]\?", "nº", t)  # o "nº" com todas as variantes
    t = re.sub(r"\[[^\]]*\]", "", t)       # o resto das classes de caractere sai
    t = t.replace("|", " ou ")
    t = re.sub(r"[?*+^$]", "", t)
    t = t.replace("(", "").replace(")", "")
    t = re.sub(r"\s+", " ", t)
    # `strip` com texto remove **caracteres**, não a palavra: `.strip(" ou ")`
    # comia o "o" final de "inovacao". Daí o laço com removeprefix/removesuffix.
    t = t.strip()
    for _ in range(3):
        t = t.removeprefix(" ou ").removesuffix(" ou ").strip()
    return t


def escrever() -> int:
    linhas: list[str] = []
    p = linhas.append

    p("""# Árvore de termos de CT&I da SECTI-RJ

**Gerado de `tools/vocabulario.py` por `tools/gerar_arvore.py`.** Não edite
este arquivo à mão: mexa no módulo e gere de novo, senão os dois divergem e o
documento passa a descrever uma ferramenta que não existe mais.

A árvore não foi inventada. Sai da **Minuta do Regimento Interno da nova SECTI,
versão 16**, e da **Lei estadual nº 9.809, de 22 de julho de 2022**, que o
regimento aponta como fundamento.

Isso muda a natureza da coisa. Vocabulário montado por quem programa reflete o
que quem programa imagina que a secretaria faz. Vocabulário tirado do regimento
reflete o que ela declara fazer — e quando alguém perguntar por que determinado
ato entrou na lente, a resposta é um artigo, e não uma opinião.

**Sobre a grafia.** Os termos aparecem sem acento e às vezes pela metade —
"inovac", "tecnolog", "foruns oficia". Não é erro: a busca roda sobre o texto
normalizado, e o radical casa com todas as flexões de uma vez. "inovac" pega
inovação, inovações, inovador e inovadora; "foruns oficia" pega fórum oficial e
fóruns oficiais.

---

## Tronco: as âncoras

Nome próprio criado pela legislação de CT&I do Estado. Quem cita, está falando
do sistema — e por isso entram sozinhas, com confiança **alta**, sem depender de
mais nenhuma palavra.
""")
    for chave, padrao in ANCORAS.items():
        p(f"- **{chave}** — {legivel(padrao)}")

    p("""
## As entidades do sistema

Ato delas é do recorte, **inclusive o de pessoal**: saber quem entra e quem sai
da FAPERJ é parte de entender a pasta.

A ordem abaixo é a ordem em que são procuradas, e ela importa. Todas publicam
sob o nome da SECTI, então a secretaria vem por último — se viesse primeiro,
casaria sempre, a vinculada nunca, e a lente que dá a cada uma o seu espaço
ficaria vazia.
""")
    for chave, padrao in ENTIDADES.items():
        p(f"- **{chave}** — {legivel(padrao)}")

    p("""
---

## Os três ramos

Não são "ciência / tecnologia / inovação". São as **três subsecretarias**, que é
como a própria SECTI dividiu o assunto — e a divisão dela responde melhor: a
ciência mora no conhecimento, a inovação nos ambientes produtivos, e a
tecnologia atravessa os dois, que é como ela se comporta na prática. Um ramo só
para "tecnologia" seria artificial.
""")
    for ramo in RAMOS.values():
        p(f"\n### {ramo['nome']}\n")
        p(f"**{ramo['subsecretaria']}** · {ramo['fonte']}\n")
        for termo in ramo["termos"]:
            p(f"- {legivel(termo)}")

    p("""
---

## Termos genéricos: entram, mas marcados

Sozinhos não bastam. "Tecnologia" aparece em contrato de impressora e "inovação"
em jargão de atribuição de cargo. A matéria entra na base com confiança
**baixa**, e a tela pode escolher não mostrá-la enquanto ninguém conferir.
""")
    for termo in GENERICOS:
        p(f"- {legivel(termo)}")

    p("""
---

## O ruído: apagado antes de qualquer busca

### A palavra mais traiçoeira do vocabulário jurídico é "ciência"

Em Diário Oficial ela quer dizer **ser notificado** muito mais vezes do que quer
dizer o campo do conhecimento: "tomar ciência do débito", "após a ciência do
lançamento", "fica o contribuinte cientificado".

Medido no corpus: **51 das 63 matérias que entraram por "ciência" eram isso** —
81% de erro num termo só, arrastando junto 48 matérias da SEFAZ cancelando
inscrição estadual, que não têm nada de CT&I.

E há uma armadilha dentro da armadilha. A primeira correção incluía `de` entre
os verbos de notificação, e passou a comer o nome da própria pasta: "Secretaria
de Estado **de Ciência**, Tecnologia e Inovação" virava "Secretaria de Estado,
Tecnologia e Inovação", e 148 matérias da SECTI deixaram de ser reconhecidas
como dela.

Os dois casos estão travados em teste, em `vocabulario.py`.
""")
    for termo in RUIDO:
        p(f"- {legivel(termo)}")

    DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{DESTINO.relative_to(DESTINO.parent.parent)}: {len(linhas)} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(escrever())
