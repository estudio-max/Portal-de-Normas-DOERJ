# ARCHITECTURE.md — Portal de Normas DOERJ

**Versão:** 0.1, de 2026-09-22

Este documento tem duas partes, e a ordem importa: **o que existe hoje** vem
primeiro, **o que se pretende** vem depois e está marcado como tal. Arquitetura
escrita no futuro do pretérito é a forma mais comum de um projeto mentir sobre
si mesmo.

---

## Parte 1 — o que existe hoje

Pastas, documentação e um fluxo de automação que ainda não tem o que executar.

```
portal-normas-doerj/
├── CLAUDE.md               contexto, com o verificado separado do herdado
├── REQUIREMENTS.md         o que o produto precisa fazer
├── ARCHITECTURE.md         este arquivo
├── STEPS.md                em que ponto estamos
├── .gitignore              PDF não entra no git
├── .github/workflows/
│   └── download-diario.yml coleta agendada, dias úteis às 9h
├── tools/
│   ├── doerj_download.py   a coleta. Só biblioteca padrão
│   └── doerj_extrair.py    PDF -> JSONL, uma linha por matéria
├── backend/db/
│   ├── 001-esquema.sql     4 tabelas, decalcadas da UFF
│   └── provar_esquema.py   roda as consultas do portal contra dado real
├── backend/api/            vazio
├── src/                    vazio
└── docs/                   vazio
```

A coleta funciona e foi provada contra o site. Da extração para frente, nada.

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

Esquema em `backend/db/001-esquema.sql`, decalcado do Portal de Normas e Atos da
UFF. Quatro tabelas:

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

## Decisões adiadas

| # | Decisão | Quando decidir |
|---|---|---|


| AD-08 | Linguagem da API | Fase 5 |

