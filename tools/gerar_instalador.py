"""Junta as migrações num `backend/db/instalar.sql` só.

    python tools/gerar_instalador.py

Hospedagem compartilhada costuma oferecer phpMyAdmin e nada mais. Subir seis
arquivos na ordem certa, por uma interface web, é onde alguém pula um e só
descobre três telas adiante — então existe um arquivo único para banco vazio.

Quem já tem o banco de pé continua aplicando as migrações uma a uma: o
instalador cria tabela, e `CREATE TABLE` em banco que já tem a tabela falha.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "backend" / "db"
DESTINO = PASTA / "instalar.sql"

CABECALHO = """-- Instalação completa do Portal de Normas DOERJ.
--
-- **Gerado de `backend/db/*.sql` por `tools/gerar_instalador.py`.** Não edite
-- à mão: mexa nas migrações e gere de novo, senão os dois divergem.
--
-- Para **banco vazio**, num arquivo só — é o que o phpMyAdmin da hospedagem
-- compartilhada aceita sem drama. Quem já tem o banco de pé aplica as
-- migrações uma a uma, na ordem do nome: o instalador cria tabela, e
-- `CREATE TABLE` em banco que já tem a tabela falha.
--
-- **Não cria o banco e não escolhe o banco.** Isso é do painel da hospedagem:
-- um `CREATE DATABASE` aqui falharia por falta de permissão ou, pior,
-- acertaria no banco errado.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
"""


def gerar() -> int:
    migracoes = sorted(PASTA.glob("[0-9]*.sql"))
    if not migracoes:
        raise SystemExit("Nenhuma migração em backend/db/.")

    partes = [CABECALHO]
    for m in migracoes:
        partes.append(f"\n\n-- {'=' * 72}\n-- {m.name}\n-- {'=' * 72}\n")
        partes.append(m.read_text(encoding="utf-8"))
    partes.append("\n\nSET FOREIGN_KEY_CHECKS = 1;\n")

    DESTINO.write_text("".join(partes), encoding="utf-8")
    print(f"{DESTINO.relative_to(RAIZ)}: {len(migracoes)} migrações, "
          f"{DESTINO.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(gerar())
