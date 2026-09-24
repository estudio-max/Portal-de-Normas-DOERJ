# ARCHITECTURE.md — Portal de Normas DOERJ

**Versão:** 0.1, de 2026-09-22

Este documento tem duas partes, e a ordem importa: **o que existe hoje** vem
primeiro, **o que se pretende** vem depois e está marcado como tal. Arquitetura
escrita no futuro do pretérito é a forma mais comum de um projeto mentir sobre
si mesmo.

---

## Parte 1 — o que existe hoje

**No ar em `https://doerj.fanara.com.br` desde 2026-09-23**, com 1.979 matérias
de 8 edições entre 2010 e 2026. Fora dos buscadores, como o portal da UFF.

O caminho inteiro funciona: o site do IOERJ entrega o PDF, o PDF vira texto por
matéria, o texto vira linha de banco classificada, e o portal lê o banco. Só a
coleta é automática; extração, carga e publicação ainda são chamadas na mão.

```
portal-normas-doerj/
├── .github/workflows/
│   └── download-diario.yml coleta agendada, dias úteis, janela de 3 dias
├── tools/                  o caminho do dado, cada peça com --autoteste
│   ├── doerj_download.py   IOERJ -> PDF. Só biblioteca padrão, porque roda no CI
│   ├── doerj_extrair.py    PDF -> JSONL, uma linha por matéria
│   ├── doerj_temas.py      escreve e_cti, confiança e ramos no JSONL
│   ├── doerj_carregar.py   JSONL -> banco, idempotente
│   ├── doerj_relacoes.py   acha o que altera ou revoga o quê, e a vigência
│   ├── lgpd.py             mascara CPF e endereço de particular, na extração
│   ├── vocabulario.py      os termos, tirados do regimento e da Lei 9.809/2022
│   ├── doerj_titulares.py  quem comandou cada pasta, lido da capa da edição
│   ├── contraste.py        23 pares de cor contra a WCAG 2.1 AA
│   ├── gerar_*.py          instalador, dump e pacote de publicação
│   └── instalar-banco.sh   recarga do banco de produção, com backup datado
├── backend/db/
│   ├── 001..008-*.sql      migrações, em ordem
│   ├── instalar.sql        as oito somadas, para instalar de uma vez
│   └── provar_esquema.py   roda as consultas do portal contra dado real
├── app/                    o portal. PHP 8.3, sem framework
│   ├── bootstrap.php       config, escape, resumo() e paragrafos()
│   ├── Banco.php           PDO com prepare nativo
│   ├── Acervo.php          as consultas: panorama, busca, ficha, filtros
│   ├── provar_texto.php    prova resumo() e paragrafos()
│   └── Views/              layout, home, busca, ato, sobre, erro
├── public/                 a raiz do site no servidor
│   ├── .htaccess           HTTPS, CSP, e a recusa de indexação
│   ├── robots.txt
│   ├── index.php           o roteador
│   └── assets/             base.css com os tokens do Mapa, e a Nunito Sans
├── config/config.exemplo.php    o de verdade não entra no git
└── docs/                   publicação, categorias, árvore de termos, titulares
```

### Como o dado anda

```
IOERJ  --download-->  dados/AAAA/MM/*.pdf  (+ .json com guid e sha256)
                          |
                      extrair            mascara CPF e endereço aqui, antes de gravar
                          v
                  extraido/*.jsonl       uma linha por matéria
                          |
                       temas             e_cti, confiança, ramos, naturezas
                          v
                  extraido/*.jsonl
                          |
                      carregar
                          v
                     MySQL  -- relacoes -->  vigência recalculada
                          |
                        app/  -->  a tela
```

O PDF fica de fora do git e do banco: o portal guarda **só o texto extraído**, e
aponta para o PDF na origem, como faz o portal de normas da UFF.

### O que se sabe da origem

Detalhado no [CLAUDE.md](CLAUDE.md). O resumo de arquitetura:

O IOERJ serve o Diário em três passos: a data vira base64, a listagem devolve um
token em base64 triplo, e a chave do PDF é o GUID com uma letra enfiada na
posição 12. O detalhe está no `CLAUDE.md` e no cabeçalho do downloader.

O endpoint aceita chave inválida em silêncio: responde 200 com corpo vazio.
Isso não é detalhe de implementação, é restrição de arquitetura. **A camada de
coleta precisa validar conteúdo, e não transporte.** Quem desenhar essa camada
confiando no protocolo desenha errado.

---

## Parte 2 — arquitetura pretendida

Quatro etapas, cada uma podendo parar sem derrubar as outras. É a diferença
entre "o site caiu" e "o site está com dois dias de atraso na coleta".

```
  IOERJ
    │  HTTP, uma requisição por vez
    ▼
┌─────────────┐
│  Coleta     │  tools/     PDF do dia, íntegro
└─────────────┘
    │
    ▼
┌─────────────┐
│ Extração    │  tools/     texto e atos individuais
└─────────────┘
    │
    ▼
┌─────────────┐
│ Banco + API │  backend/   busca e consulta
└─────────────┘
    │
    ▼
┌─────────────┐
│ Interface   │  src/       o portal
└─────────────┘
```

### Coleta

Python, disparada por agendamento. Guarda o PDF original sem tocar em nada:
ele é a prova. Qualquer dúvida sobre o que foi extraído se resolve voltando
ao arquivo de origem, e um PDF "melhorado" na entrada apaga essa possibilidade.

### Automação de produção — desenho aprovado, ainda não implementado

O cron será executado na HostGator, fora do document root, e encadeará a janela
de três dias da coleta até a carga no MySQL publicado. Uma trava exclusiva
impedirá concorrência; backup, log e marcador de estado serão gravados antes e
depois das etapas que alteram o banco. A credencial continuará somente em
`config/config.php` e não aparecerá no comando do cron.

A implantação depende de provar no servidor o interpretador Python e as
dependências nativas. Se a hospedagem compartilhada não suportar PyMuPDF ou o
tempo de execução necessário, o processamento muda para GitHub Actions e a
HostGator recebe o resultado por SSH. O desenho completo está em
`docs/superpowers/specs/2026-09-24-cron-hostgator-design.md`.

### Extração

Separada da coleta de propósito. Quando a regra de identificação de atos
melhorar, e ela vai melhorar várias vezes, o reprocessamento roda em cima dos
PDFs que já estão aqui. Se as duas etapas estivessem juntas, cada ajuste de
regex custaria uma nova visita ao site do Estado.

A separação em matérias é mecânica, não adivinhada: **o próprio IOERJ fecha cada
matéria com um `Id:`**. O que é deduzido daí para frente — tipo, número, ementa —
vai marcado como deduzido. Ver a Fase 4 do `STEPS.md`.

A saída é JSONL, e não `INSERT`. Texto extraído é material de trabalho: vai ser
refeito muitas vezes, e arquivo intermediário deixa conferir o resultado antes
de qualquer coisa tocar dado publicado.

### Banco e API

Esquema em `backend/db/`, aplicado na ordem do nome do arquivo. Decalcado do
Portal de Normas e Atos da UFF. Quatro tabelas:

| Tabela | Guarda | Equivale na UFF a |
|---|---|---|
| `edicoes` | um caderno do Diário, de um dia, com o endereço do PDF | `boletins` |
| `atos` | cada norma, com tipo, número, data, órgão e ementa | `atos` |
| `ato_corpo` | o texto inteiro, à parte | `ato_corpo` |
| `ato_relacoes` | o que altera ou revoga o quê | `ato_relacoes` |

Onde o DOERJ é diferente, a modelagem diverge: `boletins` virou `edicoes` porque
o mesmo dia tem vários cadernos e às vezes edição extra; `sigla` de unidade da
UFF virou `orgao` mais `orgao_slug`, porque a mesma secretaria muda de grafia ao
longo dos anos; e o bloco de campos do SEI não existe aqui.

### Interface

Mesma linha do Mapa de CT&I: sem bundler, sem framework pesado, servindo bem em
telefone modesto e conexão ruim. Um portal de normas que só abre em desktop
rápido exclui exatamente quem mais precisa dele.

---

## Decisões já tomadas

| # | Decisão | Motivo |
|---|---|---|
| AD-01 | Coleta separada de extração | reprocessar sem voltar ao site |
| AD-02 | PDF original preservado sem alteração | é a prova |
| AD-03 | Validação por conteúdo, nunca por status HTTP | o endpoint mente |
| AD-04 | PDF fora do git | ~80 páginas por dia |
| AD-05 | Python na coleta e na extração | é onde vivem as bibliotecas de PDF |
| AD-10 | Coleta sem dependência externa | roda em qualquer Python 3, sem `pip install`, e não quebra quando uma biblioteca muda |
| AD-11 | O token vem da listagem, não é remontado | o timestamp embutido é regra do IOERJ, que pode mudar amanhã |
| AD-12 | A automação roda no GitHub Actions | provado em 2026-09-22. Cron na hospedagem e runner próprio ficam como saída se o IOERJ passar a recusar endereço estrangeiro |
| AD-13 | O PDF não é guardado. Ficam o texto e o endereço na origem | a chave do IOERJ é permanente, provado com a edição de 2010. Derruba o custo de GB por ano para MB |
| AD-14 | MySQL, com `FULLTEXT` | é o que a hospedagem tem e o que o portal da UFF usa. Busca embutida sem serviço de índice à parte |
| AD-15 | Modelagem decalcada da UFF | quem cuida dos dois portais não aprende duas modelagens |
| AD-16 | A matéria é separada pelo `Id:` do IOERJ | é marcador da origem, não heurística nossa. E serve de chave natural para reimportar |
| AD-17 | A extração escreve JSONL, não SQL | dá para conferir antes de tocar em dado publicado |
| AD-18 | O que não é reconhecido é guardado, não descartado | decidir o que entra no portal é da DP-05, não do extrator |
| AD-19 | PyMySQL no que escreve no banco | consulta parametrizada. Montar SQL com texto de PDF é onde mora esse tipo de bug |
| AD-20 | Relação só entra quando o ato **declara** que a faz | voz passiva e oração adjetiva descrevem, não agem. Inventar revogação falsa custa mais que perder uma verdadeira |
| AD-21 | Revogação de artigo é `parcial = 1` | revogar o art. 2º não revoga a norma. Só `parcial = 0` derruba o status do alvo |
| AD-22 | Identidade visual decalcada do Mapa de CT&I | dois produtos da mesma secretaria. Quem usa um reconhece o outro sem ler o cabeçalho |
| AD-23 | Sem modo escuro | o Mapa é claro. Inventar aqui um modo que lá não existe faria os dois parecerem coisas diferentes |
| AD-24 | Fonte servida por este site, nunca por CDN | CDN entrega o endereço de rede de cada visitante a um terceiro, e num acervo que as pessoas consultam sobre si isso pesa mais |
| AD-25 | Novas edições podem ser publicadas automaticamente, sem revisão humana prévia | decidido em 2026-09-24; campos inferidos continuam marcados como automáticos |
| AD-26 | O cron principal roda na HostGator, com fallback para Actions + SSH se a prova de capacidade falhar | evita instalar uma automação incompatível ou pesada demais para a hospedagem compartilhada |

## Decisões adiadas

| # | Decisão | Quando decidir |
|---|---|---|


| AD-08 | Linguagem da API | Fase 5 |

