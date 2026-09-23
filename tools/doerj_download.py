"""Baixa o PDF do Diário Oficial do Estado do Rio de Janeiro.

    python tools/doerj_download.py --inicio 2026-09-22
    python tools/doerj_download.py --inicio 2026-09-01 --fim 2026-09-22
    python tools/doerj_download.py --inicio 2026-09-22 --todos

Grava em `dados/AAAA/MM/AAAA-MM-DD-<caderno>.pdf`. Só a biblioteca padrão.


COMO O SITE FUNCIONA, porque não é óbvio e custou caro descobrir
---------------------------------------------------------------

São três passos, e o terceiro é uma pequena charada:

1. `do_seleciona_edicao.php?data=<base64 de AAAAMMDD>` devolve o HTML com a
   lista de cadernos do dia.

2. Cada caderno vem como `mostra_edicao.php?session=<token>`. O token é
   **base64 aplicado três vezes** sobre `<GUID><timestamp>`. Três, não uma.

3. O GUID sozinho não baixa nada. A URL do arquivo é montada em JavaScript,
   dentro do `viewer-min.js`, e a montagem enfia uma letra **no meio do GUID**,
   na posição 12:

       k = guid[:12] + "P" + guid[12:]     -> o documento inteiro
       k = guid[:12] + "D" + guid[12:] + n -> só a página n

   O `P` e o `D` estão escritos no fonte como `String.fromCharCode(80)` e
   `String.fromCharCode(68)`, junto com o `?` e o `k=`. É ofuscação leve, do
   tipo que não impede ninguém e só custa tempo de quem está de boa fé.

O que o downloader NÃO faz: inventar o token. Ele lê o token da listagem, como
um navegador faria. O timestamp embutido sugere validade curta, e reconstruir
isso na mão seria adivinhar uma regra que o IOERJ pode mudar amanhã.


O 200 QUE NÃO É SUCESSO
-----------------------

`mostra_edicao.php` responde **200 com corpo vazio** para chave malformada, e
responde `Erro.` (5 bytes) quando não recebe chave nenhuma. Nas duas situações
o código HTTP é 200.

Por isso a conferência aqui é sobre o conteúdo: `Content-Type`, tamanho mínimo
e a assinatura `%PDF` nos primeiros bytes. Confiar no status faria esta
ferramenta gravar arquivos vazios em silêncio e escrever "ok" no log.


ESTE PDF NÃO TEM VALOR LEGAL
----------------------------

O próprio IOERJ nomeia o arquivo `Nao_Possui_Valor_Legal_*.pdf`. O que se baixa
aqui serve para consulta, busca e pesquisa. Não substitui a publicação oficial,
e o portal que for construído em cima disto precisa dizer isso na cara do
usuário, não num rodapé.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.cookiejar
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

BASE = "https://www.ioerj.com.br/portal/modules/conteudoonline"
NAVEGADOR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# Um Diário de verdade tem dezenas de páginas. Qualquer coisa menor que isto é
# página de erro disfarçada de PDF, ou PDF truncado.
TAMANHO_MINIMO = 20 * 1024

LINK = re.compile(
    r'<a[^>]*href="mostra_edicao\.php\?session=([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)


def chave(guid: str) -> str:
    """Monta o valor de `?k=` a partir do GUID. Ver o cabeçalho do arquivo."""
    return guid[:12] + "P" + guid[12:]


def guid_do_token(token: str) -> str:
    """Desembrulha as três camadas de base64 e devolve o GUID."""
    v = token
    for _ in range(3):
        v = base64.b64decode(v + "=" * (-len(v) % 4)).decode("ascii")
    return v[:36]


def apelido(nome: str) -> str:
    """'Parte I (Poder Executivo)' -> 'parte-i-poder-executivo'."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", sem_acento.lower())).strip("-")


def dias(inicio: date, fim: date):
    atual = inicio
    while atual <= fim:
        yield atual
        atual += timedelta(days=1)


class Ioerj:
    def __init__(self, intervalo: float = 2.0, tentativas: int = 3):
        self.intervalo = intervalo
        self.tentativas = tentativas
        self._ultima = 0.0
        biscoitos = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(biscoitos)
        )
        self.op.addheaders = [("User-Agent", NAVEGADOR)]

    def _buscar(self, url: str, referer: str | None = None):
        # Uma requisição por vez, com respiro entre elas. É um site de governo
        # estadual, e derrubá-lo encerraria o projeto.
        espera = self.intervalo - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)

        pedido = urllib.request.Request(url)
        if referer:
            pedido.add_header("Referer", referer)

        ultimo_erro = None
        for tentativa in range(1, self.tentativas + 1):
            try:
                with self.op.open(pedido, timeout=90) as r:
                    corpo, cabecalhos = r.read(), dict(r.headers)
                self._ultima = time.monotonic()
                return corpo, cabecalhos
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                ultimo_erro = e
                self._ultima = time.monotonic()
                if tentativa < self.tentativas:
                    time.sleep(self.intervalo * 2 * tentativa)
        raise RuntimeError(f"{url}: {ultimo_erro}")

    def cadernos(self, quando: date) -> list[tuple[str, str]]:
        """Os cadernos publicados na data, como (nome, GUID).

        Lista vazia significa dia sem edição, e isso é resposta normal: fim de
        semana e feriado não têm Diário.
        """
        d = base64.b64encode(quando.strftime("%Y%m%d").encode()).decode()
        corpo, _ = self._buscar(f"{BASE}/do_seleciona_edicao.php?data={d}")
        html = corpo.decode("latin-1")

        achados = []
        for token, rotulo in LINK.findall(html):
            nome = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", rotulo)).strip()
            try:
                achados.append((nome, guid_do_token(token)))
            except Exception:
                print(f"    token ilegível em {quando}, ignorado", file=sys.stderr)
        return achados

    def pdf(self, guid: str) -> bytes:
        corpo, cabecalhos = self._buscar(
            f"{BASE}/mostra_edicao.php?k={chave(guid)}",
            referer=f"{BASE}/do_seleciona_edicao.php",
        )

        tipo = cabecalhos.get("Content-Type", "")
        if "pdf" not in tipo.lower():
            raise ValueError(
                f"veio {tipo or 'sem tipo'} em vez de PDF, {len(corpo)} bytes"
            )
        if not corpo.startswith(b"%PDF"):
            raise ValueError(f"não começa com %PDF, {len(corpo)} bytes")
        if len(corpo) < TAMANHO_MINIMO:
            raise ValueError(f"só {len(corpo)} bytes, menos que o mínimo plausível")
        return corpo


def destino_de(raiz: Path, quando: date, nome: str, ja_vistos: dict[str, int]) -> Path:
    # Dias com edição extra repetem o nome do caderno. 2024-01-15 tem duas
    # "Parte I (Poder Executivo)". Numerar a partir da segunda mantém a
    # primeira com o nome limpo e não renomeia nada do que já está em disco.
    base = apelido(nome)
    ja_vistos[base] = ja_vistos.get(base, 0) + 1
    if ja_vistos[base] > 1:
        base = f"{base}-{ja_vistos[base]}"
    pasta = raiz / f"{quando:%Y}" / f"{quando:%m}"
    return pasta / f"{quando:%Y-%m-%d}-{base}.pdf"


def ja_baixado(caminho: Path) -> bool:
    """Idempotência: o cron repete, e vai repetir."""
    if not caminho.exists() or caminho.stat().st_size < TAMANHO_MINIMO:
        return False
    with caminho.open("rb") as f:
        return f.read(4) == b"%PDF"


def baixar(
    inicio: date, fim: date, raiz: Path, todos: bool, intervalo: float
) -> tuple[int, int, int]:
    io = Ioerj(intervalo=intervalo)
    gravados = pulados = falhas = 0

    for quando in dias(inicio, fim):
        try:
            disponiveis = io.cadernos(quando)
        except Exception as e:
            print(f"{quando}  FALHOU ao listar: {e}", file=sys.stderr)
            falhas += 1
            continue

        if not disponiveis:
            print(f"{quando}  sem edição")
            continue

        ja_vistos: dict[str, int] = {}
        for nome, guid in disponiveis:
            # O contador corre por todos os cadernos do dia, e não só pelos
            # escolhidos: assim o sufixo de edição extra não muda conforme o
            # filtro, e --todos e o padrão gravam a Parte I com o mesmo nome.
            caminho = destino_de(raiz, quando, nome, ja_vistos)
            if not todos and not apelido(nome).startswith("parte-i-poder-executivo"):
                continue

            if ja_baixado(caminho):
                print(f"{quando}  já tenho  {caminho.name}")
                pulados += 1
                continue

            try:
                conteudo = io.pdf(guid)
            except Exception as e:
                print(f"{quando}  FALHOU  {nome}: {e}", file=sys.stderr)
                falhas += 1
                continue

            # Grava ao lado e renomeia: assim uma interrupção no meio do
            # download não deixa meio PDF com o nome definitivo, que a próxima
            # execução leria como arquivo pronto.
            caminho.parent.mkdir(parents=True, exist_ok=True)
            parcial = caminho.with_suffix(".parcial")
            parcial.write_bytes(conteudo)
            parcial.replace(caminho)

            # A ficha ao lado do PDF. O GUID vive na listagem do IOERJ, e só
            # esta ferramenta o vê: o extrator recebe o arquivo, não a origem.
            # Sem isto, o portal não consegue montar o link de volta para a
            # fonte — e um acervo que não mostra de onde tirou cada coisa é
            # exatamente o que este projeto não quer ser.
            caminho.with_suffix(".json").write_text(
                json.dumps({
                    "guid": guid,
                    "url_pdf": f"{BASE}/mostra_edicao.php?k={chave(guid)}",
                    "caderno": nome,
                    "data_pub": quando.isoformat(),
                    "bytes": len(conteudo),
                    "sha256": hashlib.sha256(conteudo).hexdigest(),
                    "baixado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
                }, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            print(f"{quando}  {len(conteudo) / 1024:7.0f} KB  {caminho.name}")
            gravados += 1

    return gravados, pulados, falhas


def autoteste() -> int:
    """As partes que não dependem da rede, conferidas contra casos reais."""
    g = "B8EA790C-E3E3-4518-BD90-0E237E54B7CA"
    assert chave(g) == "B8EA790C-E3EP3-4518-BD90-0E237E54B7CA", chave(g)
    assert len(chave(g)) == 37

    # Token de verdade, capturado da listagem de 22/09/2026 (Parte II). Serve
    # para provar que as três camadas são mesmo três: com duas, sai base64; com
    # quatro, estoura.
    token = (
        "VDBSRk1GSnFXVEpSYWxGMFQwVldSRTU1TURCT1JHczBURlZHUlU1VVRYUlJl"
        "a1pHVVZSRk1GRlZUa1ZOVlVVd1RWUmpOVTFFUVRWTmVrVXpUbmM5UFE9PQ=="
    )
    assert guid_do_token(token) == "814F66B4-8EC7-4498-AD53-C1EA14ACD1A4"

    # E a volta: o token carrega GUID mais um timestamp Unix.
    embrulho = "B8EA790C-E3E3-4518-BD90-0E237E54B7CA1790093177"
    for _ in range(3):
        embrulho = base64.b64encode(embrulho.encode()).decode()
    assert guid_do_token(embrulho) == g, guid_do_token(embrulho)

    assert apelido("Parte I (Poder Executivo)") == "parte-i-poder-executivo"
    assert apelido("Parte V (Publicações a Pedido)") == "parte-v-publicacoes-a-pedido"
    assert apelido("Parte IB - (Tribunal de Contas)") == "parte-ib-tribunal-de-contas"

    vistos: dict[str, int] = {}
    raiz, dia = Path("dados"), date(2024, 1, 15)
    um = destino_de(raiz, dia, "Parte I (Poder Executivo)", vistos)
    dois = destino_de(raiz, dia, "Parte I (Poder Executivo)", vistos)
    assert um.name == "2024-01-15-parte-i-poder-executivo.pdf", um.name
    assert dois.name == "2024-01-15-parte-i-poder-executivo-2.pdf", dois.name
    assert um.parent == raiz / "2024" / "01"

    assert len(list(dias(date(2026, 9, 21), date(2026, 9, 23)))) == 3

    print("autoteste: tudo certo")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--inicio", help="data inicial, AAAA-MM-DD")
    p.add_argument("--fim", help="data final, AAAA-MM-DD. Em branco, usa a inicial")
    p.add_argument("--destino", default="dados", help="pasta de saída")
    p.add_argument(
        "--todos",
        action="store_true",
        help="baixa todos os cadernos, e não só a Parte I (Poder Executivo)",
    )
    p.add_argument(
        "--intervalo",
        type=float,
        default=2.0,
        help="segundos de espera entre requisições",
    )
    p.add_argument("--autoteste", action="store_true", help="confere a lógica e sai")
    o = p.parse_args()

    if o.autoteste:
        return autoteste()
    if not o.inicio:
        p.error("informe --inicio, ou --autoteste")

    try:
        inicio = date.fromisoformat(o.inicio)
        fim = date.fromisoformat(o.fim) if o.fim else inicio
    except ValueError as e:
        p.error(f"data inválida: {e}")

    if fim < inicio:
        p.error("a data final é anterior à inicial")

    gravados, pulados, falhas = baixar(
        inicio, fim, Path(o.destino), o.todos, o.intervalo
    )

    print()
    print(f"{gravados} gravado(s), {pulados} já existia(m), {falhas} falha(s)")

    # Falha vira código de saída para o cron e o GitHub Actions enxergarem.
    # Coletar nada também é falha quando havia dias úteis no intervalo, mas
    # quem decide isso é a conferência do fluxo, que sabe o calendário.
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
