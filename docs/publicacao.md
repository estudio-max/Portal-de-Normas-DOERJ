# Publicação

**Endereço:** `https://doerj.fanara.com.br`, HostGator, hospedagem particular do
responsável técnico.

**Estado:** o domínio existe; o portal não. No ar está uma página de espera e,
mais importante, a **recusa de indexação**, que precisa estar de pé antes de
qualquer conteúdo — desindexar depois é lento e incompleto.

> **Não é publicação oficial.** É o mesmo caso do Mapa de CT&I: publicar em nome
> do órgão é ato do órgão. Enquanto a SECTI-RJ não definir o ambiente
> definitivo, este endereço é homologação, e a página deve dizer isso a quem
> chega.

---

## O que já está pronto para subir

| Arquivo | O que faz |
|---|---|
| `public/.htaccess` | HTTPS obrigatório, front controller, cabeçalhos de segurança e **`X-Robots-Tag: noindex`** |
| `public/robots.txt` | pede que o buscador não rastreie |
| `public/index.php` | página de espera, e 404 para endereço inventado |

Conferido com o servidor embutido do PHP: `/` responde 200, `/qualquer-coisa`
responde 404, `/robots.txt` responde 200 em `text/plain`.

## Por que os dois, robots.txt e cabeçalho

Fazem coisas diferentes, e só o segundo resolve o que importa.

`robots.txt` pede que o buscador **não visite**. Mas uma URL que apareça num
link de terceiro pode ser indexada sem nunca ter sido visitada — o buscador
registra o endereço a partir do link. `X-Robots-Tag: noindex` chega junto com a
resposta e pede que **não indexe**, que é outra coisa.

O cabeçalho está no `.htaccess` e repetido no `index.php`. Do `.htaccess` ele
cobre arquivo estático, que não passa pelo PHP. Do `index.php` ele sobrevive a
um servidor sem `mod_headers` ou que ignore `.htaccess`.

**E uma coisa que precisa estar dita:** nada disso é cadeado. Buscador que
respeita a convenção obedece; raspador que não quiser obedecer não obedece. Não
indexar reduz alcance, não é proteção. A proteção de verdade foi feita antes, na
extração: CPF, documento de identidade e endereço residencial de particular não
chegam a entrar no banco.

---

## Como subir

Não há automação ainda, e é só um punhado de arquivos. Pelo Gerenciador de
Arquivos do cPanel ou por FTP:

```
public_html/
├── .htaccess
├── robots.txt
└── index.php
```

Depois, conferir no navegador:

```bash
curl -sI https://doerj.fanara.com.br | grep -i "x-robots-tag\|strict-transport"
curl -s  https://doerj.fanara.com.br/robots.txt
curl -so /dev/null -w "%{http_code}\n" https://doerj.fanara.com.br/pagina-que-nao-existe
```

O terceiro tem que responder 404. Se responder 200, o front controller está
devolvendo a página de espera para qualquer endereço, e aí cada URL inventada
vira uma página a mais.

---

## O que falta decidir antes do portal de verdade

| # | Pergunta |
|---|---|
| DP-10 | Onde o banco de produção mora, e quem faz backup |
| DP-03 | O repositório continua privado |
| DP-07 | Como a tela diz que o PDF de origem não tem valor legal |

E um limite que precisa aparecer na tela, não só na documentação: **o Diário
publica movimentação orçamentária, não o orçamento.** Um número que pareça ser o
total e não seja, lido por órgão de controle, custa mais caro que número nenhum.

---

## Requisitos do servidor, quando o portal existir

Herdados do Mapa de CT&I, que roda na mesma hospedagem:

| Item | Mínimo |
|---|---|
| PHP | 8.2 |
| Extensões | `pdo_mysql`, `mbstring`, `json` |
| MySQL / MariaDB | 5.7 / 10.4 |
| `mod_rewrite` | ativo |
| `mod_headers` | ativo — sem ele o `noindex` do `.htaccess` não sai |

O ideal é apontar o document root para `public/`, com o resto do repositório um
nível acima e fora do alcance do navegador. Quando o provedor não permitir,
`public/` vira `public_html/`. O `.htaccess` nega `.md`, `.sql`, `.py`, `.jsonl`
e `.csv` como segunda barreira — **a primeira é a estrutura de diretórios.**

### Credenciais

Senha de banco e de FTP não entram no repositório, não entram em documentação e
não passam por aqui. Ficam no `config/config.php`, que é criado no servidor a
partir do exemplo e nunca versionado.
