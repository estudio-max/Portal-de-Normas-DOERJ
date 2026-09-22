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
| 4 | Extração de texto e identificação dos atos | **concluída** |
| 5 | Banco e API (`backend/db`, `backend/api`) | banco **concluído**; API pendente |
| 6 | Classificação temática de CT&I | **é a próxima** |
| 7 | As três lentes, e a interface | pendente |
| 8 | Valores casados com natureza de despesa | pendente |
| 9 | Agendar extração e carga junto da coleta | pendente |

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

## Fase 4 — extração. Concluída em 2026-09-22

`tools/doerj_extrair.py`. Lê o PDF e escreve um JSONL, uma linha por matéria.
Não toca no banco: carregar é a Fase 5, e separar as duas deixa reprocessar sem
mexer em dado publicado.

### O presente que o Diário deu

**Cada matéria publicada termina com `Id: 2765345`.** É o identificador da
própria Imprensa Oficial. Foram 265 identificadores na edição de 22/09/2026,
todos distintos. Isso troca "adivinhar onde um ato acaba" por "ler o marcador",
e ainda dá de graça a chave natural que faz a reimportação ser idempotente.

As fontes dizem o papel de cada bloco: `ArialMT` é matéria, `GalliardITCbyBT-Bold`
em 10pt é nome de órgão, `UniversLTStd` é o expediente do IOERJ e `FilosofiaBold`
é o cabeçalho decorativo, que sai como lixo de codificação.

### Uma matéria não é um ato, e é isso que torna a Fase 4 difícil

Matéria é unidade de publicação. Uma traz um decreto só; outra traz sete
nomeações em sequência; outra não traz ato numerado nenhum.

Medido em 850 matérias de três edições: **entre 13% e 23% trazem ato numerado.**
O resto é movimentação de pessoal, despacho e retificação — que é o grosso do
Diário.

Por isso a ferramenta **não descarta o que não reconhece.** Toda matéria vira uma
linha, com `reconhecido: false` quando não há ato numerado. Se pessoal entra no
portal é a DP-05, e essa decisão não cabe a uma ferramenta de extração.

### Três defeitos achados e corrigidos, todos silenciosos

Nenhum dos três dava erro. Os três produziam dado errado com cara de certo, que
é o jeito que extração de PDF costuma falhar.

**O expediente do IOERJ vazava para dentro do primeiro decreto.** "ENVIO DE
MATÉRIAS / Marcio Fontes de Mattos / Diretor-Presidente" ficava colado no meio
do Decreto 50.485. Resolvido pelo filtro de fonte.

**Norma citada virava ato publicado.** "na forma do Decreto nº 25.299, de
19/05/99" gerava um registro de um decreto de 1999 como se tivesse sido
publicado hoje. Cabeçalho de ato sai em caixa alta, citação sai em caixa mista:
é esse o discriminador. Tirou 21 atos falsos de uma edição só.

**A capa inteira entrava dentro do Decreto 50.483.** Brasão, lista de
secretários e sumário. O sumário fica na terceira coluna, acima do texto do
decreto, então lido por coluna ele cai no meio do ato.

O terceiro rendeu uma lição que valeu a tarde. A primeira correção cortava tudo
acima da última linha pontilhada, porque sumário tem linha pontilhada. Só que
**resolução que altera outra norma cita artigo com reticências** —
`"Art. 7º ............"`. A página 35 da edição de 18/09/2026 virou capa e cinco
matérias reais evaporaram sem aviso nenhum. Só apareceu porque eu conferi a
contagem antes e depois.

O sinal certo é a linha pontilhada **junto do título do sumário**, que só existe
na capa. Os dois casos estão travados em teste.

### O que sai

```
python tools/doerj_extrair.py --autoteste
python tools/doerj_extrair.py dados/2026/09/*.pdf
```

Por matéria: `id_ioerj`, data, caderno, página, órgão, tipo, número, data do ato,
ementa e o texto inteiro. Mais `reconhecido` e `ementa_inferida`, porque ementa
deduzida não é ementa publicada.

Resultado nas três edições coletadas: **850 matérias, 166 atos numerados.**

### O que ainda não faz, e é honesto dizer

- Uma matéria com sete nomeações vira **uma** linha, não sete. O campo
  `outros_atos` guarda os cabeçalhos extras, mas ninguém os separou ainda.
- Não detecta relação entre atos. O `ato_relacoes` continua vazio, e a pergunta
  "essa norma ainda vale?" continua sem resposta automática.
- A ementa é deduzida do bloco em caixa alta. Funciona em cerca de 90% dos atos
  numerados, e nos outros o campo fica nulo — que é resposta honesta.
- Texto com espaçamento decorativo sai quebrado: "DEPARTAMENTO DE TRÂN S I TO".
  É artefato do PDF, e não tem conserto barato.

## Fase 5 — banco carregado. Concluída em 2026-09-22, menos a API

```
python tools/doerj_carregar.py extraido/*.jsonl --pdf dados
python tools/doerj_relacoes.py
```

850 atos e 20 relações no banco, a partir das três edições coletadas. O
encadeamento inteiro roda do banco vazio: migrações, extração, carga, relações.

### O esquema estava errado, e a Fase 4 provou

A `001` foi escrita antes de eu ter lido um Diário inteiro, e supunha que todo
ato tem número, como na UFF. A medição derrubou a suposição: **entre 77% e 87%
das matérias não têm número.** Com `numero NOT NULL`, carregar um Diário
significaria jogar fora quatro quintos dele, ou inventar número para o que não
tem. A `002` deixa `tipo` e `numero` nulos e acrescenta `id_ioerj`.

`id_ioerj` é a chave natural da origem, e sai de graça: como é `UNIQUE`,
recarregar a mesma edição atualiza as mesmas linhas em vez de duplicar o Diário.
Provado rodando a carga duas vezes: 850 novos, depois 850 atualizados.

### O detector de relações acha menos do que poderia, de propósito

78 das 850 matérias mencionam alguma relação, e só 20 viraram registro. A
diferença não é falha: é que **menção não é ação.**

| Trecho | O que é |
|---|---|
| "ALTERA A PORTARIA SEDES Nº 102" | relação. Este ato faz isso |
| "o valor do Anexo I do Decreto nº 50.240, alterado..." | contexto. Outro ato alterou, em outro momento |
| "regulamentada pelo Decreto nº 43.510" | contexto. Quem regulamenta é o outro |

Um detector que aceitasse as três avisaria que normas vivas foram revogadas. Num
portal de normas esse é o pior erro possível: alguém deixa de cumprir regra que
vale, ou cumpre regra que caiu, e o erro tem a nossa assinatura.

Deixar relação verdadeira escapar custa um campo vazio. Inventar relação falsa
custa o portal inteiro. Os dois erros não pesam igual, e o código reflete isso.

Depois de medir os 18 casos que escapavam, 5 eram falha minha e foram
corrigidos: sigla de duas palavras ("PORTARIA DER SEI Nº 136"), "ALTERA O ART. 1º
DA...", "ALTERA, EM PARTE,", "N.º" com ponto, e "DISPÕE SOBRE A ALTERAÇÃO DA...".
Os outros 13 eram rejeição correta: "ALTERA A LOTAÇÃO DO PROCURADOR" não altera
norma nenhuma.

### Revogar um artigo não é revogar a norma

O caso que obrigou uma coluna nova. A Resolução SES/SMS 4.281 faz duas coisas
com a Resolução Conjunta 564, de 2018:

```
Fica alterado o art. 1º da Resolução Conjunta ... nº 564
Fica revogado  o art. 2º da Resolução Conjunta ... nº 564
```

As duas relações são verdadeiras, e **a Resolução 564 continua em vigor.** O que
caiu foi um artigo.

Sem a coluna `parcial`, um portal que lesse `tipo_relacao = 'Revoga'` marcaria a
564 como revogada e diria a quem consulta que uma norma viva está morta. A `003`
acrescenta `parcial` e `dispositivo`, e a regra para quem for escrever a tela é
uma linha: **só revogação com `parcial = 0` derruba o status da norma alvo.**

A consulta que prova isso está no `provar_esquema.py`, item 8.

### O que falta na fase

A API. O banco responde às consultas do portal, mas nada serve isso ainda.

## Fases 6 a 9 — o recorte de CT&I

O produto mudou de escopo em 2026-09-22, e o `REQUIREMENTS.md` 0.2 tem o
detalhe. Em resumo: deixou de ser portal de normas genérico e passou a ter três
lentes — CT&I em todas as pastas, histórico da SECTI, e espaço próprio por
vinculada — mais uma camada de números.

### O que já foi medido, e não é suposição

| O quê | Medido em 850 matérias |
|---|---|
| Mencionam termo de CT&I | 17% |
| Trazem valor em R$ | 26%, somando R$ 3,2 bi em três dias |
| Trazem processo SEI | **91%** |
| Trazem contrato | 10% |
| Trazem prazo ou vigência | 13% |
| Vinculada identificada | 45% |

O SEI em 91% é o achado mais útil: é a chave que liga edital, contrato, aditivo
e pagamento do mesmo objeto numa linha do tempo.

### Duas armadilhas já conhecidas

**"Pesquisa de preços" não é pesquisa científica.** É licitação. Aparece em 2 das
850, e classificar por palavra solta erraria.

**Crédito suplementar não é o orçamento.** O Diário publica movimentação. Quem
somar crédito suplementar e chamar de gasto da pasta vai errar, e errar na frente
de órgão de controle. Ver o limite no `REQUIREMENTS.md` §5.

### Fase 6 — classificar por tema

Regra explícita com lista de inclusão e de exclusão, e marca de "classificado
automaticamente" em tudo que sair dela. Conferência à mão contra o PDF antes de
qualquer tela usar isso.

### Fase 7 — as três lentes e a interface

A lente 2, do histórico da SECTI, depende de coletar anos anteriores. A coleta
já sabe fazer isso — testei até 2010 — mas é volume: cerca de 250 edições por
ano.

### Fase 8 — valor casado com natureza de despesa

É o que responde "quanto vai para folha e quanto vai para projeto". Os códigos
estão nos anexos dos decretos de crédito suplementar: `3190` pessoal, `3390`
custeio, `4490` investimento, `3350` e `4450` repasse a terceiro setor.

**Exige ler a tabela pela geometria da página.** No texto achatado, o código e o
valor ficam em pedaços distantes, e casar os dois por expressão regular produz
número errado com aparência de certo — que aqui é o pior resultado possível.

## Dúvidas e decisões pendentes

| # | Pergunta | Alternativas | Impacto |
|---|---|---|---|
| ~~DP-01~~ | ~~Trazer o downloader ou reconstruir?~~ | reconstruído em 2026-09-22 | resolvido |
| ~~DP-02~~ | ~~Quem cria o repositório?~~ | criado em 2026-09-22 | resolvido |
| DP-03 | Abrir o repositório ao público agora que a coleta funciona? | (a) abrir; (b) seguir privado | Médio |
| ~~DP-04~~ | ~~Onde os PDFs ficam em definitivo~~ | (c) só texto, PDF por referência | resolvido em 2026-09-22 |
| ~~DP-05~~ | ~~Que atos entram?~~ | **tudo, inclusive movimentação de pessoal** | resolvido em 2026-09-22 |
| DP-11 | Quais foram os nomes da pasta de CT&I ao longo do tempo | não sei, e não vou supor. Método: coletar uma edição por semestre desde 2010 e ler os cabeçalhos de órgão | **Alto — sem isso a lente 2 perde o histórico anterior ao nome atual** |
| DP-12 | Até que ano recompor o acervo, para a lente 2 | 250 edições por ano; 2010 foi testado e funciona. Agora é conta de texto, não de 20 GB de PDF | Alto — decide o esforço de coleta |
| DP-13 | O que conta como tema de CT&I | lista de inclusão e exclusão, conferida à mão | Alto — define a lente 1 |
| DP-14 | A classificação temática precisa de revisão humana antes de publicar? | (a) sim, fila de curadoria; (b) não, com marca de automático | Médio |
| DP-06 | Qual a licença do repositório | — | Baixo |
| DP-07 | Como o portal deixa claro que o PDF não tem valor legal | (a) aviso fixo na página de cada ato; (b) só na página "sobre" | **Alto — é o risco jurídico do projeto** |
| DP-10 | Onde o banco de produção vai morar, e quem faz backup | (a) MySQL da hospedagem; (b) outro | **Alto — hoje só existe banco de teste** |
| DP-09 | O que fazer se o IOERJ quebrar os links | (a) aceitar e viver de texto; (b) guardar PDF só das normas, não do Diário inteiro | Médio — é a única defesa que devolveria o arquivo |
