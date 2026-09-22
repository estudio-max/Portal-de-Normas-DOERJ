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
| 2 | Provar que o download roda no GitHub Actions | **concluída** |
| 3 | Onde os PDFs ficam em definitivo | **concluída** |
| 4 | Extração de texto e identificação dos atos | **é a próxima** |
| 5 | Banco e API (`backend/db`, `backend/api`) | esquema pronto; API pendente |
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

## Fase 2 — roda no Actions. Concluída em 2026-09-22

**O risco não se confirmou.** O runner do GitHub fica nos Estados Unidos, e a
dúvida era se um site de governo estadual recusaria endereço estrangeiro. Não
recusou: a execução levou 33 segundos e trouxe os arquivos com os mesmos
tamanhos byte a byte do que tinha sido baixado aqui.

Com isso, cron na hospedagem e runner self-hosted saem do desenho. Ficam
anotados como saída caso o IOERJ mude de ideia.

### Duas coisas quebraram, e as duas eram minhas

**`cache: pip` sem `requirements.txt`.** O downloader não tem dependência
nenhuma, e o cache do pip precisa de um arquivo de dependências para montar a
chave. A execução morria antes de tentar baixar qualquer coisa. Um fluxo que
falha por causa do cache de algo que não existe é ruído puro.

**O padrão coletava "ontem".** A edição do dia é gerada por volta das 4h da
manhã, então às 9h ela já existe. Coletar ontem deixaria a de hoje para nunca, e
o portal viveria um dia atrasado sem nenhum sinal de erro.

Agora o agendamento cobre os últimos três dias, no fuso do Rio. Como o
downloader pula o que já tem, a janela custa três consultas de listagem e
recupera sozinha o que uma falha de rede tiver perdido.

### Prova

Execução sem data nenhuma, em 22/09/2026:

```
Coletando de 2026-09-19 a 2026-09-22
2026-09-19  sem edição
2026-09-20  sem edição
2026-09-21     4783 KB  2026-09-21-parte-i-poder-executivo.pdf
2026-09-22     2623 KB  2026-09-22-parte-i-poder-executivo.pdf
2 gravado(s), 0 já existia(m), 0 falha(s)
```

## Fase 3 — decidida em 2026-09-22: guarda-se o texto, não o PDF

**O PDF não fica.** Fica o texto extraído e o endereço do arquivo na origem, do
mesmo jeito que o Portal de Normas e Atos da UFF faz com `boletins.url_pdf` e
`ato_corpo.texto`.

Isso derruba de 750 MB a 1,5 GB por ano para alguns megabytes, e torna a
recomposição do acervo desde 2010 uma conta de texto, não de 20 GB de PDF.

### Por que isto funciona aqui, e o teste que provou

Referenciar arquivo na origem só presta se o endereço durar. Testei: **a chave
da edição de 15/01/2010 continuava servindo o arquivo em 22/09/2026.** O
timestamp que aparece no token mora na listagem, não na chave do PDF.

### O que se perde, e está escrito para não ser redescoberto com espanto

O endereço aponta para servidor de terceiro. Se o IOERJ mudar o esquema, todos os
links quebram de uma vez e não há cópia para onde correr. Diferente da UFF, cujo
`url_pdf` aponta para um servidor da própria UFF.

Duas defesas baratas ficaram no esquema, e nenhuma devolve o arquivo:

- `edicoes.guid` guarda o identificador cru, então uma mudança na forma de montar
  a URL se conserta com um `UPDATE`, não com uma recoleta;
- `edicoes.sha256` guarda a impressão digital do PDF de onde o texto saiu. Sem o
  arquivo em mãos, é o que permite provar depois que o texto publicado veio
  daqueles bytes.

Se o acervo de origem sumir, o portal continua funcionando como texto e perde a
prova. É a troca que a decisão implica.

### O que ficou pronto

`backend/db/001-esquema.sql`, decalcado do modelo da UFF: `edicoes`, `atos`,
`ato_corpo` e `ato_relacoes`. Nomes iguais aos de lá onde o sentido é o mesmo,
para quem cuida dos dois portais não ter que aprender duas modelagens.

Três coisas que o esquema carrega de propósito, e que são lições da UFF:

- `ementa_inferida` — ementa deduzida não é ementa publicada;
- `status_origem` e `ato_relacoes.origem` — "detectado automaticamente" não é a
  mesma coisa que "conferido por pessoa", e quem lê tem direito de saber qual é;
- `ato_destino_id` pode ser nulo — dá para registrar "revoga o Decreto nº 45.452"
  antes de saber qual registro é esse, que é como a curadoria acontece.

### Prova

```
python backend/db/provar_esquema.py
```

Cria o banco do zero, aplica o esquema, insere as três edições coletadas e três
decretos de verdade do Diário de 22/09/2026, e roda as sete consultas que o
portal vai fazer. Inclui o caso real do Decreto 50.485, que revoga o 45.452 de
2015.

Rodou contra MySQL 8.4 em 2026-09-22. Passou.

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
| ~~DP-04~~ | ~~Onde os PDFs ficam em definitivo~~ | (c) só texto, PDF por referência | resolvido em 2026-09-22 |
| DP-05 | Que atos entram? Só normas, ou também atos de pessoal | (a) só normas; (b) tudo | Alto — muda a extração e o tamanho do banco |
| DP-06 | Qual a licença do repositório | — | Baixo |
| DP-07 | Como o portal deixa claro que o PDF não tem valor legal | (a) aviso fixo na página de cada ato; (b) só na página "sobre" | **Alto — é o risco jurídico do projeto** |
| DP-08 | Até que ano recompor o acervo | testei 2010 e funcionou | Médio — agora é conta de texto, não de 20 GB de PDF |
| DP-09 | O que fazer se o IOERJ quebrar os links | (a) aceitar e viver de texto; (b) guardar PDF só das normas, não do Diário inteiro | Médio — é a única defesa que devolveria o arquivo |
