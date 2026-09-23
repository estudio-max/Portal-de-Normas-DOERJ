"""Monta `outputs/publicar-doerj.zip`, com tudo que vai para a hospedagem.

    python tools/gerar_pacote.py

Roda depois do `gerar_instalador.py` e do `gerar_dump.py`, que produzem as duas
peças do banco.


POR QUE UM PACOTE, E NÃO UMA LISTA DE ARQUIVOS

Publicação por painel de hospedagem é feita clicando, e escolher arquivo por
arquivo numa árvore de diretórios é onde alguém esquece um. O pacote tem a
estrutura certa dentro: basta descompactar no lugar.

E, mais importante, ele diz o que **não** vai. `tools/` e `docs/` ficam de
fora: são para quem mantém, não para quem visita. O que não está no servidor
não pode ser servido por engano — e essa é uma barreira melhor que qualquer
regra de `.htaccess`.

`config/config.php` também fica de fora, e por outro motivo: é onde mora a
senha do banco. Vai o `config.exemplo.php`, que se copia no servidor.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "outputs" / "publicar-doerj.zip"

# (origem no repositório, destino dentro do pacote)
#
# O prefixo `_banco/` separa o que sobe para o site do que roda no phpMyAdmin.
# Sem ele, alguém sobe o `instalar.sql` junto com o resto e deixa o esquema do
# banco acessível pela web.
CONTEUDO = [
    ("app", "app"),
    ("public", "public"),
    ("config/config.exemplo.php", "config/config.exemplo.php"),
    # O conteúdo da área interna. Não entra no git (DP-03), mas o servidor
    # precisa dele, e o pacote viaja por SCP e fica fora da pasta pública.
    # A proteção da pasta `interno/` NÃO vai no pacote: é o cPanel que
    # escreve aquele `.htaccess`, e um pacote que levasse um apagaria a senha.
    ("config/interno.php", "config/interno.php"),
    ("backend/db/instalar.sql", "_banco/instalar.sql"),
    ("outputs/dados.sql.gz", "_banco/dados.sql.gz"),
    # O instalador vai junto. Ficou de fora até 2026-09-23, e o resultado foi
    # uma publicação em que o servidor rodou a versão anterior do script: ele
    # contava linhas `INSERT` para conferir a carga, o dump passara a usar
    # INSERT estendido, e a conferência anunciou 20 atos onde havia 50.062.
    # Script de instalação que não viaja com o que instala envelhece sozinho.
    ("tools/instalar-banco.sh", "_banco/instalar-banco.sh"),
    ("docs/publicacao.md", "_banco/LEIA-ME-publicacao.md"),
]


def montar() -> int:
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    faltando = []

    with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for origem, destino in CONTEUDO:
            o = RAIZ / origem
            if o.is_dir():
                for f in sorted(o.rglob("*")):
                    if f.is_file():
                        interno = f"{destino}/{f.relative_to(o)}".replace("\\", "/")
                        z.write(f, interno)
            elif o.is_file():
                z.write(o, destino)
            else:
                faltando.append(origem)

    if faltando:
        print("Faltou gerar antes:", file=sys.stderr)
        for f in faltando:
            if f.endswith("interno.php"):
                print(f"  {f} — copie de config/interno.exemplo.php e preencha", file=sys.stderr)
                continue
            ferramenta = ("tools/gerar_dump.py" if f.endswith(".gz")
                          else "tools/gerar_instalador.py")
            print(f"  {f} — rode {ferramenta}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(SAIDA) as z:
        arquivos = len(z.namelist())
    print(f"{SAIDA.relative_to(RAIZ)}")
    print(f"  {arquivos} arquivos, {SAIDA.stat().st_size / 1024 / 1024:.1f} MB")
    print("  O roteiro está em _banco/LEIA-ME-publicacao.md, dentro do pacote.")
    return 0


if __name__ == "__main__":
    raise SystemExit(montar())
