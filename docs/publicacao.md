# Publicação

**Endereço:** `https://doerj.fanara.com.br`, HostGator, hospedagem particular
do responsável técnico.
**Banco:** `fanara87_doerj`.

> **Não é publicação oficial.** É o mesmo caso do Mapa de CT&I: publicar em
> nome do órgão é ato do órgão. Enquanto a SECTI-RJ não definir o ambiente
> definitivo, este endereço é homologação, e o rodapé diz isso a quem chega.

---

## O que sobe

| O quê | Onde |
|---|---|
| `public/` inteiro | vira o document root — `.htaccess`, `index.php`, `assets/` |
| `app/` | um nível **acima** do document root |
| `config/config.php` | criado no servidor, a partir do exemplo |
| `backend/db/instalar.sql` | roda no phpMyAdmin, não sobe para o site |
| `outputs/dados.sql.gz` | idem |

**`tools/` e `docs/` não precisam ir.** São para quem mantém, não para quem
visita, e o que não está no servidor não pode ser servido por engano.

---

## Como está publicado hoje

Publicado por SSH em 2026-09-23. O acesso é por chave — `hostgator-fanara` no
`~/.ssh/config`, usuário `fanara87`, porta 2222.

```
/home1/fanara87/
├─ doerj/                    o projeto
│  ├─ app/                   fora do alcance do navegador
│  ├─ config/config.php      a senha mora só aqui, com permissão 600
│  ├─ public/                servido
│  └─ instalar-banco.sh      cria as tabelas e carrega os dados
├─ doerj-banco/_banco/       instalar.sql e dados.sql.gz
└─ doerj.fanara.com.br  ->   /home1/fanara87/doerj/public
```

**O document root é um link** para `doerj/public`. Assim a estrutura do
repositório fica intacta no servidor, e `app/` e `config/` ficam fora do
alcance do navegador sem precisar de regra nenhuma.

O `.well-known` que estava no document root foi **movido para dentro de
`doerj/public/`**, e não apagado: é por ele que o certificado SSL se renova.
A pasta original virou `doerj.fanara.com.br.anterior`, e pode ser removida
depois que o certificado renovar uma vez sem problema.

### O que falta, e é decisão de quem tem a senha

Criar o usuário MySQL no cPanel, dar acesso a `fanara87_doerj`, e preencher a
linha `"senha"` em `~/doerj/config/config.php`. Depois:

```bash
bash ~/doerj/instalar-banco.sh
```

O script lê a credencial do próprio `config.php` e passa ao MySQL por arquivo
temporário com permissão 600, apagado ao fim aconteça o que acontecer — **senha
em linha de comando fica no histórico do shell e na lista de processos da
máquina**, visível a qualquer outro usuário do servidor compartilhado.

### Uma pendência de faxina

Existem **dois** bancos vazios: `fanara87_doerj` e `fanara87_dourj`. O segundo
tem o nome trocado e não é usado. Apagar é decisão de quem criou — está aqui
para não ser esquecido.

---

## Roteiro, para quem for refazer do zero


### 1. O banco

Pelo painel: criar `fanara87_doerj` com `utf8mb4` e
`utf8mb4_unicode_ci`, e um usuário com acesso a ele.

No phpMyAdmin, **nesta ordem**:

1. `backend/db/instalar.sql` — cria as seis tabelas
2. `outputs/dados.sql.gz` — 1,4 MB compactado, e o phpMyAdmin aceita `.gz`

Conferir depois:

```sql
SELECT (SELECT COUNT(*) FROM atos) AS atos,
       (SELECT COUNT(*) FROM ato_natureza) AS classificacoes,
       (SELECT COUNT(*) FROM edicoes) AS edicoes;
```

Hoje isso dá **2.012, 3.099 e 8**. Número diferente quer dizer importação
incompleta, e vale refazer em vez de seguir com o acervo pela metade.

### 2. Os arquivos

O ideal é apontar o document root para `public/`, com o resto um nível acima:

```
/home/fanara87/
├─ doerj/
│  ├─ app/            ← fora do alcance do navegador
│  ├─ config/
│  └─ public/         ← document root aponta para cá
```

Quando o provedor não permitir mudar o document root, `public/` vira
`public_html/` e `app/` e `config/` ficam ao lado, fora dele. O `.htaccess`
nega `.md`, `.sql`, `.py`, `.jsonl` e `.csv` como segunda barreira — **a
primeira é a estrutura de diretórios, e é nela que se confia.**

### 3. A configuração

```bash
cp config/config.exemplo.php config/config.php
```

Preencher o banco, e deixar:

```php
'ambiente' => 'producao',
'debug'    => false,
```

`debug => true` em produção mostra a mensagem do erro na tela, e mensagem de
erro conta ao visitante detalhes do servidor que não são da conta dele.

**A senha fica só ali.** Não entra no repositório — `config/config.php` está no
`.gitignore` —, não entra em documentação e não passa por conversa.

### 4. Conferir

```bash
curl -sI https://doerj.fanara.com.br | grep -i "x-robots-tag\|strict-transport"
curl -so /dev/null -w "%{http_code}\n" https://doerj.fanara.com.br/pagina-que-nao-existe
curl -s https://doerj.fanara.com.br/busca?q=decreto | grep -c resultado__titulo
```

O segundo tem que dar **404**. Se der 200, o front controller está devolvendo
página para qualquer endereço, e cada URL inventada vira uma página a mais para
quem estiver rastreando.

---

## Requisitos do servidor

| Item | Mínimo |
|---|---|
| PHP | 8.2 |
| Extensões | `pdo_mysql`, `mbstring` |
| MySQL / MariaDB | 5.7 / 10.4 |
| `mod_rewrite` | ativo |
| `mod_headers` | ativo — sem ele o `noindex` do `.htaccess` não sai |

---

## Como atualizar depois

O acervo cresce por fora: a coleta roda no GitHub Actions, a extração e a carga
rodam na máquina de quem mantém, e o resultado vai para o servidor como dump.

```bash
python tools/doerj_download.py --inicio 2026-09-23
python tools/doerj_extrair.py  dados/2026/09/*.pdf
python tools/doerj_temas.py    extraido/*.jsonl
python tools/doerj_carregar.py extraido/*.jsonl --pdf dados
python tools/doerj_relacoes.py
python tools/gerar_dump.py
```

Depois, no phpMyAdmin, importar `outputs/dados.sql.gz` de novo. O dump traz
`INSERT` e não `REPLACE`, então **importar por cima de dado existente dá erro de
chave duplicada** — para recarga completa, esvaziar as tabelas antes:

```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE ato_relacoes; TRUNCATE ato_ramo; TRUNCATE ato_natureza;
TRUNCATE ato_corpo; TRUNCATE atos; TRUNCATE edicoes;
SET FOREIGN_KEY_CHECKS = 1;
```

**Isto apaga a curadoria humana junto.** Enquanto ninguém tiver conferido
classificação nenhuma, não custa nada. Quando começar a custar, o caminho é
dar acesso remoto ao MySQL e rodar o `doerj_carregar.py` direto contra o
servidor — ele preserva o que está marcado como `conferido`.

---

## O que ainda não existe

| O quê | Por quê importa |
|---|---|
| Automação da carga | hoje é manual, e manual esquece |
| Cópia de segurança do banco | o painel da HostGator faz, mas ninguém testou restaurar |
| Coleta contínua indo ao ar | o Actions coleta; ninguém leva ao servidor sozinho |

E um limite que precisa aparecer na tela, não só aqui: **o Diário publica
movimentação orçamentária, não o orçamento.** Um número que pareça ser o total
e não seja, lido por órgão de controle, custa mais caro que número nenhum.
