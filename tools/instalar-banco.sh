#!/bin/bash
#
# Cria as tabelas e carrega os dados no banco, rodando NO SERVIDOR.
#
#   bash ~/doerj/instalar-banco.sh
#
# Lê a credencial do próprio `config.php`, que é onde ela já mora. Não recebe
# senha por argumento: argumento de linha de comando aparece em `ps` e no
# histórico do shell, e num servidor compartilhado isso é visível a todo mundo.

set -euo pipefail

CONFIG=~/doerj/config/config.php
BANCO_DIR=~/doerj-banco/_banco

ler() {
  php -r "\$c = require \"$CONFIG\"; echo \$c[\"banco\"][\"$1\"] ?? \"\";"
}

NOME=$(ler nome); USUARIO=$(ler usuario); SENHA=$(ler senha)

if [ -z "$SENHA" ]; then
  echo "A senha em $CONFIG está vazia." >&2
  echo "Crie o usuário do banco no cPanel, dê acesso a $NOME, e preencha a linha." >&2
  exit 1
fi

CNF=$(mktemp); chmod 600 "$CNF"
trap 'rm -f "$CNF"' EXIT

# A senha vai ENTRE ASPAS.
#
# Sem elas, o formato `.cnf` trata `#` como início de comentário e corta a senha
# no meio. Aconteceu aqui: a senha reaproveitada tinha `#`, o MySQL respondeu
# "Access denied", e o erro não aponta para lugar nenhum — parecia senha errada,
# quando o que estava errado era o arquivo que a carregava.
printf '[client]\nuser=%s\npassword="%s"\nhost=localhost\n' "$USUARIO" "$SENHA" > "$CNF"

echo "Conferindo o acesso a $NOME..."
mysql --defaults-extra-file="$CNF" "$NOME" -e "SELECT 1" >/dev/null

echo "Criando as tabelas..."
mysql --defaults-extra-file="$CNF" "$NOME" < "$BANCO_DIR/instalar.sql"

echo "Carregando os dados..."
gunzip -c "$BANCO_DIR/dados.sql.gz" | mysql --defaults-extra-file="$CNF" "$NOME"

echo
echo "Conferência:"
mysql --defaults-extra-file="$CNF" "$NOME" -e "
SELECT (SELECT COUNT(*) FROM atos) AS atos,
       (SELECT COUNT(*) FROM ato_natureza) AS classificacoes,
       (SELECT COUNT(*) FROM ato_relacoes) AS relacoes,
       (SELECT COUNT(*) FROM edicoes) AS edicoes;"
echo
echo "Esperado hoje: 2012 atos, 3099 classificações, 23 relações, 8 edições."
