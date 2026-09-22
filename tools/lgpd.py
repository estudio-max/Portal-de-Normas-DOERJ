"""Tira CPF e documento de identidade do texto, antes de ele chegar ao banco.

Usado pelo `doerj_extrair.py`. Não é biblioteca geral: resolve o caso deste
projeto, que é publicar Diário Oficial sem republicar documento de pessoa.


POR QUE MASCARAR, SE A FONTE É PÚBLICA

O Diário é publicação oficial e o CPF está lá, à vista. A diferença é o que
acontece depois: um PDF por dia, que exige saber a data, é uma coisa. Um acervo
de anos, com busca por texto, é outra — o mesmo dado passa a permitir montar o
histórico de uma pessoa em segundos.

A LGPD trata dessa diferença. Publicidade legal não autoriza reuso ilimitado, e
tratamento de dado pessoal precisa de finalidade. A finalidade deste projeto é
transparência sobre **o que o Estado decidiu e gastou** — e para isso o CPF de
ninguém é necessário.

O nome do servidor fica. Nomeação, exoneração e designação são atos públicos, e
esconder o nome esvaziaria a transparência que motiva o projeto. O que sai é o
documento, que não acrescenta nada à fiscalização e acrescenta tudo ao risco.

O próprio IOERJ já publica CPF parcialmente mascarado em parte dos atos —
`041.XXX.127-96`. Mascarar por completo segue a mesma direção, e vai um passo
além.


ONDE O MASCARAMENTO ACONTECE, E POR QUE ALI

Na extração, antes de gravar o JSONL. O banco nunca vê o número.

É diferente de mascarar na tela. Mascarar na tela deixa o dado no banco, no
backup e no dump — e basta uma consulta mal feita, um relatório exportado ou um
vazamento de base para ele reaparecer. O que não se guarda não vaza.

O PDF original continua no IOERJ, com tudo. Quem tiver necessidade legítima e
base legal vai à fonte.
"""

from __future__ import annotations

import re

# "123.456.789-01", e também "041.XXX.127-96", que é como o próprio IOERJ
# publica parte dos CPFs. Mascarado pela metade ainda é dado pessoal: com o
# nome ao lado, os dígitos que sobram bastam para confirmar de quem se trata.
CPF_FORMATADO = re.compile(
    r"(?<![\dX*.])([\dX*]{3})\.([\dX*]{3})\.([\dX*]{3})-([\dX*]{2})(?![\dX*])",
    re.I,
)

# Onze dígitos seguidos podem ser CPF, mas também número de processo, matrícula
# ou telefone. Só o dígito verificador separa os dois, e é o que usamos.
ONZE_DIGITOS = re.compile(r"(?<!\d)(\d{11})(?!\d)")

# "RG nº 12.345.678-9", "RG 32.183 CBMERJ"
RG = re.compile(r"\b(RG|R\.G\.|IDENTIDADE)\s*n?[ºo°.]?\s*([\d][\d\.\-/]{4,})", re.I)

CPF_OCULTO = "***.***.***-**"
RG_OCULTO = "[documento omitido]"


def cpf_valido(digitos: str) -> bool:
    """Confere os dois dígitos verificadores do CPF.

    Serve para não mascarar o que não é CPF. Entre as 850 matérias das três
    primeiras edições há 349 sequências de onze dígitos, e a maioria é número de
    processo. Mascarar todas apagaria dado que o portal precisa mostrar.
    """
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(
            int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho)
        )
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[tamanho]):
            return False
    return True


def mascarar(texto: str | None) -> tuple[str | None, int]:
    """Devolve o texto sem documentos, e quantos foram ocultados.

    A contagem existe para haver registro: se um dia alguém perguntar quanto
    dado pessoal passou por aqui, a resposta não pode ser "sei lá".
    """
    if not texto:
        return texto, 0

    ocultados = 0

    def some_cpf(m: re.Match) -> str:
        nonlocal ocultados
        # Mascara mesmo quando o dígito verificador não fecha: o IOERJ às vezes
        # publica CPF já parcialmente oculto ou com erro de digitação, e nesses
        # casos o número continua sendo dado pessoal.
        ocultados += 1
        return CPF_OCULTO

    texto = CPF_FORMATADO.sub(some_cpf, texto)

    def some_onze(m: re.Match) -> str:
        nonlocal ocultados
        if not cpf_valido(m.group(1)):
            return m.group(0)
        ocultados += 1
        return CPF_OCULTO

    texto = ONZE_DIGITOS.sub(some_onze, texto)

    def some_rg(m: re.Match) -> str:
        nonlocal ocultados
        ocultados += 1
        return f"{m.group(1)} {RG_OCULTO}"

    texto = RG.sub(some_rg, texto)
    return texto, ocultados


def autoteste() -> int:
    # CPFs de teste, com dígito verificador correto, gerados para este teste.
    assert cpf_valido("52998224725")
    assert cpf_valido("11144477735")
    assert not cpf_valido("12345678901")
    assert not cpf_valido("11111111111")
    assert not cpf_valido("0000000000")

    t, n = mascarar("JANAÍNA DA SILVA CAPELLA, CPF nº 090.070.707-03, com validade")
    assert "090.070.707-03" not in t and CPF_OCULTO in t, t
    assert "JANAÍNA DA SILVA CAPELLA" in t, "o nome do servidor não podia sair"
    assert n == 1

    # Já mascarado na origem: continua saindo.
    t, n = mascarar("CPF 041.XXX.127-96, de acordo")
    assert "041" not in t, t

    # Onze dígitos que são CPF de verdade saem.
    t, n = mascarar("o servidor de CPF 52998224725 foi nomeado")
    assert "52998224725" not in t and n == 1, t

    # Onze dígitos que NÃO são CPF ficam: é número de processo.
    t, n = mascarar("Processo nº SEI-350001/020290/2026 e a matrícula 12345678901")
    assert "12345678901" in t, t
    assert n == 0, t

    # Número de menos de onze dígitos não é tocado.
    t, n = mascarar("ID FUNCIONAL Nº 4189721-8")
    assert "4189721-8" in t and n == 0, t

    # CNPJ é de empresa, não é dado pessoal, e fica.
    t, n = mascarar("CNPJ 33.000.167/0001-01 firmou contrato")
    assert "33.000.167/0001-01" in t and n == 0, t

    t, n = mascarar("CARDOSO BAPTISTA, RG 32.183 CBMERJ, Id Funcional 3137444-1")
    assert "32.183" not in t and RG_OCULTO in t, t
    assert "3137444-1" in t, "id funcional não é documento de identidade"

    assert mascarar(None) == (None, 0)
    assert mascarar("") == ("", 0)

    print("autoteste lgpd: tudo certo")
    return 0


if __name__ == "__main__":
    raise SystemExit(autoteste())
