# STEPS.md — Portal de Normas DOERJ

**Documento criado em:** 2026-09-22
**Estado geral:** projeto recém-aberto. Esqueleto e documentação de pé; nenhuma
etapa funcional concluída.

---

## Onde estamos

| Fase | O que entrega | Status |
|---|---|---|
| 0 | Esqueleto, documentação e agendamento | **concluída** |
| 1 | Downloader do DOERJ Poder Executivo | **bloqueada** — ver abaixo |
| 2 | Provar que o download roda no GitHub Actions | pendente, depende da 1 |
| 3 | Onde os PDFs ficam em definitivo | pendente |
| 4 | Extração de texto e identificação dos atos | pendente |
| 5 | Banco e API (`backend/db`, `backend/api`) | pendente |
| 6 | Interface, no formato do portal da UFF (`src`) | pendente |

---

## Fase 0 — concluída em 2026-09-22

Estrutura de pastas, `.gitignore`, `CLAUDE.md` com o que se sabe do site,
`README.md` com a tabela de etapas, e o fluxo do GitHub Actions.

Junto veio uma investigação do site do IOERJ, registrada no `CLAUDE.md`. O achado
que muda o desenho do downloader: **`mostra_edicao.php` devolve `Erro.` quando
não recebe chave, mas devolve corpo vazio com status 200 quando a chave é
inválida.** Quem confiar no código de status grava arquivo vazio e registra
sucesso no log.

## Fase 1 — downloader. **Bloqueada, e o bloqueio é de informação**

O handoff que abriu este projeto descreve `tools/doerj_download.py` como pronto
e funcionando. **O arquivo não chegou a esta máquina**, e o zip mencionado
também não. Procurei em `C:\projetos` e em `Downloads`.

Deliberadamente não escrevi um substituto. O que eu verifiquei sozinho cobre
metade do caminho — o endpoint `?k=` e a armadilha do 200 vazio — e falta a
etapa que traduz **data → GUID**, sem a qual não há o que baixar. Escrever um
arquivo com esse nome que não baixa nada seria pior que a ausência dele: o fluxo
do Actions passaria a apontar para algo que parece existir.

### Duas saídas, e a escolha é de quem tem o contexto

| # | Caminho | O que exige |
|---|---|---|
| A | Trazer o downloader que já funciona | copiar o arquivo ou colar o conteúdo |
| B | Reconstruir do zero | continuar a engenharia reversa a partir do que está no `CLAUDE.md`, provavelmente lendo o JavaScript da listagem de edições |

A é barata e preserva conhecimento já pago. B custa tempo incerto: o que falta
não está no HTML servido, então passa por descobrir como a listagem é montada.

## Fase 2 — provar que roda no Actions

**Esta é a fase que mais importa cedo, e por isso não fica para o fim.**

O runner do GitHub fica nos Estados Unidos, e sites de governo estadual às vezes
recusam endereço estrangeiro. Se o download funcionar aqui e falhar lá, todo o
desenho de automação muda.

Teste: rodar o fluxo manualmente com uma data conhecida antes de confiar no
agendamento. Se falhar, as saídas são cron na hospedagem ou runner self-hosted.

Enquanto a Fase 1 estiver bloqueada, esta não roda — mas o fluxo já está escrito
e o teste é de um clique quando houver o que testar.

## Fase 3 — onde os PDFs ficam

Artifact de 7 dias resolve o desenvolvimento e não resolve o produto: um portal
de normas precisa do histórico. Decidir entre armazenamento na hospedagem,
bucket, ou só o texto extraído com o PDF referenciado na origem.

## Fases 4 a 6

Extração e identificação dos atos, banco e API, interface. O formato de destino
é o do Portal de Normas e Atos da UFF, cuja base existe em dumps de 2001 a 2014
e serve de referência de modelagem — `boletins`, `ato_funcoes` e afins.

---

## Dúvidas e decisões pendentes

| # | Pergunta | Alternativas | Impacto |
|---|---|---|---|
| DP-01 | O downloader existente será trazido, ou reconstruo? | (a) trazer; (b) reconstruir | **Alto — trava a Fase 1 e tudo depois** |
| DP-02 | O repositório no GitHub deve ser criado por mim ou por você? | (a) eu crio com `gh`, mediante sua confirmação; (b) você cria | Médio — o handoff dizia que o último passo era seu |
| DP-03 | `estudio-max/Portal-de-Normas-DOERJ` público desde o início? | (a) público; (b) privado até a Fase 2 passar | Médio — código de raspagem público antes de funcionar convida cópia de algo quebrado |
| DP-04 | Onde os PDFs ficam em definitivo | (a) hospedagem; (b) bucket; (c) só texto, PDF por referência | Alto — decide a Fase 3 e o custo mensal |
| DP-05 | Que atos entram? Só normas, ou também atos de pessoal | (a) só normas; (b) tudo | Alto — muda a extração e o tamanho do banco |
| DP-06 | Qual a licença do repositório | — | Baixo |
