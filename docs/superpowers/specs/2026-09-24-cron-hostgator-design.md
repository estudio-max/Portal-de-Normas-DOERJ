# Automação diária da importação na HostGator

**Data:** 2026-09-24  
**Estado:** desenho aprovado em princípio; implementação depende da revisão deste documento

## Objetivo

Publicar automaticamente no portal as novas edições do DOERJ — Poder
Executivo — sem revisão humana prévia. Em cada dia útil, a hospedagem baixa uma
janela de três dias, extrai e classifica as matérias, atualiza o MySQL de
produção e recalcula relações e prazos.

A classificação automática continua identificada como automática na interface.
O cron publica dados; não atualiza o código do portal e não executa `git pull`.

## Abordagem escolhida

O caminho principal é um cron executado na própria HostGator. Antes de criar a
tarefa, uma prova de capacidade deve confirmar no servidor:

- Python compatível com o código atual;
- criação de ambiente virtual fora do document root;
- instalação e importação de PyMuPDF e PyMySQL;
- disponibilidade de `flock`, `php`, `mysql` e `mysqldump`;
- espaço e tempo de execução suficientes para três edições.

Se qualquer uma dessas condições falhar, o fallback aprovado é executar o
processamento no GitHub Actions e publicar na HostGator por SSH. Não será criado
um cron incompleto ou silenciosamente incompatível.

## Componentes

### Orquestrador

Um orquestrador versionado em `tools/` executará, nesta ordem:

1. adquirir trava exclusiva; se já houver execução, sair sem erro;
2. calcular hoje e três dias atrás no fuso `America/Sao_Paulo`;
3. baixar os PDFs com `doerj_download.py`;
4. extrair os PDFs da janela com `doerj_extrair.py`;
5. classificar os JSONL com `doerj_temas.py`;
6. fazer backup do banco antes da primeira escrita;
7. carregar os JSONL com `doerj_carregar.py`;
8. recalcular relações com `doerj_relacoes.py`;
9. recalcular prazos com `doerj_prazos.py`;
10. gravar um marcador de sucesso com horário, intervalo e contagens.

Feriado ou dia sem edição é sucesso sem alteração. Repetir a mesma janela é
seguro porque o downloader pula o PDF íntegro já existente e a carga usa o
`id_ioerj` único para atualizar em vez de duplicar.

### Diretórios no servidor

Código e dados operacionais ficam fora do alcance do navegador:

```text
/home1/fanara87/
├── doerj/                     código; public/ continua sendo o document root
└── doerj-var/
    ├── dados/                 PDFs de trabalho
    ├── extraido/              JSONL processado
    ├── backups/               dumps anteriores à carga
    ├── logs/                  uma execução por arquivo
    ├── estado/                último sucesso e última falha
    └── cron.lock              trava de concorrência
```

PDFs e JSONL operacionais terão retenção limitada, suficiente para diagnóstico e
recuperação. Backups e logs serão rotacionados sem tocar nos arquivos do site.

### Credenciais

A senha continua somente em `/home1/fanara87/doerj/config/config.php`, com
permissão `600`. O orquestrador lê a configuração por um subprocesso PHP e
entrega a credencial aos processos filhos sem colocá-la na linha de comando, no
crontab, no repositório ou nos logs.

O cron usará caminhos absolutos para o interpretador, o projeto e os dados. Não
haverá endpoint web capaz de iniciar uma importação.

### Agendamento

A intenção é executar de segunda a sexta às 09:15 no horário de Brasília. A
expressão final será calculada depois de conferir o fuso que o cPanel aplica ao
cron: `15 9 * * 1-5` se o servidor usar Brasília; `15 12 * * 1-5` se usar UTC.

O horário evita a virada da hora, quando tarefas compartilhadas tendem a se
concentrar, e mantém a coleta depois do horário habitual de publicação do
Diário.

## Falhas e recuperação

- Qualquer etapa que falhe interrompe as seguintes e produz código de saída
  diferente de zero.
- A carga de cada JSONL já é transacional; erro provoca rollback daquele
  arquivo.
- O backup acontece antes da primeira escrita no banco.
- Relações e prazos só rodam depois de a carga terminar.
- A última execução bem-sucedida não é sobrescrita por uma execução com erro.
- O cron emite saída somente em falha ou num resumo curto, para que o mecanismo
  de e-mail do cPanel possa avisar sem enviar ruído diário.
- Para rollback, desativa-se o cron e restaura-se o último dump confirmado.

## Publicação sem revisão

Foi decidido em 2026-09-24 que novas matérias podem ir ao ar sem revisão humana
prévia. Isso não transforma inferência em fato: `ementa_inferida`, classificação
temática automática e demais campos deduzidos continuam marcados como tais.

## Testes e implantação

A implementação seguirá TDD e será liberada em quatro gates:

1. testes do orquestrador com comandos substituídos por executáveis falsos,
   cobrindo ordem, janela de datas, ausência de edição, falha e trava;
2. todos os `--autoteste` das ferramentas atuais e a prova de esquema verdes;
3. execução manual na HostGator com janela curta, backup e conferência das
   contagens antes/depois;
4. criação do cron e confirmação de uma execução realmente disparada pelo
   agendador.

Executar o script manualmente duas vezes deve produzir as mesmas contagens no
banco. A automação só será declarada concluída depois de uma edição nova ficar
visível no portal e de o registro de sucesso corresponder ao log do cron.

## Critérios de aceitação

- o cron existe no cPanel e está habilitado em dias úteis;
- uma edição nova percorre download, extração, classificação e carga sem ação
  humana;
- duas execuções da mesma janela não duplicam edição nem matéria;
- uma falha não deixa duas instâncias concorrentes nem apaga o último estado de
  sucesso;
- existe backup anterior à carga e um procedimento de restauração documentado;
- nenhum segredo aparece no repositório, no comando do cron ou nos logs;
- relações e prazos refletem os atos recém-importados;
- a página pública exibe um ato da edição importada automaticamente.

## Fora deste escopo

- atualização automática do código do portal;
- recomposição histórica de anos anteriores;
- revisão humana antes da publicação;
- criação de um endpoint HTTP de administração;
- mudança de provedor ou de banco de dados.

