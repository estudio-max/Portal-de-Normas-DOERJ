"""A árvore de termos de ciência, tecnologia e inovação da SECTI-RJ.

Não foi inventada aqui. Sai da **Minuta do Regimento Interno da nova SECTI,
versão 16**, e da **Lei estadual nº 9.809, de 22 de julho de 2022**, que o
regimento cita como fundamento.

Isso importa mais do que parece. Vocabulário montado por quem programa reflete
o que quem programa imagina que a secretaria faz. Vocabulário tirado do
regimento reflete o que ela **diz que faz** — e quando alguém questionar por que
determinado ato entrou na lente, a resposta é um artigo, não uma opinião.


OS TRÊS RAMOS SÃO AS TRÊS SUBSECRETARIAS

A própria SECTI já dividiu o assunto, e a divisão dela responde melhor do que a
tríade solta "ciência / tecnologia / inovação":

| Ramo | Subsecretaria |
|---|---|
| Governança do sistema | SUBSIS — Governança do Sistema Estadual de CT&I |
| Conhecimento, pesquisa e formação | SUBCON — Conhecimento, Pesquisa e Formação |
| Inovação e ambientes produtivos | SUBINOV — Inovação e Ambientes Produtivos |

"Ciência" mora no ramo do conhecimento, "inovação" no dos ambientes produtivos,
e "tecnologia" atravessa os dois — que é como ela se comporta na prática, e por
isso um ramo só para ela seria artificial.


O QUE VALE MAIS QUE PALAVRA SOLTA

`Lei nº 9.809/2022` é a âncora jurídica do sistema estadual de CT&I. Ato que a
cita é de CT&I com altíssima confiança, sem depender de nenhuma palavra do
vocabulário. O mesmo vale para `SISTECTI-RJ`, `CONECTI` e `FATEC`: são nomes
próprios criados por essa lei, e não aparecem por acaso.

Termo genérico como "tecnologia" é o oposto: aparece em contrato de impressora.
Por isso os pesos existem.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Âncoras: nome próprio criado pela legislação de CT&I do Estado. Quem cita,
# está falando do sistema. Não precisam de reforço.
# ---------------------------------------------------------------------------

ANCORAS = {
    "lei 9809": r"lei\s*(?:estadual\s*)?n?[ºo°.]?\s*9\.?809",
    "sistecti": r"sistecti",
    "conecti": r"\bconecti\b",
    "fatec": r"fundo de apoio ao desenvolvimento tecnologico|\bfatec\b",
    "polo virtual": r"polo virtual de inovacao",
    "estrategia estadual": r"estrategia estadual de ciencia",
    "ict": r"\bicts?\b|instituic(?:ao|oes) cientific",
    "marco legal": r"lei complementar\s*n?[ºo°.]?\s*182|marco legal da inovacao|"
                   r"lei\s*n?[ºo°.]?\s*10\.?973",
}

# ---------------------------------------------------------------------------
# As entidades do sistema. Ato delas é do recorte, inclusive o de pessoal:
# saber quem entra e quem sai da FAPERJ é parte de entender a pasta.
# ---------------------------------------------------------------------------

# A ordem importa: quem procura devolve a primeira que casar, e as vinculadas
# vêm antes da secretaria de propósito. Todas elas publicam sob o nome da SECTI,
# então a secretaria casaria sempre e a vinculada nunca — e a lente que dá a
# cada uma o seu espaço ficaria vazia.
#
# A SECTI fica por último: sobra para as matérias da própria pasta, que são as
# que nenhuma vinculada reivindicou.
ENTIDADES = {
    "faperj": r"\bfaperj\b|fundacao carlos chagas filho",
    "uerj": r"\buerj\b|universidade do estado do rio de janeiro",
    "uenf": r"\buenf\b|universidade estadual do norte fluminense",
    "cecierj": r"\bcecierj\b|educacao superior a distancia",
    "faetec": r"\bfaetec\b|fundacao de apoio a escola tecnica",
    "subsis": r"\bsubsis\b",
    "subcon": r"\bsubcon\b",
    "subinov": r"\bsubinov\b",
    "secti": r"secretaria de estado de ciencia",
}

# ---------------------------------------------------------------------------
# Os três ramos, com os termos que o regimento usa em cada um.
#
# A referência entre parênteses é o artigo de onde o termo saiu, para que a
# curadoria possa conferir em vez de acreditar.
# ---------------------------------------------------------------------------

RAMOS = {
    "governanca": {
        "nome": "Governança do sistema estadual",
        "subsecretaria": "SUBSIS",
        "fonte": "Regimento, art. 26; Lei 9.809/2022",
        "termos": [
            r"politica estadual de ciencia",
            r"sistema estadual de ciencia",
            r"sistemas? municipa(?:l|is) de ciencia",
            r"consorcios? intermunicipa",
            r"plano de acao.{0,40}(ciencia|inovacao)",
            r"mapeamento tecnologico",
            r"prospeccao tecnologica",
            r"diagnostico.{0,30}tecnologic",
            r"indicadores.{0,30}(ciencia|inovacao|tecnolog)",
            r"cadastro estadual de icts",
            r"redes de pesquisa",
            r"grupos de pesquisa",
            r"entidades vinculadas",
            r"supervisao finalistica",
            r"autonomia universitaria",
            r"conselho estadual de ciencia",
            r"camara tecnica.{0,30}(ciencia|inovacao)",
            r"foruns? oficia",
        ],
    },
    "conhecimento": {
        "nome": "Conhecimento, pesquisa e formação",
        "subsecretaria": "SUBCON",
        "fonte": "Regimento, arts. 34 a 40",
        "termos": [
            r"pesquisa cientifica",
            r"producao cientifica",
            r"pos-graduacao",
            r"ensino superior",
            r"educacao (?:tecnica|tecnologica|profissionalizante)",
            r"ensino (?:tecnico|tecnologico)",
            r"formacao.{0,25}recursos humanos",
            r"capacitacao.{0,30}(ciencia|tecnolog|inovacao)",
            r"bolsa de estimulo a inovacao",
            r"bolsa de extensao tecnologica",
            r"bolsa de (?:pesquisa|iniciacao|mestrado|doutorado|pos-doutorado)",
            r"iniciacao cientifica",
            r"compartilhamento de laboratorios",
            r"capital intelectual",
            r"tecnologias? socia",
            r"extensao tecnologica",
            r"inclusao produtiva",
            r"popularizacao da ciencia",
            r"cultura cientifica",
            r"divulgacao cientifica",
            r"equidade (?:racial|de genero).{0,40}(ciencia|tecnolog|inovacao)",
            r"laboratori(?:o|os) de pesquisa",
            r"pesquisador(?:es|as)?\b",
        ],
    },
    "inovacao": {
        "nome": "Inovação e ambientes produtivos",
        "subsecretaria": "SUBINOV",
        "fonte": "Regimento, arts. 41 a 47",
        "termos": [
            r"parques? tecnologic",
            r"polos? tecnologic",
            r"incubadora",
            r"aceleradora",
            r"ambientes? promotor(?:es)? da inovacao",
            r"ambientes? de inovacao",
            r"\bstartups?\b",
            r"startup rio",
            r"empreendimentos? inovador",
            r"agencias? de inovacao",
            r"nucleos? de inovacao tecnologica",
            r"\bnits?\b",
            r"propriedade (?:intelectual|industrial)",
            r"transferencia de tecnologia",
            r"encomenda tecnologica",
            r"bonus tecnologico",
            r"subvencao economica",
            r"compras? publicas? em inovacao",
            r"poder de compra.{0,30}inovacao",
            r"participacao societaria.{0,40}inovacao",
            r"inventor independente",
            r"centros? de pesquisa e desenvolvimento",
            r"pesquisa, desenvolvimento e inovacao",
            r"\bp&d\b|\bpd&i\b",
            r"inovacao aberta",
        ],
    },
}

# ---------------------------------------------------------------------------
# NATUREZA DO ATO — o segundo eixo, e o que estrutura a navegação.
#
# São oito categorias derivadas dos rótulos que o **próprio Diário** usa para
# separar as suas matérias, e medidas em 2.012 delas antes de virarem código.
# Não classificam assunto: classificam **o que o ato faz**.
#
# Valem para toda matéria, e não só para as de CT&I. O portal mostra tudo, e
# quem procura um aditivo de contrato procura do mesmo jeito dentro ou fora do
# recorte temático.
#
# Uma matéria pode ter mais de uma, e isso é fiel ao objeto: um edital de pregão
# para equipar laboratório é compra **e** contrato.
# ---------------------------------------------------------------------------

NATUREZA = {
    "contratos": {
        "nome": "Contratos e convênios",
        "termos": [
            r"extrato de (?:instrumento|termo)", r"instrumento contratual",
            r"termo aditivo", r"\bcontrato n", r"convenio", r"termo de cooperacao",
            r"termo de fomento", r"termo de colaboracao", r"vigencia",
            r"faturar por empenho", r"valor (?:total|global) d", r"contratada?\b",
            r"prorroga(?:cao|r).{0,40}contrato", r"rescis(?:ao|ao contratual)",
        ],
    },
    "academico": {
        "nome": "Ensino e vida acadêmica",
        "termos": [
            r"matricula(?!\s*funcional)", r"vestibular", r"calendario (?:academico|escolar)",
            r"colacao de grau", r"curso (?:tecnico|de graduacao|superior|de pos)",
            r"diploma", r"discente", r"corpo docente", r"concurso publico",
            r"processo seletivo", r"prova (?:objetiva|discursiva)", r"gabarito",
            r"isencao de taxa", r"classificacao final", r"banca examinadora",
            r"monitoria", r"estagio (?:obrigatorio|curricular|supervisionado)",
        ],
    },
    "compras": {
        "nome": "Compras e licitações",
        "termos": [
            r"pregao (?:eletronico|presencial)", r"licitacao", r"dispensa de licitacao",
            r"inexigibilidade", r"homologa(?:cao|r|do)", r"adjudica",
            r"tomada de precos", r"concorrencia publica", r"credenciamento",
            r"registro de precos", r"ata de registro", r"menor preco",
            r"aviso de (?:licitacao|pregao|suspensao)", r"edital de pregao",
        ],
    },
    "pessoal": {
        "nome": "Pessoal",
        "termos": [
            r"\bnomear\b", r"\bexonerar\b", r"\bnomeacao\b", r"\bexoneracao\b",
            r"aposenta(?:r|doria|do|da)", r"licenca premio", r"licenca especial",
            r"matricula funcional", r"cargo em comissao", r"tomar posse|\bposse\b",
            r"cessao de servidor", r"remocao", r"lotacao", r"redistribuicao",
            r"contrato temporario", r"admissao", r"progressao funcional",
            r"averbacao de tempo", r"pensao", r"substituicao.{0,30}(titular|impedimento)",
        ],
    },
    "governanca": {
        "nome": "Governança e normas",
        "termos": [
            r"fica(?:m)? institu", r"\binstituir\b", r"regimento interno",
            r"regulamenta(?:r|cao)", r"aprova o regulamento", r"plano estadual",
            r"politica estadual", r"diretrizes", r"estrutura organizacional",
            r"competencias? d[aeo]", r"delega(?:cao|r) de competencia",
            r"conselho estadual", r"camara tecnica", r"fica(?:m)? aprovad",
        ],
    },
    "comissoes": {
        "nome": "Comissões e fiscalização",
        "termos": [
            r"comissao de (?:fiscaliza|acompanh|gestao|avalia|sindic|licita|etica)",
            r"gestor do contrato", r"fiscal (?:do contrato|setorial|tecnico)",
            r"grupo de trabalho", r"comite gestor", r"designar.{0,60}compor",
            r"processo administrativo disciplinar", r"sindicancia",
        ],
    },
    "orcamento": {
        "nome": "Orçamento e finanças",
        "termos": [
            r"credito (?:suplementar|especial|extraordinario)", r"dotacao orcamentaria",
            r"programa de trabalho", r"natureza de despesa", r"fonte de recursos",
            r"ordenador de despesas", r"descentralizacao de credito",
            r"nota de empenho", r"anulacao de empenho", r"restos a pagar",
            r"abre credito", r"suplementa",
        ],
    },
    "fomento": {
        "nome": "Fomento e bolsas",
        "termos": [
            r"\bbolsa", r"auxilio a pesquisa", r"auxilio instalacao",
            r"chamada publica", r"edital de (?:apoio|fomento|selecao)",
            r"subvencao", r"concessao de (?:bolsa|auxilio)", r"apoio financeiro",
            r"financiamento a pesquisa", r"projeto (?:contemplado|aprovado)",
        ],
    },

    # As três abaixo não estavam na proposta de oito. Foram acrescentadas depois
    # de medir o que sobrava sem categoria: eram 583 matérias, 29% do corpus, e
    # dentro delas havia três grupos com nome próprio. A maior, sozinha, tem 356.
    #
    # Deixá-las fora não tornaria o Diário mais simples: tornaria a navegação
    # mentirosa, porque um terço do acervo cairia num "outros" que ninguém abre.
    "despachos": {
        "nome": "Despachos em processos",
        "termos": [
            # **"processo nº" ficou de fora.** Ele aparece em 91% das matérias,
            # porque o SEI numera tudo — e com ele aqui esta categoria engolia
            # 1.298 das 2.012, dois terços do acervo. Número de processo diz
            # onde o ato tramita, não que ele seja um despacho.
            r"despachos? d[aeo]\b", r"\bdefiro\b", r"\bindefiro\b", r"\bautorizo\b",
            r"\bhomologo\b", r"\baprovo\b", r"\bratifico\b",
            r"arquive-se", r"cientifique-se", r"publique-se", r"restitua-se",
            r"na forma do parecer", r"acolho o parecer", r"de acordo com o parecer",
        ],
    },
    "contencioso": {
        "nome": "Julgamento e contencioso",
        "termos": [
            r"conselho de contribuintes", r"recurso (?:voluntario|de oficio|hierarquico)",
            r"\bacordao\b", r"\brelator\b", r"(?:negar|dar) provimento",
            r"julgar (?:procedente|improcedente)", r"auto de infracao",
            r"defesa administrativa", r"impugnacao", r"junta de revisao",
            r"decisao monocratica", r"camara de julgamento",
        ],
    },
    "retificacoes": {
        "nome": "Retificações e republicações",
        "termos": [
            r"\bretificacao\b", r"\berrata\b", r"republicacao por incorrecao",
            r"onde se le", r"leia-se", r"tornar sem efeito", r"torna sem efeito",
            r"\bapostila\b", r"fica retificad", r"ratifica(?:cao|r) o (?:ato|despacho)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Termos genéricos: sozinhos não bastam. "Tecnologia" aparece em contrato de
# impressora, e "inovação" em jargão de atribuição de cargo — foi medido: cinco
# matérias entraram por "melhoria ou inovação em seus processos institucionais".
# ---------------------------------------------------------------------------

GENERICOS = [
    r"tecnolog",
    r"inovac",
    r"cientific",
    r"ciencia e tecnologia",
    r"ciencia, tecnologia",
    r"ciencias\b",
    r"laboratori",
]

# O sentido jurídico de "ciência". Medido: 51 das 63 matérias que entraram por
# "ciência" eram "tomar ciência do débito". Apagado do texto antes de procurar.
RUIDO = [
    # Os verbos da notificação. **`de` e `da` ficaram de fora de propósito**:
    # eles são genéricos demais e comiam o nome da própria pasta — "Secretaria
    # de Estado **de Ciência**, Tecnologia e Inovação" virava "Secretaria de
    # Estado, Tecnologia e Inovação", e 148 matérias da SECTI deixaram de ser
    # reconhecidas como dela.
    r"(?:dar|ter|tomar|teve|tomou|deu|apos a)\s+ciencia\b",
    # "ciência do débito", "ciência da decisão": é a notificação outra vez, e
    # aqui o `d[aeo]` seguinte é o que a distingue do nome da pasta, que vem
    # seguido de vírgula ou de "e tecnologia".
    r"\bciencia\s+d[aeo]\s+\w",
    r"cientificar|cientificado|cientificada",
    r"pesquisa de preco|pesquisa de mercado",
    r"melhoria ou inovacao",
    r"inovacao em seus processos",
]


def _junta(padroes) -> re.Pattern:
    return re.compile("|".join(padroes), re.I)


ANCORA = _junta(ANCORAS.values())
ENTIDADE = _junta(ENTIDADES.values())
GENERICO = _junta(GENERICOS)
RUIDO_RE = _junta(RUIDO)
POR_RAMO = {k: _junta(v["termos"]) for k, v in RAMOS.items()}
POR_NATUREZA = {k: _junta(v["termos"]) for k, v in NATUREZA.items()}


def normalizar(texto: str) -> str:
    sem = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem.lower())


def limpar(texto: str) -> str:
    """Tira o que parece CT&I e não é, antes de qualquer busca."""
    return RUIDO_RE.sub(" ", normalizar(texto))


def qual_ancora(alvo: str) -> str | None:
    for nome, padrao in ANCORAS.items():
        if re.search(padrao, alvo, re.I):
            return nome
    return None


def qual_entidade(alvo: str) -> str | None:
    for nome, padrao in ENTIDADES.items():
        if re.search(padrao, alvo, re.I):
            return nome
    return None


def quais_naturezas(alvo: str) -> list[str]:
    """O que o ato faz. Pode ser mais de uma coisa, e costuma ser."""
    return [chave for chave, padrao in POR_NATUREZA.items() if padrao.search(alvo)]


def autoteste() -> int:
    # Âncoras: entram sozinhas, sem precisar de mais nada.
    for t in ("nos termos da Lei nº 9.809, de 22 de julho de 2022",
              "integrante do SISTECTI-RJ",
              "submeter ao CONECTI",
              "gestão do FATEC",
              "cadastro estadual de ICTs"):
        assert qual_ancora(limpar(t)), t

    assert qual_entidade(limpar("Fundação Carlos Chagas Filho de Amparo à Pesquisa")) == "faperj"
    assert qual_entidade(limpar("UNIVERSIDADE ESTADUAL DO NORTE FLUMINENSE")) == "uenf"
    assert qual_entidade(limpar("contrato de limpeza predial")) is None

    # A vinculada ganha da secretaria. Todas publicam sob o nome da SECTI, e sem
    # esta ordem a lente por vinculada ficaria vazia.
    junto = limpar("SECRETARIA DE ESTADO DE CIÊNCIA, TECNOLOGIA E INOVAÇÃO "
                   "FUNDAÇÃO CARLOS CHAGAS FILHO DE AMPARO À PESQUISA")
    assert qual_entidade(junto) == "faperj", qual_entidade(junto)

    # E a secretaria sobra para o que é dela mesma.
    sozinha = limpar("SECRETARIA DE ESTADO DE CIÊNCIA, TECNOLOGIA E INOVAÇÃO "
                     "ATO DO SECRETÁRIO")
    assert qual_entidade(sozinha) == "secti", qual_entidade(sozinha)

    # Cada ramo reconhece o que é dele.
    assert POR_RAMO["governanca"].search(limpar("atualização da Estratégia Estadual e seu Plano de Ação de inovação"))
    assert POR_RAMO["conhecimento"].search(limpar("bolsa de iniciação científica"))
    assert POR_RAMO["inovacao"].search(limpar("apoio a incubadoras e aceleradoras"))
    assert POR_RAMO["inovacao"].search(limpar("encomenda tecnológica e bônus tecnológico"))

    # E não reconhece o que não é.
    assert not POR_RAMO["inovacao"].search(limpar("contrato de manutenção predial"))

    # O ruído some antes de ser procurado.
    for t in ("para tomar ciência do débito apurado",
              "fica o contribuinte cientificado da decisão",
              "realização de pesquisa de preços",
              "oportunidades de melhoria ou inovação em seus processos institucionais"):
        limpo = limpar(t)
        assert not GENERICO.search(limpo), (t, limpo)

    # Mas o sentido de verdade sobrevive.
    assert GENERICO.search(limpar("Secretaria de Estado de Ciência e Tecnologia"))
    assert GENERICO.search(limpar("bolsa em ciências agrárias"))

    # O nome da pasta não pode ser comido pela limpeza do ruído. Foi o que
    # aconteceu quando `de` estava entre os verbos de notificação: 148 matérias
    # da SECTI deixaram de ser reconhecidas como dela.
    for nome in ("Secretaria de Estado de Ciência, Tecnologia e Inovação",
                 "Secretaria de Estado de Ciência e Tecnologia",
                 "Secretaria de Estado de Ciência, Tecnologia, Inovação e "
                 "Desenvolvimento Social"):
        assert qual_entidade(limpar(nome)) == "secti", (nome, limpar(nome))

    # E a notificação continua saindo.
    assert qual_entidade(limpar("tomar ciência do débito")) is None
    assert not GENERICO.search(limpar("dar ciência da decisão ao interessado"))

    assert len(RAMOS) == 3, "os ramos são as três subsecretarias"
    for chave, ramo in RAMOS.items():
        assert ramo["fonte"], f"{chave} sem fonte no regimento"

    # ---------------------------------------------------- natureza do ato
    # Oito aprovadas, mais três que a medição do que sobrava exigiu.
    assert len(NATUREZA) == 11, len(NATUREZA)

    def nat(t):
        return quais_naturezas(limpar(t))

    assert "pessoal" in nat("NOMEAR FULANO DE TAL para exercer o cargo em comissão")
    assert "pessoal" in nat("EXONERAR, a pedido, a servidora de matrícula funcional")
    assert "pessoal" in nat("concede 3 meses de licença prêmio ao servidor")
    assert "contratos" in nat("EXTRATO DE TERMO ADITIVO ao Contrato nº 46/2020")
    assert "compras" in nat("AVISO DE LICITAÇÃO. Pregão eletrônico nº 12/2026")
    assert "orcamento" in nat("ABRE CRÉDITO SUPLEMENTAR no valor global de")
    assert "fomento" in nat("concessão de bolsa de iniciação científica")
    assert "academico" in nat("resultado final do processo seletivo para o curso técnico")
    assert "comissoes" in nat("designar os servidores para compor a comissão de fiscalização")
    assert "governanca" in nat("Fica instituído o Comitê Gestor, e aprovado o regimento interno")

    # "matrícula funcional" é de pessoal; "matrícula" de aluno é acadêmica. A
    # distinção está no padrão, e sem ela toda nomeação viraria vida acadêmica.
    assert "academico" not in nat("servidor de matrícula funcional nº 123")
    assert "academico" in nat("abertura do período de matrícula dos alunos")

    # Uma matéria pode fazer duas coisas, e isso é fiel ao objeto.
    duplo = nat("AVISO DE LICITAÇÃO pregão eletrônico para contratação, "
                "Contrato nº 9/2026, vigência de 12 meses")
    assert {"compras", "contratos"} <= set(duplo), duplo

    # --- as três acrescentadas depois de medir o que sobrava ---
    assert "retificacoes" in nat("RETIFICAÇÃO. No D.O. de 21/09/2026, página 30, "
                                 "onde se lê 'Fulano', leia-se 'Sicrano'")
    assert "retificacoes" in nat("TORNAR SEM EFEITO o Ato de 23 de março de 2026")
    assert "despachos" in nat("DESPACHO DO PRESIDENTE. Processo nº SEI-260002/005670/2026. "
                              "AUTORIZO a contratação na forma do parecer")
    assert "contencioso" in nat("CONSELHO DE CONTRIBUINTES. Recurso voluntário desprovido. "
                                "Acórdão. Relator:")
    assert "contencioso" in nat("AUTO DE INFRAÇÃO nº SUPPIBEAI/00133441")

    # Despacho que autoriza contrato é as duas coisas, e a tela mostra as duas.
    r = nat("DESPACHO DO SECRETÁRIO. AUTORIZO a celebração do Contrato nº 9/2026")
    assert {"despachos", "contratos"} <= set(r), r

    print("autoteste vocabulario: tudo certo")
    return 0


if __name__ == "__main__":
    raise SystemExit(autoteste())
