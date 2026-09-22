# Portal de Normas — DOERJ

Reunir as normas do **Diário Oficial do Estado do Rio de Janeiro, Poder
Executivo**, num lugar onde dê para achar uma norma sem saber a data em que ela
saiu.

Hoje o acervo é público e quase inacessível. Para ler um decreto é preciso saber
o dia da publicação, abrir o PDF daquele dia e procurar. Quem não sabe a data
não acha. O projeto existe para resolver esse pedaço.

> **Repositório privado** por enquanto. Abrir ou não é decisão pendente.
>
> **A coleta funciona.** Falta o resto: extrair o texto, separar os atos, banco,
> busca e interface.

---

## Em que ponto estamos

| Fase | O que entrega | Status |
|---|---|---|
| 0 | Esqueleto, documentação e agendamento | concluída |
| 1 | Downloader do Diário | **concluída** |
| 2 | Provar que a coleta roda no GitHub Actions | em teste |
| 3 | Onde os PDFs ficam em definitivo | pendente |
| 4 | Extração de texto e separação dos atos | pendente |
| 5 | Banco e API | pendente |
| 6 | Interface | pendente |

O detalhe de cada fase está em [STEPS.md](STEPS.md).

## Como baixar

Só precisa de Python 3. Nenhuma dependência fora da biblioteca padrão.

```
python tools/doerj_download.py --inicio 2026-09-22
python tools/doerj_download.py --inicio 2026-09-01 --fim 2026-09-22
python tools/doerj_download.py --inicio 2026-09-22 --todos
python tools/doerj_download.py --autoteste
```

O padrão é só a Parte I, do Poder Executivo. `--todos` traz os outros cadernos.
Os arquivos ficam em `dados/AAAA/MM/`, fora do git.

Rodar duas vezes a mesma data não baixa de novo, e dia sem edição sai como
"sem edição" em vez de erro.

## Duas coisas que quem mexer nisto precisa saber

### 200 não é sucesso

O `mostra_edicao.php` responde `Erro.` quando não recebe chave nenhuma. Mas
quando recebe uma chave **inválida**, responde **status 200 com corpo vazio**.

Um downloader que confie no código de status grava centenas de arquivos vazios,
e o log diz que deu tudo certo. A conferência tem que ser sobre o conteúdo:
tipo, tamanho e a assinatura `%PDF` nos primeiros bytes. O downloader confere, e
o [fluxo do Actions](.github/workflows/download-diario.yml) confere de novo.

### O PDF não tem valor legal

O próprio IOERJ nomeia o arquivo `Nao_Possui_Valor_Legal_*.pdf`. O que se coleta
aqui serve para consulta, busca e pesquisa, e não substitui a publicação
oficial. O portal precisa dizer isso onde a pessoa lê, e não num rodapé.

O caminho completo até o PDF, com o truque da chave, está no [CLAUDE.md](CLAUDE.md).

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
