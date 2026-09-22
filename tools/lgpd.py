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

# Auto de infração traz nome, CPF e **endereço de casa** de um particular.
#
# O endereço só sai aqui dentro. Fora do auto, "ENDEREÇO:" é local de entrega de
# proposta, sala de sessão de licitação ou sede de empresa — informação que o
# portal precisa mostrar. Medido em 2.012 matérias: 20 autos com endereço, e 32
# outras ocorrências, todas institucionais.
AUTO_DE_INFRACAO = re.compile(
    r"AUTO DE INFRA[ÇC][ÃA]O|NOTIFICA[ÇC][ÃA]O DE INFRA[ÇC][ÃA]O|AUTO DE CONSTATA",
    re.I,
)

# "ENDEREÇO: Estrada Circuito da Gameleira nº. 1.100 - Barra do Imbuí INFRAÇÃO:"
# O campo acaba onde começa a próxima etiqueta em caixa alta.
#
# A etiqueta "ENDEREÇO" casa em qualquer caixa, mas **a detecção do fim do campo
# não pode ignorar caixa**: com `re.I`, "Barra do Imbuí INFRAÇÃO:" casava como
# se "Barra" fosse a próxima etiqueta, e metade do endereço sobrava na tela.
ENDERECO_DO_AUTO = re.compile(
    r"((?i:\bENDERE[ÇC]O)\s*:\s*)(.+?)(?=\s[A-ZÀ-Ü]{3,}[A-ZÀ-Ü\s/]{0,28}:|$)",
    re.S,
)

# Quem é o autuado aparece logo antes do endereço. Esta é a janela onde
# procurar, medida no formato que o INEA usa: "NOME: X CNPJ: Y ENDEREÇO: Z".
JANELA_DO_AUTUADO = 200

CNPJ = re.compile(r"\bCNPJ\b|\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", re.I)

# O CPF já foi mascarado quando esta conferência roda, então o que sobra para
# reconhecer pessoa natural é a máscara e a etiqueta.
CPF_NO_AUTO = re.compile(r"\bCPF\b|\*\*\*\.\*\*\*\.\*\*\*-\*\*", re.I)

CPF_OCULTO = "***.***.***-**"
RG_OCULTO = "[documento omitido]"
ENDERECO_OCULTO = "[endereço omitido]"


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

    # O endereço de casa só sai dentro de auto de infração. Fiscalização
    # ambiental e de trânsito não é o objeto deste portal, e o endereço
    # residencial de um particular não precisa ficar fácil de achar.
    #
    # A condição não é firula: fora do auto, "ENDEREÇO:" é onde se entrega
    # proposta de licitação ou onde é a sessão, e apagar isso tiraria do portal
    # informação que ele existe para mostrar.
    if AUTO_DE_INFRACAO.search(texto):
        def some_endereco(m: re.Match) -> str:
            nonlocal ocultados
            # **Endereço de empresa fica.** A LGPD protege pessoa natural, e
            # autuação ambiental contra empresa é exatamente o que o portal
            # existe para mostrar: esconder onde fica a fábrica autuada seria
            # proteger quem não precisa.
            #
            # Quem é autuado aparece logo antes do endereço, e o documento diz
            # o que é: CNPJ é empresa, CPF é pessoa. Quando os dois aparecem,
            # vale o mais protetivo.
            antes = texto[max(0, m.start() - JANELA_DO_AUTUADO):m.start()]
            if CNPJ.search(antes) and not CPF_NO_AUTO.search(antes):
                return m.group(0)
            ocultados += 1
            return f"{m.group(1)}{ENDERECO_OCULTO}"

        texto = ENDERECO_DO_AUTO.sub(some_endereco, texto)

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

    # --- endereço: sai no auto de infração, fica em todo o resto ---
    auto = ("INSTITUTO ESTADUAL DO AMBIENTE AUTO DE INFRAÇÃO Nº SUPPIBEAI/00133441 "
            "NOME: ADILSON AJARA VILLOTE CPF Nº 090.070.707-03 "
            "ENDEREÇO: Estrada Circuito da Gameleira nº. 1.100 - Barra do Imbuí "
            "INFRAÇÃO: Dar início a instalação sem licença ambiental")
    t, n = mascarar(auto)
    assert "Gameleira" not in t and "Barra do Imbuí" not in t, t
    assert ENDERECO_OCULTO in t, t
    # O que o portal precisa mostrar continua lá: o órgão, o número do auto e a
    # infração cometida. O nome também, porque autuação é ato público.
    assert "SUPPIBEAI/00133441" in t and "sem licença ambiental" in t, t
    assert "ADILSON AJARA VILLOTE" in t, t
    assert n == 2, (n, t)

    # Empresa autuada: o endereço fica. Autuação ambiental contra empresa é o
    # que o portal existe para mostrar, e CNPJ não é dado pessoal.
    empresa = ("AUTO DE INFRAÇÃO Nº SUPBGEAI/00160933 "
               "NOME: J.J.A. 2007 COMÉRCIO DE PRODUTOS QUÍMICOS LTDA - ME. "
               "CNPJ: 08.532.150/0001-58. ENDEREÇO: Rua Sabará, Lotes 5 e 6 "
               "DESCRIÇÃO: Por destinar bombonas com resíduos perigosos")
    t, n = mascarar(empresa)
    assert "Rua Sabará" in t, t
    assert n == 0, (n, t)

    # Prefeitura também é pessoa jurídica.
    orgao = ("AUTO DE INFRAÇÃO Nº SUPBGEAI/00150201 NOME: Prefeitura Municipal de "
             "Itaboraí CNPJ Nº: 28.741.080/0001-55. ENDEREÇO: Praça Marechal Floriano "
             "INFRAÇÃO: Artigo 76 da Lei nº 3.467")
    t, n = mascarar(orgao)
    assert "Praça Marechal Floriano" in t, t

    # Quando aparecem os dois rótulos, vale o mais protetivo.
    ambos = ("AUTO DE CONSTATAÇÃO CONVOCA: NOME: CARLOS ARTHUR ROALE MARTINS "
             "CNPJ/CPF Nº: 090.070.707-03 ENDEREÇO: Rua das Flores, 42 CONVOCA:")
    t, n = mascarar(ambos)
    assert "Rua das Flores" not in t, t

    # Endereço institucional fica, porque é o que o portal existe para mostrar.
    for institucional in (
        "entrega no setor de licitações, no endereço: Estrada do Caricó, 111, Galeão",
        "DATA DA SESSÃO: 21/06/2018 ENDEREÇO: Av. Padre Leonel Franca, n° 248",
        "AETEC CNPJ nº: 12.517.650/0001-98 Endereço: Rua Anita Peçanha, número 100",
    ):
        t, n = mascarar(institucional)
        assert t == institucional and n == 0, (n, t)

    assert mascarar(None) == (None, 0)
    assert mascarar("") == ("", 0)

    print("autoteste lgpd: tudo certo")
    return 0


if __name__ == "__main__":
    raise SystemExit(autoteste())
