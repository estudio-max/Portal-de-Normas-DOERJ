# Portal de Normas — DOERJ

Reunir as normas do **Diário Oficial do Estado do Rio de Janeiro, Poder
Executivo**, num lugar onde dê para achar uma norma sem saber a data em que ela
saiu.

Hoje o acervo é público e quase inacessível. Para ler um decreto é preciso saber
o dia da publicação, abrir o PDF daquele dia e procurar. Quem não sabe a data
não acha. O projeto existe para resolver esse pedaço.

> **Repositório privado** até a coleta provar que funciona. Código de raspagem
> público antes de funcionar convida cópia de algo quebrado.
>
> **Estado: começando.** A documentação e o esqueleto estão de pé. Nada foi
> coletado ainda, e a primeira fase está bloqueada. O porquê está logo abaixo.

---

## Em que ponto estamos

| Fase | O que entrega | Status |
|---|---|---|
| 0 | Esqueleto, documentação e agendamento | concluída |
| 1 | Downloader do Diário | **bloqueada** |
| 2 | Provar que a coleta roda no GitHub Actions | pendente |
| 3 | Onde os PDFs ficam em definitivo | pendente |
| 4 | Extração de texto e separação dos atos | pendente |
| 5 | Banco e API | pendente |
| 6 | Interface | pendente |

O detalhe de cada fase está em [STEPS.md](STEPS.md).

### Por que a Fase 1 está bloqueada

Falta o downloader. Ele foi descrito como pronto e funcionando, mas o arquivo
não chegou a esta máquina.

Metade do caminho está mapeada: o endpoint que serve o PDF foi encontrado e
testado, e junto com ele veio uma armadilha que mudou o desenho da verificação.
O que falta é a etapa que traduz uma data no identificador que o endpoint
espera. Sem ela, não há o que pedir ao servidor.

Nenhum arquivo foi escrito no lugar do que falta. Um `doerj_download.py` que não
baixa nada seria pior que a ausência dele, porque o agendamento passaria a
apontar para algo que parece existir.

### A armadilha, porque ela vale para quem for escrever o downloader

O `mostra_edicao.php` do IOERJ responde `Erro.` quando não recebe chave nenhuma.
Mas quando recebe uma chave **inválida**, responde **status 200 com corpo
vazio**.

Ou seja: **200 não é sucesso aqui.** Um downloader que confie no código de
status vai gravar centenas de arquivos vazios, e o log vai dizer que deu tudo
certo. A verificação tem que ser sobre o conteúdo: tamanho do arquivo e a
assinatura `%PDF` nos primeiros bytes.

O fluxo do Actions já confere isso, em [download-diario.yml](.github/workflows/download-diario.yml).

---

## Como está organizado

```
tools/        coleta e extração
backend/db/   modelo de dados
backend/api/  consulta
src/          o portal
docs/         documentação de apoio
```

Os PDFs ficam em `dados/`, que está fora do git. São cerca de 80 páginas por
dia, e repositório não é lugar para isso.

---

## Documentação

| Arquivo | Responde |
|---|---|
| [CLAUDE.md](CLAUDE.md) | o que se sabe do site de origem, com o verificado separado do herdado |
| [REQUIREMENTS.md](REQUIREMENTS.md) | o que o produto faz, para quem, sob quais regras |
| [ARCHITECTURE.md](ARCHITECTURE.md) | como está construído hoje, e só depois o pretendido |
| [STEPS.md](STEPS.md) | em que ponto estamos e o que vem a seguir |

---

## Um risco que ainda não foi medido

O servidor que o GitHub Actions usa fica nos Estados Unidos, e sites de governo
estadual às vezes recusam endereço estrangeiro. Se a coleta funcionar na máquina
local e falhar no Actions, o caminho passa a ser cron na hospedagem ou um
servidor próprio rodando o agendamento.

Esse teste é a Fase 2, e ele vem cedo de propósito: descobrir isso depois de
construir o resto seria caro.
