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
    GENERICO, NATUREZA, POR_RAMO, RAMOS,
    dona_da_materia, limpar, quais_naturezas, qual_ancora,
)


def classificar(texto: str, ementa: str | None = None, orgao: str | None = None,
                unidade: str | None = None) -> dict:
    """Os dois eixos: o que o ato faz, e se ele é do recorte de CT&I.

    A natureza vale para **toda** matéria, e não só para as de CT&I: quem
    procura um aditivo de contrato procura do mesmo jeito dentro ou fora do
    recorte temático.
    """
    alvo = limpar(" ".join(x for x in (ementa, orgao, unidade, texto) if x))

    naturezas = quais_naturezas(alvo)
    ancora = qual_ancora(alvo)
    entidade = dona_da_materia(alvo, limpar(" ".join(x for x in (orgao, unidade) if x)))
    ramos = [chave for chave, padrao in POR_RAMO.items() if padrao.search(alvo)]

    if ancora:
        confianca, porque = "alta", f"cita {ancora}"
    elif entidade == "varias":
        confianca, porque = "alta", "cita três ou mais vinculadas"
    elif entidade:
        confianca, porque = "alta", f"entidade do sistema: {entidade}"
    elif ramos:
        confianca, porque = "media", f"termo de {RAMOS[ramos[0]]['subsecretaria']}"
    elif GENERICO.search(alvo):
        confianca, porque = "baixa", "só termo genérico"
    else:
        return {"e_cti": False, "confianca": None, "ramos": [], "porque": None,
                "entidade": None, "naturezas": naturezas}

    return {
        "e_cti": True,
        "confianca": confianca,
        "ramos": ramos,
        "porque": porque,
        "entidade": entidade,
        "naturezas": naturezas,
    }


def processar(caminhos: list[Path], amostra: int) -> int:
    por_confianca: Counter = Counter()
    por_natureza: Counter = Counter()
    sem_natureza = 0
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
            r["naturezas"] = res["naturezas"]
            # Nada aqui foi conferido por pessoa, e a tela tem que dizer isso.
            r["temas_origem"] = "automatico"

            total += 1
            for n in res["naturezas"]:
                por_natureza[n] += 1
            if not res["naturezas"]:
                sem_natureza += 1
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

    print("  natureza do ato, em todas as matérias")
    maior = max(por_natureza.values(), default=1)
    for chave, n in NATUREZA.items():
        q = por_natureza.get(chave, 0)
        print(f"    {n['nome']:26} {q:5}  {'#' * min(34, q * 34 // maior)}")
    print(f"    {'(sem categoria)':26} {sem_natureza:5}")

    print()
    print("  por confiança, só no recorte de CT&I")
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
                rotulo_linha = re.sub(r"[ \n]+", " ", rotulo)[:104]
                print(f"    [{r['confianca']}] {str(r.get('unidade') or r.get('orgao'))[:32]:34}")
                print(f"       {rotulo_linha}")
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

    # --- os seis erros que a auditoria de 2026-09-23 achou ---
    #
    # Cada um destes entrava no filtro, e juntos eram 131 das 352 matérias. O
    # motivo era sempre o mesmo: a palavra estava lá, o assunto não.
    for erro in (
        # TI corporativa. Era o maior grupo do filtro inteiro, 75 matérias.
        "SECRETARIA DE ESTADO DA CASA CIVIL CENTRO DE TECNOLOGIA DE INFORMAÇÃO"
        " E COMUNICAÇÃO DO ESTADO DO RIO DE JANEIRO EXTRATO DE TERMO ADITIVO",
        "aquisição de equipamentos de tecnologia para a repartição",
        # Laboratório de saúde e cargo de escola, 28 matérias.
        "para realização de exames laboratoriais nas Unidades de Pronto Atendimento",
        "AUXILIAR DE LABORATÓRIO DE ANÁLISES QUÍMICAS Lenice Telles de Andrade",
        # Razão social de fornecedor, 12 matérias.
        "ADJUDICO os trabalhos à empresa HEXIS CIENTÍFICA S/A, por ter oferecido",
        "RECONHEÇO A DÍVIDA, em favor da SINC DO BRASIL INSTRUMENTAÇÃO CIENTÍFICA LTDA.",
        # NIT é Niterói: o Hospital da PM se escreve HPM-NIT. Doze matérias da
        # Polícia Militar entravam como ação de inovação.
        "hpm-nit : 1o SGT PM RG 00000 marcelo dornellas designado para a escala",
        # Disciplina escolar, em lista de professores.
        "DISCIPLINA: CIÊNCIAS FÍSICAS E BIOLÓGICAS NOME MUNICIPIO TATIANA DA HORA",
        # Vínculo previdenciário.
        "total de 3641 dias de serviço prestado a entidades vinculadas ao sistema"
        " de previdência social",
    ):
        assert not c(erro)["e_cti"], erro

    # --- os cinco que só apareceram com o ano de 2026 inteiro ---
    #
    # Oito edições não bastavam para vê-los: cada um aparecia uma ou duas vezes
    # e passava por exceção. Em 214 edições viraram 219 matérias.
    for erro in (
        # 96 matérias. "Sociedade de Ensino Superior Estácio de Sá" é razão
        # social num termo de estágio, e "docentes de instituições de ensino
        # superior" é a composição de uma banca.
        "termo de compromisso de estágio entre a Secretaria de Fazenda, o estudante"
        " Thiago Borba Andrade e a Sociedade de Ensino Superior Estácio de Sá",
        "o corpo docente será formado, em sua maioria, por docentes de instituições"
        " de ensino superior do país ou estrangeiras",
        # 61 matérias. Progressão funcional e pontuação de concurso.
        "para fins de concessão do adicional de qualificação referente a cursos de"
        " pós-graduação lato sensu, mestrado ou doutorado",
        "para receber a pontuação relativa aos cursos de pós-graduação lato sensu",
        # 16 matérias. Vocabulário administrativo de qualquer secretaria.
        "as entidades vinculadas/supervisionadas deverão elaborar o plano anual",
        # 15 matérias. Cláusula-padrão que está em todo edital.
        "que não viole os direitos de terceiros, incluindo os de propriedade"
        " intelectual; f) atente contra a ordem pública",
        # 13 matérias. Equipamento de laboratório e tabela de preço de serviço.
        "doação de 26 (vinte e seis) incubadoras biológicas - equipamentos automatizados",
        "tração, por dia 60025034 taxa de incubadora por hora R$ 8,43",
    ):
        assert not c(erro)["e_cti"], erro

    # --- os dois fundos do art. 51 do regimento, que faltavam ---
    #
    # A ordem importa: o FATEC é gerido pela FAPERJ, e matéria da FAPERJ que
    # cita o fundo tem de continuar sendo da FAPERJ.
    assert c("40610 FATEC 323.818.473 323.818.473")["entidade"] == "fatec"
    assert c("Fundo para as Ciências do Estado do Rio de Janeiro - FUNCIERJ,"
             " extrato de termo")["entidade"] == "funcierj"
    assert c("A FAPERJ, gestora do Fundo de Apoio ao Desenvolvimento"
             " Tecnológico - FATEC, torna público")["entidade"] == "faperj"

    # --- três ou mais vinculadas não são de nenhuma delas ---
    #
    # O decreto de crédito lista todas as unidades da SECTI; a primeira da lista
    # levava. Mas quem publica manda: edital da FAPERJ que cita outras continua
    # dela.
    tabela = ("40410 FAPERJ 763.824.100 40430 UERJ 2.219.917.607 40450 UENF"
              " 447.059.248 40460 CECIERJ 119.764.360 40610 FATEC 280.892.454")
    assert c(tabela, orgao="ATOS DO PODER EXECUTIVO")["entidade"] == "varias"
    assert c("Programa de apoio a pesquisadores da UERJ, da UENF e do CECIERJ",
             orgao="Secretaria de Estado de Ciência, Tecnologia e Inovação",
             unidade="FUNDAÇÃO CARLOS CHAGAS FILHO DE AMPARO À PESQUISA")["entidade"] == "faperj"

    # --- e o que precisa continuar entrando ---
    #
    # Estes vieram da mesma auditoria e são a razão de o filtro existir: CT&I
    # feita por pasta que não é a SECTI.
    for certo in (
        "o Estado apoiará iniciativas de capacitação, pesquisa e inovação"
        " tecnológica voltadas ao setor de energia renovável",
        "convênio com a UFRRJ, com interveniência da Fundação de Apoio à Pesquisa"
        " Científica e Tecnológica",
        "a promoção de ações educacionais voltadas a ciência, tecnologia e inovação,"
        " sob a ótica de gênero",
        "edital do programa de pós-graduação em saúde coletiva, com bolsas",
        "aquisição de espectrômetro de massa para o laboratório de pesquisas aplicadas",
    ):
        assert c(certo)["e_cti"], certo

    r = c("convênio para o desenvolvimento tecnológico do setor naval fluminense")
    assert r["e_cti"] and r["confianca"] == "baixa", r

    # ICT estadual de outra pasta: é o caso que dá sentido ao filtro.
    r = c("PARTES: a Empresa de Pesquisa Agropecuária do Estado do Rio de Janeiro")
    assert r["e_cti"] and r["confianca"] == "alta", r

    r = c("implantação do Núcleo de Inovação Tecnológica da autarquia")
    assert r["e_cti"], r

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
