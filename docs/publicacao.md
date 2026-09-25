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
visita, e o que não está no servidor não pode ser servido por engano. A exceção
é o conjunto mínimo de ferramentas de importação automática, descrito abaixo,
que fica fora do document root.

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

### O banco

`fanara87_doerj`, carregado em 2026-09-23 com 2.012 atos, 3.099 classificações,
23 relações e 8 edições.

O usuário MySQL é o **mesmo do portal da UFF**, `fanara87_UFFN0rm4s`, por
decisão de quem responde pela conta. Vale saber o que isso implica: a mesma
credencial abre os dois bancos, e se uma vazar, vazam os dois. Um usuário
dedicado por projeto isolaria — é troca de conveniência por contenção, e a
escolha está registrada aqui para poder ser revista.

Para recarregar:

```bash
bash ~/doerj/instalar-banco.sh
```

O script lê a credencial do próprio `config.php` e a passa ao MySQL por arquivo
temporário com permissão 600, apagado ao fim aconteça o que acontecer. **Senha
em linha de comando fica no histórico do shell e na lista de processos**,
visível a qualquer outro usuário do servidor compartilhado.

#### Uma armadilha que custou uma rodada

A senha reaproveitada tem `#`. O formato `.cnf` trata `#` como início de
comentário e **corta a senha no meio** — o MySQL respondeu "Access denied", que
não aponta para lugar nenhum: parecia senha errada, quando o errado era o
arquivo que a carregava.

A senha vai entre aspas no `.cnf`, e é por isso. Quem for reaproveitar o script
em outro projeto não repete o erro.

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

## A área interna: a senha é criada no cPanel

A pasta `interno/` guarda o que é só da equipe da SECTI: prazos dos
compromissos, o 100 Dias, o regimento contra o Diário. Ela é protegida pela
senha do próprio servidor, e **quem cria o usuário e a senha é quem administra a
hospedagem** — a senha não passa pelo código, pelo repositório nem por quem
programou.

1. No cPanel, abra **Privacidade do diretório** (em inglês, *Directory
   Privacy*).
2. Entre em `doerj.fanara.com.br` e clique na pasta **`interno`**.
3. Marque **Proteger este diretório por senha**, dê um nome — por exemplo,
   "Área interna SECTI" — e salve.
4. Na mesma tela, em **Criar usuário**, crie um usuário e uma senha para cada
   pessoa ou um para a equipe.
5. Abra `https://doerj.fanara.com.br/interno/`. O navegador deve pedir usuário
   e senha, e depois mostrar os prazos.

**Enquanto isso não for feito, a área responde "Área restrita" para todo
mundo** — inclusive para a equipe. É de propósito: o PHP só abre a página quando
o servidor diz que alguém entrou com senha, e sem a proteção ninguém entrou.

**O pacote de publicação não leva `.htaccess` para dentro de `interno/`.** O
cPanel grava a proteção num `.htaccess` dessa pasta; se uma publicação trouxesse
outro, apagaria a senha. Se um dia a área voltar a dizer "Área restrita" para
quem tem senha, é isto: refaça o passo 3.

O conteúdo dos painéis vem de `config/interno.php`, que não está no git e vai
no pacote. Sem ele, os painéis do 100 Dias e do regimento aparecem vazios.

## Requisitos do servidor

| Item | Mínimo |
|---|---|
| PHP | 8.2 |
| Extensões | `pdo_mysql`, `mbstring` |
| MySQL / MariaDB | 5.7 / 10.4 |
| `mod_rewrite` | ativo |
| `mod_headers` | ativo — sem ele o `noindex` do `.htaccess` não sai |

---

## Importação automática

Desde 2026-09-25, a HostGator executa uma importação direta, sem revisão humana,
em dias úteis às **09:15 de Brasília**. O relógio do host foi conferido em
2026-09-24 como UTC-03:00, o mesmo fuso de Brasília usado pelo agendador:

```cron
15 9 * * 1-5 TZ=America/Sao_Paulo /home1/fanara87/doerj-var/venv/bin/python /home1/fanara87/doerj/tools/doerj_cron.py --raiz /home1/fanara87/doerj --trabalho /home1/fanara87/doerj-var >> /home1/fanara87/doerj-var/logs/cron.log 2>&1
```

O comando processa os três dias anteriores, reaproveita PDFs já presentes e
reprocessa a janela de forma idempotente, impede execuções concorrentes, cria
um backup do MySQL antes da carga e atualiza
relações e prazos. O estado da última execução fica em
`/home1/fanara87/doerj-var/estado/ultimo-sucesso.json`; falhas ficam em
`ultima-falha.json` e têm log próprio em `logs/`.

Os diretórios temporários `dados/` e `extraido/` e os backups são retidos por
14 dias; logs, por 30 dias. O runtime `doerj-var` é privado (700), e
`config/config.php` tem permissão 600.

Para executar manualmente uma janela, sem alterar o agendamento:

```bash
/home1/fanara87/doerj-var/venv/bin/python /home1/fanara87/doerj/tools/doerj_cron.py \
  --raiz /home1/fanara87/doerj --trabalho /home1/fanara87/doerj-var \
  --inicio 2026-09-24 --fim 2026-09-24
```

Para conferir o backup mais recente sem restaurá-lo sobre produção:

```bash
arquivo=$(ls -1t /home1/fanara87/doerj-var/backups/*.sql.gz | head -1)
gzip -t "$arquivo"
gunzip -c "$arquivo" | head -20
```

Para desativar a automação, remova somente essa linha em **Cron Jobs** no cPanel
ou por `crontab -e`; não apague `doerj-var`, os backups ou os logs.

---

## O que ainda não existe

| O quê | Por quê importa |
|---|---|
| Restauração do backup em ambiente descartável | o backup gzip foi validado, mas restaurar em produção não é teste seguro |

E um limite que precisa aparecer na tela, não só aqui: **o Diário publica
movimentação orçamentária, não o orçamento.** Um número que pareça ser o total
e não seja, lido por órgão de controle, custa mais caro que número nenhum.
