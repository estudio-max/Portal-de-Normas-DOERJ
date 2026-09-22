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

    print("autoteste vocabulario: tudo certo")
    return 0


if __name__ == "__main__":
    raise SystemExit(autoteste())
