# STEPS.md — Portal de Normas DOERJ

**Documento criado em:** 2026-09-22
**Estado geral:** projeto recém-aberto. Esqueleto e documentação de pé; nenhuma
etapa funcional concluída.

---

## Onde estamos

| Fase | O que entrega | Status |
|---|---|---|
| 0 | Esqueleto, documentação e agendamento | **concluída** |
| 1 | Downloader do DOERJ Poder Executivo | **concluída** |
| 2 | Provar que o download roda no GitHub Actions | **em teste** |
| 3 | Onde os PDFs ficam em definitivo | pendente |
| 4 | Extração de texto e identificação dos atos | pendente |
| 5 | Banco e API (`backend/db`, `backend/api`) | pendente |
| 6 | Interface, no formato do portal da UFF (`src`) | pendente |

---

## Fase 0 — concluída em 2026-09-22

Estrutura de pastas, `.gitignore`, `CLAUDE.md` com o que se sabe do site,
`README.md` com a tabela de etapas, e o fluxo do GitHub Actions.

O repositório está em `estudio-max/Portal-de-Normas-DOERJ`, **privado**.

Junto veio uma investigação do site do IOERJ, registrada no `CLAUDE.md`. O achado
que muda o desenho do downloader: **`mostra_edicao.php` devolve `Erro.` quando
não recebe chave, mas devolve corpo vazio com status 200 quando a chave é
inválida.** Quem confiar no código de status grava arquivo vazio e registra
sucesso no log.

## Fase 1 — downloader. Concluída em 2026-09-22

`tools/doerj_download.py`, só biblioteca padrão. O caminho até ele está no
`CLAUDE.md`: três passos, token em base64 triplo, e uma letra enfiada no meio do
GUID para montar a chave.

O downloader que existiria nunca chegou a esta máquina. Este foi reconstruído
por engenharia reversa do `viewer-min.js`.

### O que ele faz

- lê o token da listagem em vez de inventá-lo, porque o timestamp embutido
  sugere validade curta e a regra é do IOERJ, não nossa;
- confere `Content-Type`, `%PDF` e tamanho mínimo antes de gravar;
- grava em `.parcial` e renomeia, para interrupção não deixar meio PDF com nome
  de arquivo pronto;
- pula o que já está em disco, porque o cron repete;
- espera entre requisições, com repetição em caso de falha de rede;
- numera edição extra a partir da segunda, sem renomear a primeira.

### Prova

```
python tools/doerj_download.py --autoteste
python tools/doerj_download.py --inicio 2026-09-18 --fim 2026-09-22
```

Resultado em 22/09/2026: edições 171, 172 e 173, de 81, 70 e 41 páginas, em
sequência e sem buraco. Sábado e domingo saíram como "sem edição". A segunda
execução pulou os três.

## Fase 2 — provar que roda no Actions

**Esta é a fase que mais importa cedo, e por isso não fica para o fim.**

O runner do GitHub fica nos Estados Unidos, e sites de governo estadual às vezes
recusam endereço estrangeiro. Se o download funcionar aqui e falhar lá, todo o
desenho de automação muda.

Teste: rodar o fluxo manualmente com uma data conhecida antes de confiar no
agendamento. Se falhar, as saídas são cron na hospedagem ou runner self-hosted.

Com a Fase 1 pronta, o teste é disparar o fluxo à mão com uma data conhecida e
olhar o resultado.

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
| ~~DP-01~~ | ~~Trazer o downloader ou reconstruir?~~ | reconstruído em 2026-09-22 | resolvido |
| ~~DP-02~~ | ~~Quem cria o repositório?~~ | criado em 2026-09-22 | resolvido |
| DP-03 | Abrir o repositório ao público agora que a coleta funciona? | (a) abrir; (b) seguir privado | Médio |
| DP-04 | Onde os PDFs ficam em definitivo | (a) hospedagem; (b) bucket; (c) só texto, PDF por referência | Alto — decide a Fase 3 e o custo mensal |
| DP-05 | Que atos entram? Só normas, ou também atos de pessoal | (a) só normas; (b) tudo | Alto — muda a extração e o tamanho do banco |
| DP-06 | Qual a licença do repositório | — | Baixo |
| DP-07 | Como o portal deixa claro que o PDF não tem valor legal | (a) aviso fixo na página de cada ato; (b) só na página "sobre" | **Alto — é o risco jurídico do projeto** |
| DP-08 | Até que ano recompor o acervo | testei 2010 e funcionou | Médio — decide o volume inicial |
