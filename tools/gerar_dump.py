"""Gera o dump dos dados para levar à hospedagem.

    python tools/gerar_dump.py
    python tools/gerar_dump.py --saida outputs/

Escreve `outputs/dados.sql.gz`, só com os dados — o esquema vai no
`backend/db/instalar.sql`, que é gerado à parte.

Ligação pelo ambiente, igual às outras ferramentas: `DOERJ_HOST`, `DOERJ_PORT`,
`DOERJ_USER`, `DOERJ_SENHA`, `DOERJ_BANCO`.


POR QUE DUMP, E NÃO CARREGAR DIRETO NO SERVIDOR

MySQL de hospedagem compartilhada quase nunca aceita conexão de fora: é preciso
liberar o endereço de rede no painel, e o endereço de quem trabalha de casa
muda sozinho. Dump é o caminho que funciona sem depender disso — sobe pelo
phpMyAdmin e pronto.


AS OPÇÕES DO mysqldump, E POR QUE CADA UMA

Três delas existem para o dump **não falhar em hospedagem compartilhada**, e é
o tipo de coisa que só se descobre quando falha:

- `--set-gtid-purged=OFF` — sem isto o dump inclui um `SET @@GLOBAL.gtid_purged`,
  que exige privilégio de administrador. O phpMyAdmin recusa a importação
  inteira por causa de uma linha no começo.
- `--no-tablespaces` — o dump pediria `PROCESS`, que usuário de hospedagem
  compartilhada não tem.
- `--no-create-info` — o esquema vem do instalador. Dump com `CREATE TABLE`
  sobrescreveria as migrações e levaria junto as particularidades da versão do
  MySQL local, que não é a mesma do servidor.

E duas para o dia em que der errado:

- `--complete-insert` — cada `INSERT` nomeia as colunas, então ele sobrevive a
  uma coluna nova no meio da tabela.
- `--skip-extended-insert` — uma linha por `INSERT`. O arquivo fica maior, mas
  quando uma linha falha o erro diz qual é. Com `INSERT` estendido, a mensagem
  aponta para um bloco de mil linhas.
"""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

OPCOES = [
    "--default-character-set=utf8mb4",
    "--no-create-info",
    "--complete-insert",
    "--skip-extended-insert",
    "--single-transaction",
    "--set-gtid-purged=OFF",
    "--no-tablespaces",
]


def achar_mysqldump() -> str:
    achado = os.environ.get("DOERJ_MYSQLDUMP") or shutil.which("mysqldump")
    if achado:
        return achado
    # O caminho comum no Windows, onde o instalador não mexe no PATH.
    for padrao in Path("C:/Program Files/MySQL").glob("*/bin/mysqldump.exe"):
        return str(padrao)
    sys.exit("Não achei o mysqldump. Aponte DOERJ_MYSQLDUMP para ele.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--saida", type=Path, default=RAIZ / "outputs")
    o = p.parse_args()
    o.saida.mkdir(parents=True, exist_ok=True)

    banco = os.environ.get("DOERJ_BANCO", "doerj")
    comando = [
        achar_mysqldump(),
        "-u", os.environ.get("DOERJ_USER", "root"),
        "-h", os.environ.get("DOERJ_HOST", "127.0.0.1"),
        "-P", os.environ.get("DOERJ_PORT", "3306"),
    ]
    if os.environ.get("DOERJ_SENHA"):
        comando.append("-p" + os.environ["DOERJ_SENHA"])
    comando += OPCOES + [banco]

    bruto = o.saida / "dados.sql"
    with bruto.open("wb") as destino:
        resultado = subprocess.run(comando, stdout=destino, stderr=subprocess.PIPE)
    if resultado.returncode != 0:
        bruto.unlink(missing_ok=True)
        sys.exit("mysqldump falhou:\n" + resultado.stderr.decode(errors="replace")[:600])

    comprimido = o.saida / "dados.sql.gz"
    with bruto.open("rb") as f, gzip.open(comprimido, "wb", 9) as g:
        shutil.copyfileobj(f, g)
    bruto.unlink()

    print(f"{comprimido.relative_to(RAIZ)}")
    print(f"  {comprimido.stat().st_size / 1024 / 1024:.1f} MB compactado")
    print("  Sobe pelo phpMyAdmin, depois do backend/db/instalar.sql.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
