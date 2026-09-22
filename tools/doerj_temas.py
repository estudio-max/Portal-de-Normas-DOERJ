"""Classifica as matérias pelo vocabulário de CT&I da própria SECTI.

    python tools/doerj_temas.py extraido/*.jsonl
    python tools/doerj_temas.py extraido/*.jsonl --amostra 12
    python tools/doerj_temas.py --autoteste

Escreve `e_cti`, `confianca` e `ramos` de volta no JSONL. Não toca no banco.


O VOCABULÁRIO NÃO É MEU

Sai do `vocabulario.py`, que por sua vez sai da Minuta do Regimento Interno da
nova SECTI e da Lei estadual nº 9.809/2022. Os três ramos são as três
subsecretarias — SUBSIS, SUBCON, SUBINOV.

A diferença é de natureza, não de qualidade: quando alguém questionar por que um
ato entrou na lente, a resposta é um artigo do regimento, e não o palpite de
quem escreveu o código.


TRÊS NÍVEIS DE CONFIANÇA, PORQUE OS SINAIS NÃO VALEM O MESMO

| Nível | Quando | Exemplo |
|---|---|---|
| `alta` | cita âncora do sistema | "nos termos da Lei nº 9.809/2022" |
| `alta` | é entidade do sistema | ato da FAPERJ, da UERJ, da FAETEC |
| `media` | termo específico de um ramo | "encomenda tecnológica", "bolsa de iniciação científica" |
| `baixa` | só termo genérico | "tecnologia", "inovação" soltos |

Âncora é nome próprio criado pela lei de CT&I do Estado: `SISTECTI-RJ`,
`CONECTI`, `FATEC`, `Polo Virtual de Inovação`. Não aparecem por acaso.

Termo genérico é o oposto. "Tecnologia" aparece em contrato de impressora e
"inovação" em jargão de atribuição de cargo. Por isso `baixa` existe: a matéria
entra na base, mas a tela pode escolher não mostrá-la sem curadoria.

**Nada disso é conferido por pessoa.** Tudo sai marcado como automático, e a
tela tem que dizer isso a quem lê.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocabulario import (  # noqa: E402
    ENTIDADE, GENERICO, POR_RAMO, RAMOS,
    limpar, qual_ancora, qual_entidade,
)


def classificar(texto: str, ementa: str | None = None, orgao: str | None = None,
                unidade: str | None = None) -> dict:
    """Devolve o recorte, a confiança, os ramos e por que entrou."""
    alvo = limpar(" ".join(x for x in (ementa, orgao, unidade, texto) if x))

    ancora = qual_ancora(alvo)
    entidade = qual_entidade(alvo)
    ramos = [chave for chave, padrao in POR_RAMO.items() if padrao.search(alvo)]

    if ancora:
        confianca, porque = "alta", f"cita {ancora}"
    elif entidade:
        confianca, porque = "alta", f"entidade do sistema: {entidade}"
    elif ramos:
        confianca, porque = "media", f"termo de {RAMOS[ramos[0]]['subsecretaria']}"
    elif GENERICO.search(alvo):
        confianca, porque = "baixa", "só termo genérico"
    else:
        return {"e_cti": False, "confianca": None, "ramos": [], "porque": None,
                "entidade": None}

    return {
        "e_cti": True,
        "confianca": confianca,
        "ramos": ramos,
        "porque": porque,
        "entidade": entidade,
    }


def processar(caminhos: list[Path], amostra: int) -> int:
    por_confianca: Counter = Counter()
    por_ramo: Counter = Counter()
    por_entidade: Counter = Counter()
    exemplos: dict[str, list] = {}
    total = 0

    for caminho in caminhos:
        linhas = [
            json.loads(x)
            for x in caminho.read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
        for r in linhas:
            res = classificar(r.get("texto") or "", r.get("ementa"),
                              r.get("orgao"), r.get("unidade"))
            r["e_cti"] = res["e_cti"]
            r["confianca"] = res["confianca"]
            r["ramos"] = res["ramos"]
            r["porque_cti"] = res["porque"]
            r["entidade_sistema"] = res["entidade"]
            # Nada aqui foi conferido por pessoa, e a tela tem que dizer isso.
            r["temas_origem"] = "automatico"

            total += 1
            if res["e_cti"]:
                por_confianca[res["confianca"]] += 1
                if res["entidade"]:
                    por_entidade[res["entidade"]] += 1
                for ramo in res["ramos"]:
                    por_ramo[ramo] += 1
                    exemplos.setdefault(ramo, []).append(r)

        with caminho.open("w", encoding="utf-8") as f:
            for r in linhas:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    de_cti = sum(por_confianca.values())
    print(f"{total} matérias, {de_cti} no recorte de CT&I ({de_cti * 100 // max(total,1)}%)\n")

    print("  por confiança")
    for nivel in ("alta", "media", "baixa"):
        print(f"    {nivel:6} {por_confianca.get(nivel, 0):4}")

    print("\n  por ramo, que são as três subsecretarias")
    for chave, ramo in RAMOS.items():
        print(f"    {ramo['subsecretaria']:8} {por_ramo.get(chave, 0):4}  {ramo['nome']}")

    if por_entidade:
        print("\n  entidades do sistema")
        for k, n in por_entidade.most_common():
            print(f"    {k:10} {n:4}")

    if amostra:
        for chave, ramo in RAMOS.items():
            itens = exemplos.get(chave, [])[:amostra]
            if not itens:
                continue
            print(f"\n  --- {ramo['nome']} ({ramo['subsecretaria']}) ---")
            for r in itens:
                rotulo = r.get("ementa") or (r.get("texto") or "")[:110]
                print(f"    [{r['confianca']}] {str(r.get('unidade') or r.get('orgao'))[:32]:34}")
                print(f"       {re.sub(r'[ \n]+', ' ', rotulo)[:104]}")
    return 0


def autoteste() -> int:
    def c(texto, ementa=None, orgao=None, unidade=None):
        return classificar(texto, ementa, orgao, unidade)

    # --- âncoras: confiança alta sem depender de palavra do vocabulário ---
    r = c("Fica instituído o comitê, nos termos da Lei nº 9.809, de 22 de julho de 2022")
    assert r["e_cti"] and r["confianca"] == "alta", r
    assert "9809" in r["porque"], r

    for ancorado in ("integrante do SISTECTI-RJ", "submetido ao CONECTI",
                     "quanto à gestão do FATEC", "manter o cadastro estadual de ICTs"):
        assert c(ancorado)["confianca"] == "alta", ancorado

    # --- entidades do sistema: pessoal entra ---
    r = c("NOMEAR FULANO para cargo em comissão",
          unidade="FUNDAÇÃO CARLOS CHAGAS FILHO DE AMPARO À PESQUISA")
    assert r["confianca"] == "alta" and r["entidade"] == "faperj", r

    # --- ramos ---
    r = c("apoio à criação de incubadoras, aceleradoras e parques tecnológicos")
    assert "inovacao" in r["ramos"], r
    r = c("concessão de bolsa de iniciação científica na pós-graduação")
    assert "conhecimento" in r["ramos"], r
    r = c("atualização da Estratégia Estadual e do mapeamento tecnológico")
    assert "governanca" in r["ramos"], r

    # Um ato pode tocar mais de um ramo, e isso é fiel ao objeto.
    r = c("transferência de tecnologia das ICTs e bolsa de extensão tecnológica")
    assert len(r["ramos"]) >= 2, r

    # --- o que tem que ficar de fora ---
    for fora in ("NOMEAR FULANO para o cargo de assistente",
                 "contrato de fornecimento de material de limpeza",
                 "para tomar ciência do débito apurado no processo",
                 "fica o contribuinte cientificado da decisão",
                 "realização de PESQUISA DE PREÇOS para aferir valores",
                 "revelar oportunidades de melhoria ou inovação em seus processos"):
        assert not c(fora)["e_cti"], fora

    # --- genérico entra, mas marcado como baixa ---
    r = c("aquisição de equipamentos de tecnologia para a repartição")
    assert r["e_cti"] and r["confianca"] == "baixa", r

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("jsonl", nargs="*", type=Path)
    p.add_argument("--amostra", type=int, default=0)
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.jsonl:
        p.error("informe ao menos um .jsonl, ou --autoteste")
    return processar(o.jsonl, o.amostra)


if __name__ == "__main__":
    raise SystemExit(main())
