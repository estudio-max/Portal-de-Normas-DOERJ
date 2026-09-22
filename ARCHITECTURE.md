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
│   └── download-diario.yml agendamento pronto, sem downloader para chamar
├── tools/                  vazio. Aqui vai o downloader
├── backend/db/             vazio
├── backend/api/            vazio
├── src/                    vazio
└── docs/                   vazio
```

Nenhum código roda. Nenhum dado foi coletado.

### O que se sabe da origem

Detalhado no [CLAUDE.md](CLAUDE.md). O resumo de arquitetura:

O IOERJ serve o Diário por `…/portal/modules/conteudoonline/mostra_edicao.php`,
que recebe uma chave em `?k=`. A chave parece ser um GUID, e a etapa que
traduz uma data nesse GUID não foi encontrada. Sem ela não há o que buscar.

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

### Banco e API

A modelagem tem referência pronta: o Portal de Normas e Atos da UFF, cujos
dumps de 2001 a 2014 estão à mão, com tabelas como `boletins` e `ato_funcoes`.
Vale estudar antes de desenhar do zero. **Referência, não cópia:** o que serve à
UFF não serve necessariamente ao Executivo estadual, que tem outros tipos de
ato e outra estrutura de órgãos.

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

## Decisões adiadas

| # | Decisão | Quando decidir |
|---|---|---|
| AD-06 | Onde os PDFs ficam em definitivo | Fase 3 |
| AD-07 | Banco: MySQL da hospedagem, ou SQLite com busca embutida | Fase 5 |
| AD-08 | Linguagem da API | Fase 5 |
| AD-09 | Onde a automação roda: Actions, cron da hospedagem, runner próprio | depende do teste da Fase 2 |
