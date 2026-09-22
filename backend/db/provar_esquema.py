"""Prova o esquema contra um MySQL de verdade, com dado real do Diário.

    python backend/db/provar_esquema.py

Aplica `001-esquema.sql` num banco descartável, insere edições e decretos de
verdade, e roda as consultas que o portal vai precisar fazer. **Apaga e recria o
banco que receber**, então aponte para um banco de teste.

A configuração vem do ambiente, com padrão de desenvolvimento local:

    DOERJ_MYSQL   caminho do cliente mysql, se ele não estiver no PATH
    DOERJ_HOST    127.0.0.1
    DOERJ_PORT    3306
    DOERJ_USER    root
    DOERJ_SENHA   vazia
    DOERJ_BANCO   doerj_teste

Fala com o cliente de linha de comando em vez de usar um driver. É teste de
esquema, não de aplicação: o que importa é o que o servidor aceita, e um driver
a mais seria dependência para não ganhar nada.

O que este teste responde, e é por isso que ele existe:

- a chave única barra edição repetida, mas deixa passar a edição extra do mesmo
  dia, que acontece de verdade;
- a busca em texto livre acha por assunto, com acento;
- dá para registrar "revoga o Decreto nº 45.452" antes de saber qual registro é
  esse, que é como a curadoria de fato acontece;
- apagar um ato leva junto o corpo e as relações, sem deixar órfão.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

MYSQL = os.environ.get("DOERJ_MYSQL") or shutil.which("mysql")
if not MYSQL:
    sys.exit("Não achei o cliente mysql. Ponha no PATH ou aponte DOERJ_MYSQL para ele.")

BANCO = os.environ.get("DOERJ_BANCO", "doerj_teste")
LIGACAO = [
    MYSQL,
    "-u", os.environ.get("DOERJ_USER", "root"),
    "-h", os.environ.get("DOERJ_HOST", "127.0.0.1"),
    "-P", os.environ.get("DOERJ_PORT", "3306"),
]
if os.environ.get("DOERJ_SENHA"):
    LIGACAO.append("-p" + os.environ["DOERJ_SENHA"])
ARGS = LIGACAO + [BANCO]

ESQUEMA = Path(__file__).resolve().parent / "001-esquema.sql"


def roda(sql, esperar_erro=False):
    r = subprocess.run(
        ARGS + ["--default-character-set=utf8mb4", "-e", sql],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if esperar_erro:
        if r.returncode == 0:
            print("  FALHOU: o banco aceitou o que devia recusar")
            sys.exit(1)
        return r.stderr.strip().splitlines()[0] if r.stderr else ""
    if r.returncode != 0:
        print("  ERRO:", r.stderr.strip()[:400])
        sys.exit(1)
    return r.stdout


BASE = "https://www.ioerj.com.br/portal/modules/conteudoonline/mostra_edicao.php?k="


def url(guid):
    return BASE + guid[:12] + "P" + guid[12:]


print(f"=== recriando o banco {BANCO} e aplicando o esquema ===")
inicial = subprocess.run(
    LIGACAO + ["-e", f"DROP DATABASE IF EXISTS {BANCO}; CREATE DATABASE {BANCO} "
               "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"],
    capture_output=True, text=True,
)
if inicial.returncode != 0:
    sys.exit("Não consegui falar com o MySQL:\n" + inicial.stderr.strip()[:400])

with ESQUEMA.open("rb") as f:
    aplicar = subprocess.run(ARGS, stdin=f, capture_output=True, text=True)
if aplicar.returncode != 0:
    sys.exit("O esquema não aplicou:\n" + aplicar.stderr.strip()[:600])
print("  esquema aplicado")

print("=== inserindo as tres edicoes reais coletadas hoje ===")
edicoes = [
    ("2026-09-18", "LII", "171", "F6A0FDFE-0000-0000-0000-000000000171", 81, 6647040),
    ("2026-09-21", "LII", "172", "A1B2C3D4-0000-0000-0000-000000000172", 70, 4897792),
    ("2026-09-22", "LII", "173", "B8EA790C-E3E3-4518-BD90-0E237E54B7CA", 41, 2685505),
]
for data, ano_r, num, guid, pags, bytes_ in edicoes:
    sha = "9d738c2396775f77df4a8d1651be2d4cb1c3843d53838b54b6667e3516c4234a" if num == "173" else "NULL"
    sha_sql = f"'{sha}'" if sha != "NULL" else "NULL"
    roda(
        "INSERT INTO edicoes (data_pub, caderno, caderno_slug, ano_romano, numero, "
        f"guid, url_pdf, paginas, bytes, sha256) VALUES ('{data}', "
        "'Parte I (Poder Executivo)', 'parte-i-poder-executivo', "
        f"'{ano_r}', '{num}', '{guid}', '{url(guid)}', {pags}, {bytes_}, {sha_sql});"
    )
print("  3 edicoes")

print("=== a chave unica barra edicao repetida? ===")
erro = roda(
    "INSERT INTO edicoes (data_pub, caderno, caderno_slug, guid, url_pdf) VALUES "
    "('2026-09-22', 'Parte I (Poder Executivo)', 'parte-i-poder-executivo', "
    "'11111111-2222-3333-4444-555555555555', 'http://x');",
    esperar_erro=True,
)
print("  barrou:", erro[:90])

print("=== mas aceita a edicao extra do mesmo dia, com sequencia 2 ===")
roda(
    "INSERT INTO edicoes (data_pub, caderno, caderno_slug, sequencia, guid, url_pdf) VALUES "
    "('2026-09-22', 'Parte I (Poder Executivo)', 'parte-i-poder-executivo', 2, "
    "'11111111-2222-3333-4444-555555555555', 'http://x');"
)
print("  aceitou")

print("=== inserindo tres decretos reais do Diario de hoje ===")
atos = [
    (
        "2026-09-22-decreto-50483",
        "50.483",
        "Regulamenta a Lei nº 11.236, de 22 de junho de 2026, que dispõe sobre a "
        "distribuição da cota-parte do ICMS.",
        "Governo do Estado do Rio de Janeiro",
    ),
    (
        "2026-09-22-decreto-50484",
        "50.484",
        "Declaração de utilidade pública, para fins de desapropriação, do terreno "
        "que menciona no município de Miguel Pereira.",
        "Governo do Estado do Rio de Janeiro",
    ),
    (
        "2026-09-22-decreto-50485",
        "50.485",
        "Revoga o Decreto nº 45.452, de 17 de novembro de 2015, e dá outras "
        "providências.",
        "Governo do Estado do Rio de Janeiro",
    ),
]
eid = roda("SELECT id FROM edicoes WHERE numero='173' AND sequencia=1;").split()[-1]
for aid, num, ementa, orgao in atos:
    ementa_sql = ementa.replace("'", "''")
    roda(
        "INSERT INTO atos (id, edicao_id, tipo, numero, ano, data_ato, data_pub, "
        "orgao, orgao_slug, ementa) VALUES "
        f"('{aid}', {eid}, 'Decreto', '{num}', 2026, '2026-09-21', '2026-09-22', "
        f"'{orgao}', 'governo-do-estado', '{ementa_sql}');"
    )
    roda(
        f"INSERT INTO ato_corpo (ato_id, texto) VALUES ('{aid}', "
        f"'{ementa_sql} O GOVERNADOR DO ESTADO DO RIO DE JANEIRO, EM EXERCÍCIO, "
        "no uso das suas atribuições constitucionais e legais, DECRETA:');"
    )
print("  3 atos, com corpo")

print("=== a norma revogada, de 2015, e a relacao ===")
roda(
    "INSERT INTO atos (id, tipo, numero, ano, data_pub, orgao_slug, ementa, status) VALUES "
    "('2015-11-18-decreto-45452', 'Decreto', '45.452', 2015, '2015-11-18', "
    "'governo-do-estado', 'Afeta ao uso exclusivo do Tribunal de Justiça o imóvel que menciona.', "
    "'Revogado');"
)
roda(
    "INSERT INTO ato_relacoes (ato_id, tipo_relacao, ato_destino_texto, ato_destino_id) VALUES "
    "('2026-09-22-decreto-50485', 'Revoga', 'Decreto nº 45.452, de 17 de novembro de 2015', "
    "'2015-11-18-decreto-45452');"
)
# Relacao que ainda nao se sabe para quem aponta: tem que ser aceita assim.
roda(
    "INSERT INTO ato_relacoes (ato_id, tipo_relacao, ato_destino_texto, externo) VALUES "
    "('2026-09-22-decreto-50483', 'Regulamenta', 'Lei nº 11.236, de 22 de junho de 2026', 1);"
)
print("  2 relacoes, uma resolvida e uma ainda em prosa")

print()
print("=== AGORA AS CONSULTAS QUE O PORTAL FARIA ===")
print()

print("1. Busca por assunto, em texto livre:")
print(roda(
    "SELECT id, numero, LEFT(ementa, 60) AS ementa FROM atos "
    "WHERE MATCH(ementa) AGAINST('desapropriação' IN NATURAL LANGUAGE MODE);"
))

print("2. Busca dentro do corpo do ato:")
print(roda(
    "SELECT ato_id FROM ato_corpo "
    "WHERE MATCH(texto) AGAINST('GOVERNADOR EXERCÍCIO' IN NATURAL LANGUAGE MODE) LIMIT 3;"
))

print("3. Por numero, que e como servidor procura:")
print(roda("SELECT id, tipo, numero, data_pub, status FROM atos WHERE numero='50.485';"))

print("4. 'Essa norma ainda vale?' — o que revogou o Decreto 45.452:")
print(roda(
    "SELECT d.id AS revogado, d.status, r.tipo_relacao, o.id AS por_qual, o.data_pub "
    "FROM atos d "
    "JOIN ato_relacoes r ON r.ato_destino_id = d.id "
    "JOIN atos o ON o.id = r.ato_id "
    "WHERE d.id = '2015-11-18-decreto-45452';"
))

print("5. O ato com o link do PDF na origem:")
print(roda(
    "SELECT a.id, a.numero, e.data_pub, e.paginas, e.url_pdf "
    "FROM atos a JOIN edicoes e ON e.id = a.edicao_id WHERE a.numero='50.485';"
))

print("6. Relacoes ainda nao resolvidas, que e a fila de curadoria:")
print(roda(
    "SELECT ato_id, tipo_relacao, ato_destino_texto FROM ato_relacoes "
    "WHERE ato_destino_id IS NULL;"
))

print("7. Edicoes ainda sem extracao, que e a fila da Fase 4:")
print(roda("SELECT data_pub, numero FROM edicoes WHERE extraido_em IS NULL ORDER BY data_pub;"))

print("=== apagar o ato leva o corpo e a relacao junto? ===")
antes = roda("SELECT COUNT(*) FROM ato_corpo;").split()[-1]
roda("DELETE FROM atos WHERE id='2026-09-22-decreto-50483';")
depois = roda("SELECT COUNT(*) FROM ato_corpo;").split()[-1]
orfas = roda("SELECT COUNT(*) FROM ato_relacoes WHERE ato_id='2026-09-22-decreto-50483';").split()[-1]
print(f"  ato_corpo: {antes} -> {depois}, relacoes orfas: {orfas}")
assert int(depois) == int(antes) - 1 and orfas == "0", "o CASCADE nao funcionou"

print()
print("TUDO PASSOU")
