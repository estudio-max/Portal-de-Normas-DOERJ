# Portal de Normas — DOERJ

Reunir as normas do **Diário Oficial do Estado do Rio de Janeiro, Poder
Executivo**, num lugar onde dê para achar uma norma sem saber a data em que ela
saiu.

Hoje o acervo é público e quase inacessível. Para ler um decreto é preciso saber
o dia da publicação, abrir o PDF daquele dia e procurar. Quem não sabe a data
não acha. O projeto existe para resolver esse pedaço.

> **Repositório privado** por enquanto. Abrir ou não é decisão pendente.
>
> **A coleta funciona e roda sozinha**, dias úteis às 9h de Brasília. Falta o
> resto: extrair o texto, separar os atos, banco, busca e interface.
>
> **O PDF não fica guardado.** Ficam o texto extraído e o endereço do arquivo
> na origem, como o portal da UFF faz.

---

## Em que ponto estamos

| Fase | O que entrega | Status |
|---|---|---|
| 0 | Esqueleto, documentação e agendamento | concluída |
| 1 | Downloader do Diário | **concluída** |
| 2 | Provar que a coleta roda no GitHub Actions | **concluída** |
| 3 | Onde os PDFs ficam em definitivo | **concluída** |
| 4 | Extração de texto e separação dos atos | **concluída** |
| 5 | Banco e API | banco pronto; **API é a próxima** |
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

## Como extrair

```
python tools/doerj_extrair.py dados/2026/09/*.pdf
```

Escreve um JSONL por edição, uma linha por matéria publicada, com órgão, tipo,
número, data, ementa e o texto inteiro.

A separação não é adivinhada: **cada matéria do Diário termina com um `Id:` da
própria Imprensa Oficial**, e é ele que marca onde uma acaba e outra começa.

Nem toda matéria é um ato numerado. Entre 13% e 23% são; o resto é movimentação
de pessoal, despacho e retificação. A ferramenta guarda tudo e marca a
diferença, porque decidir o que entra no portal não é trabalho de extrator.


## Do PDF ao banco

```
python tools/doerj_extrair.py  dados/2026/09/*.pdf
python tools/doerj_carregar.py extraido/*.jsonl --pdf dados
python tools/doerj_relacoes.py
```

Rodar duas vezes não duplica nada: o `Id:` do IOERJ é chave única, então
recarregar atualiza as mesmas linhas.

### Uma regra para quem for escrever a tela

**Só revogação com `parcial = 0` derruba o status da norma alvo.**

Um ato pode revogar o art. 2º de uma resolução sem revogar a resolução. Tratar
os dois casos como um faria o portal dizer que uma norma viva está morta — que é
exatamente o erro que este projeto existe para não cometer.


## O banco

Esquema em [001-esquema.sql](backend/db/001-esquema.sql), decalcado do Portal de
Normas e Atos da UFF: `edicoes`, `atos`, `ato_corpo` e `ato_relacoes`.

Para conferir que ele faz o que promete, contra um MySQL de verdade:

```
python backend/db/provar_esquema.py
```

O teste cria o banco do zero, insere três decretos reais do Diário de 22/09/2026
e roda as consultas do portal, incluindo a pergunta que mais importa: **essa
norma ainda vale?**

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
