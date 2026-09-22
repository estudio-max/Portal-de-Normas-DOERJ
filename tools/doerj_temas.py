"""Classifica as matérias por tema de ciência, tecnologia e inovação.

    python tools/doerj_temas.py extraido/*.jsonl
    python tools/doerj_temas.py extraido/*.jsonl --amostra 20
    python tools/doerj_temas.py --autoteste

Escreve `tema` e `temas` de volta no JSONL. Não toca no banco.


OS GRUPOS SÃO OS DO MAPA DE CT&I, E ISSO É DECISÃO DE PRODUTO

Os nove grupos vêm do `database/seed/01-camadas.sql` do Mapa de CT&I da
SECTI-RJ. Não foram inventados aqui.

O ganho não é economia de trabalho: é as duas ferramentas falarem a mesma
língua. Quando o mapa mostra que um município tem incubadora e o portal mostra
que saiu uma resolução sobre ecossistema empresarial, as duas coisas se
encontram porque estão no mesmo vocabulário. Taxonomia paralela produziria dois
retratos do mesmo Estado que não conversam.


DUAS ETAPAS, E A PRIMEIRA É O QUE EVITA O DESASTRE

A tentação é jogar palavra-chave no texto inteiro e ver o que cola. Isso não
funciona aqui, e o motivo é estrutural: **os grupos do Mapa classificam
instituição e infraestrutura, não ato administrativo.**

"Saúde e bioeconomia" existe para marcar um laboratório de biotecnologia. Se
virar simples busca por "saúde", toda nomeação da Secretaria de Saúde entra — e
são centenas por edição. O tema afoga em movimentação de pessoal, e a lente
perde a serventia exatamente por excesso.

Então são duas perguntas, nesta ordem:

1. **Isto é de CT&I?** Precisa de um termo do núcleo — pesquisa científica,
   inovação, tecnologia, laboratório — ou de uma instituição do sistema —
   FAPERJ, UERJ, UENF, CECIERJ, FAETEC.
2. **Se for, de qual grupo?** Aí sim o vocabulário específico decide, e uma
   matéria pode cair em mais de um.

Sem o portão, "energia" marcaria todo contrato de luz e "ambiente" todo auto do
INEA.


O QUE ESTA FERRAMENTA NÃO PRETENDE

Acertar sempre. Classificação por vocabulário erra, e por isso **tudo que sai
daqui vai marcado como automático**. A tela tem que dizer isso a quem lê, e a
curadoria tem que poder corrigir sem recomeçar.

A armadilha conhecida está no teste: **"pesquisa de preços" é licitação, não
ciência.** Foram duas ocorrências em 850 matérias, e bastariam para pôr um
pregão no meio dos editais de fomento.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


def normalizar(texto: str) -> str:
    """Sem acento e em minúscula, para o vocabulário não precisar de variantes."""
    sem = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem.lower())


def termos(*palavras: str) -> re.Pattern:
    return re.compile(r"\b(?:" + "|".join(palavras) + r")", re.I)


# ---------------------------------------------------------------- etapa 1

# O portão. Sem um destes, a matéria não é de CT&I, por mais que fale de saúde
# ou de energia.
NUCLEO = termos(
    r"pesquisa cientifica", r"pesquisador", r"pesquisadora", r"cientific",
    # "ciencia" sozinha NÃO entra. Ver CIENCIA_DE_NOTIFICACAO, logo abaixo.
    r"ciencia e tecnologia", r"ciencia, tecnologia", r"ciencias\b",
    r"tecnolog", r"inovac", r"laboratori", r"p&d",
    r"pesquisa e desenvolvimento", r"propriedade intelectual", r"patente",
    r"iniciacao cientifica", r"pos-graduacao", r"mestrado", r"doutorado",
    r"bolsa de estudo", r"bolsa de pesquisa", r"incubadora", r"startup",
    r"parque tecnologico", r"polo tecnologico", r"transferencia de tecnologia",
    r"marco legal da inovacao",
)

# As instituições do sistema estadual de CT&I. Qualquer ato delas é do recorte,
# inclusive movimentação de pessoal: saber quem entra e quem sai da FAPERJ é
# parte de entender a pasta.
INSTITUICOES = termos(
    r"faperj", r"fundacao carlos chagas filho",
    r"uerj", r"universidade do estado do rio de janeiro",
    r"uenf", r"universidade estadual do norte fluminense",
    r"cecierj", r"educacao superior a distancia",
    r"faetec", r"fundacao de apoio a escola tecnica",
    r"secretaria de estado de ciencia",
)

# A palavra mais traiçoeira do vocabulário, e a medição mostrou o tamanho:
# **51 das 63 matérias que entraram por "ciência" eram "tomar ciência do
# débito"** — 81% de erro num termo só.
#
# Em português jurídico, "ciência" quer dizer ser notificado muito mais vezes do
# que quer dizer o campo do conhecimento. "Dar ciência ao interessado", "após a
# ciência do lançamento", "para tomar ciência do processo". Num Diário Oficial
# esse sentido é o dominante.
#
# Por isso "ciencia" sozinha saiu do núcleo: ela só entra acompanhada —
# "ciência e tecnologia", "ciência, tecnologia" — ou no plural, que é como o
# nome de área aparece ("ciências agrárias", "ciências da saúde").
CIENCIA_DE_NOTIFICACAO = termos(
    r"(?:dar|ter|tomar|teve|tomou|deu|apos a|da|de|para)\s+ciencia\b",
    r"cientificar", r"cientificado", r"cientificada",
)

# O que parece CT&I e não é. Vem antes de tudo.
#
# "Pesquisa de preços" é o caso que a medição pegou: aparece em pregão e em
# dispensa, e sem esta linha um pregão de material de limpeza entraria como
# pesquisa científica.
FALSOS = [
    (termos(r"pesquisa de preco", r"pesquisa de mercado", r"pesquisa de precos"),
     "pesquisa de preços é licitação"),
    (termos(r"tecnologia da informacao e comunicacao do estado"),
     "nome de órgão, não tema"),
]

# ---------------------------------------------------------------- etapa 2
#
# Os nove grupos do Mapa de CT&I, na ordem em que ele os apresenta. O `slug` é o
# mesmo dos tokens de cor do Mapa, para a tela poder usar a mesma paleta.

GRUPOS = [
    ("conectividade", "Conectividade", termos(
        r"telecomunicac", r"satelite", r"cabo submarino", r"rede optica",
        r"fibra optica", r"banda larga", r"espectro", r"anatel", r"5g",
        r"ponto de presenca", r"backbone", r"radiofrequencia", r"conectividade",
    )),
    ("conhecimento", "Conhecimento e pesquisa", termos(
        r"pesquisa cientifica", r"pesquisador", r"laboratori", r"instituto de pesquisa",
        r"universidade", r"campus", r"educacao a distancia", r"pos-graduacao",
        r"mestrado", r"doutorado", r"iniciacao cientifica", r"producao cientifica",
        r"uerj", r"uenf", r"cecierj", r"cientific",
    )),
    ("ecossistema", "Ecossistema empresarial", termos(
        r"startup", r"incubadora", r"aceleradora", r"parque tecnologico",
        r"polo tecnologico", r"hub de inovacao", r"empresa de base tecnologica",
        r"inovacao aberta", r"spin-off", r"ambiente de inovacao",
    )),
    ("fomento", "Fomento à CT&I", termos(
        r"faperj", r"fundacao carlos chagas filho", r"fomento",
        r"bolsa de pesquisa", r"auxilio a pesquisa", r"subvencao economica",
        r"chamada publica", r"edital de apoio", r"financiamento a pesquisa",
    )),
    ("formacao", "Formação científica e técnica", termos(
        r"faetec", r"escola tecnica", r"curso tecnico", r"ensino tecnologico",
        r"educacao profissional", r"qualificacao profissional",
        r"formacao tecnica", r"aprendizagem industrial",
    )),
    ("governanca", "Governança e capacidade", termos(
        r"politica de ciencia", r"politica estadual de inovacao",
        r"sistema estadual de inovacao", r"conselho.{0,30}ciencia",
        r"plano.{0,20}ciencia", r"marco legal da inovacao",
        r"comite gestor.{0,40}(ciencia|inovacao|tecnolog)",
        r"secretaria de estado de ciencia",
    )),
    ("industria", "Indústria e energia", termos(
        r"aeroespacial", r"industria naval", r"industria tecnologica",
        r"base industrial de defesa", r"petroleo e gas", r"anp\b",
        r"energia renovavel", r"hidrogenio verde", r"nuclear",
    )),
    ("infraestrutura", "Infraestrutura digital", termos(
        r"data center", r"datacenter", r"computacao em nuvem", r"nuvem",
        r"transformacao digital", r"governo digital", r"ativos de ti",
        r"inteligencia artificial", r"software", r"sistema de informacao",
    )),
    ("saude", "Saúde e bioeconomia", termos(
        r"biotecnolog", r"farmac", r"vacina", r"bioeconomia", r"biodiversidade",
        r"imunobiolog", r"ensaio clinico", r"pesquisa clinica", r"genomic",
        r"agroindustri", r"aquicultura", r"seguranca alimentar",
    )),
]


def classificar(texto: str, ementa: str | None, orgao: str | None,
                unidade: str | None) -> dict:
    """Devolve os temas da matéria, ou vazio quando não é do recorte."""
    alvo = normalizar(" ".join(x for x in (ementa, orgao, unidade, texto) if x))

    # O sentido jurídico de "ciência" é apagado do texto antes de procurar
    # qualquer coisa, e não excluído depois. Assim "cientificado" some junto,
    # em vez de escapar por casar com `cientific`.
    alvo = CIENCIA_DE_NOTIFICACAO.sub(" ", alvo)

    for padrao, motivo in FALSOS:
        if padrao.search(alvo) and not INSTITUICOES.search(alvo):
            return {"e_cti": False, "temas": [], "motivo": motivo}

    por_instituicao = bool(INSTITUICOES.search(alvo))
    if not (por_instituicao or NUCLEO.search(alvo)):
        return {"e_cti": False, "temas": [], "motivo": None}

    achados = [slug for slug, _, padrao in GRUPOS if padrao.search(alvo)]

    # Passou no portão e nenhum grupo reconheceu: é de CT&I, e a curadoria
    # decide de qual grupo. Deixar sem grupo é mais honesto que forçar um.
    return {
        "e_cti": True,
        "temas": achados,
        "motivo": "instituição do sistema" if por_instituicao and not achados else None,
    }


def nome_do_grupo(slug: str) -> str:
    return next(nome for s, nome, _ in GRUPOS if s == slug)


def processar(caminhos: list[Path], amostra: int) -> int:
    contagem: Counter = Counter()
    exemplos: dict[str, list] = {}
    total = de_cti = sem_grupo = 0

    for caminho in caminhos:
        linhas = [
            json.loads(x)
            for x in caminho.read_text(encoding="utf-8").splitlines()
            if x.strip()
        ]
        for r in linhas:
            resultado = classificar(
                r.get("texto") or "", r.get("ementa"),
                r.get("orgao"), r.get("unidade"),
            )
            r["e_cti"] = resultado["e_cti"]
            r["temas"] = resultado["temas"]
            # Nada aqui foi conferido por pessoa, e a tela tem que dizer isso.
            r["temas_origem"] = "automatico"

            total += 1
            if resultado["e_cti"]:
                de_cti += 1
                if not resultado["temas"]:
                    sem_grupo += 1
                for t in resultado["temas"]:
                    contagem[t] += 1
                    exemplos.setdefault(t, []).append(r)

        with caminho.open("w", encoding="utf-8") as f:
            for r in linhas:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{total} matérias")
    print(f"{de_cti} passaram no portão de CT&I ({de_cti * 100 // max(total,1)}%)")
    print(f"{sem_grupo} de CT&I sem grupo reconhecido, à espera de curadoria")
    print()
    for slug, nome, _ in GRUPOS:
        n = contagem.get(slug, 0)
        barra = "#" * min(40, n * 40 // max(contagem.values(), default=1))
        print(f"  {nome:32} {n:4}  {barra}")

    if amostra:
        print()
        for slug, nome, _ in GRUPOS:
            itens = exemplos.get(slug, [])[:max(1, amostra // len(GRUPOS))]
            if not itens:
                continue
            print(f"\n  --- {nome} ---")
            for r in itens:
                rotulo = r.get("ementa") or (r.get("texto") or "")[:110]
                print(f"    {r['data_pub']} {str(r.get('unidade') or r.get('orgao'))[:34]:36}")
                print(f"      {re.sub(r'[ \n]+', ' ', rotulo)[:110]}")
    return 0


def autoteste() -> int:
    def temas(texto, ementa=None, orgao=None, unidade=None):
        return classificar(texto, ementa, orgao, unidade)

    # --- o portão barra o que não é de CT&I ---
    r = temas("NOMEAR FULANO DE TAL para exercer o cargo em comissão",
              orgao="Secretaria de Estado de Saúde")
    assert not r["e_cti"], r

    r = temas("Contrato de fornecimento de energia elétrica para o prédio",
              orgao="Secretaria de Estado de Fazenda")
    assert not r["e_cti"], r

    r = temas("AUTO DE INFRAÇÃO ambiental por supressão de vegetação",
              orgao="Instituto Estadual do Ambiente")
    assert not r["e_cti"], r

    # --- as armadilhas medidas ---
    r = temas("torna público a realização de PESQUISA DE PREÇOS destinada a "
              "aferir os preços estimados para prestação de serviços")
    assert not r["e_cti"], r
    assert "licitação" in (r["motivo"] or ""), r

    # "Ciência" no sentido de ser notificado: 51 das 63 ocorrências no corpus.
    for juridico in (
        "com a finalidade de tomar ciência do débito apurado no processo",
        "visto que o pagamento ocorreu após a ciência do lançamento",
        "dar ciência ao interessado do teor da decisão",
        "fica o contribuinte cientificado da decisão",
    ):
        assert not temas(juridico)["e_cti"], juridico

    # Mas acompanhada, entra.
    assert temas("Secretaria de Estado de Ciência e Tecnologia")["e_cti"]
    assert temas("bolsa na área de ciências agrárias")["e_cti"]

    # Mas pesquisa de preços feita pela FAPERJ continua sendo da FAPERJ.
    r = temas("pesquisa de preços para aquisição", unidade="FAPERJ")
    assert r["e_cti"], r

    # --- o que tem que entrar ---
    r = temas("Concede auxílio à pesquisa no âmbito do programa de fomento",
              unidade="FUNDAÇÃO CARLOS CHAGAS FILHO DE AMPARO À PESQUISA")
    assert r["e_cti"] and "fomento" in r["temas"], r

    r = temas("Dispõe sobre o curso técnico de eletrotécnica",
              unidade="FUNDAÇÃO DE APOIO À ESCOLA TÉCNICA")
    assert "formacao" in r["temas"], r

    r = temas("Incubadora Sul Fluminense: infraestrutura para ambiente de inovação",
              unidade="UERJ")
    assert "ecossistema" in r["temas"] and "conhecimento" in r["temas"], r

    r = temas("contratação de data center e computação em nuvem para o Estado",
              ementa="MODERNIZA A INFRAESTRUTURA DE TECNOLOGIA DA INFORMAÇÃO")
    assert "infraestrutura" in r["temas"], r

    r = temas("laboratório de biotecnologia para produção de imunobiológicos")
    assert "saude" in r["temas"] and "conhecimento" in r["temas"], r

    # Nomeação na UERJ entra: saber quem entra e quem sai do sistema é parte de
    # entender a pasta.
    r = temas("NOMEAR FULANO para o cargo", unidade="UNIVERSIDADE DO ESTADO DO RIO DE JANEIRO")
    assert r["e_cti"], r

    # Passou no portão sem grupo: fica sem grupo, e não num grupo forçado.
    r = temas("Designa comissão", unidade="FUNDAÇÃO DE APOIO À ESCOLA TÉCNICA")
    assert r["e_cti"] and "formacao" in r["temas"], r

    assert normalizar("Ciência, Tecnologia e Inovação") == "ciencia, tecnologia e inovacao"
    assert {s for s, _, _ in GRUPOS} == {
        "conectividade", "conhecimento", "ecossistema", "fomento", "formacao",
        "governanca", "industria", "infraestrutura", "saude",
    }
    assert len(GRUPOS) == 9, "os grupos são os nove do Mapa de CT&I"

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("jsonl", nargs="*", type=Path)
    p.add_argument("--amostra", type=int, default=0,
                   help="mostra exemplos de cada grupo, para conferir a olho")
    p.add_argument("--autoteste", action="store_true")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.jsonl:
        p.error("informe ao menos um .jsonl, ou --autoteste")
    return processar(o.jsonl, o.amostra)


if __name__ == "__main__":
    raise SystemExit(main())
