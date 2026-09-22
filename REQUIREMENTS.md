# REQUIREMENTS.md — Portal de Normas DOERJ

**Versão:** 0.1, de 2026-09-22
**Aviso de leitura:** nada aqui está implementado ainda. Este documento diz o
que o produto precisa fazer, e a coluna de status diz onde cada coisa está.

---

## 1. O que é e para quem

Um lugar onde se acha uma norma do Estado do Rio de Janeiro sem precisar saber
em que dia ela saiu.

Hoje, quem procura um decreto ou uma resolução do Executivo estadual tem que
conhecer a data de publicação, abrir o PDF do Diário daquele dia e ler até
encontrar. Quem não sabe a data não acha. É um acervo público que na prática só
serve a quem já sabe onde procurar.

O destino é o mesmo formato do Portal de Normas e Atos da UFF: cada ato como um
registro próprio, com número, data, ementa, texto e o PDF de origem ao lado.

### Quem usa

| Perfil | O que quer |
|---|---|
| Servidor do Estado | a norma que rege o procedimento que ele executa hoje |
| Advogado, contador, despachante | a redação vigente, e o histórico de alterações |
| Jornalista e pesquisador | o que mudou em determinado assunto ao longo do tempo |
| Cidadão | entender uma regra que o afeta, sem vocabulário jurídico |
| Fornecedor do Estado | editais, prazos, e as normas de contratação |

Vale o mesmo princípio do outro projeto: **escreva para o porteiro e para o
doutor.** Quem chega sabendo o número do decreto tem que achar rápido. Quem
chega sabendo só o assunto também.

---

## 2. Requisitos funcionais

| # | Requisito | Status |
|---|---|---|
| RF-01 | Baixar o PDF do DOERJ Poder Executivo de uma data | **implementado** |
| RF-02 | Baixar um intervalo de datas, para recompor o acervo | **implementado** |
| RF-03 | Rodar sozinho todo dia útil, sem ninguém apertar botão | **implementado** |
| RF-04 | Não gravar arquivo vazio nem dar sucesso falso | **implementado** |
| RF-05 | ~~Guardar o PDF original~~ — substituído: guardar o endereço e a impressão digital | **revisto em 2026-09-22** |
| RF-06 | Extrair o texto do PDF | **implementado** |
| RF-07 | Separar o Diário do dia em atos individuais | parcial — separa matérias; matéria com vários atos ainda é uma só |
| RF-08 | Identificar tipo, número, data e órgão de cada ato | **implementado** para os atos numerados |
| RF-09 | Extrair a ementa | parcial — deduzida, e marcada como tal |
| RF-10 | Guardar tudo em banco com busca por texto | esquema pronto e provado; falta o que preencher |
| RF-11 | Ligar um ato ao que ele altera ou revoga | pendente |
| RF-12 | Busca por número, por data, por órgão, por assunto | pendente |
| RF-13 | Página de cada ato, com link para o PDF de origem | pendente |
| RF-14 | Dizer de onde veio e quando foi coletado | pendente |
| RF-16 | Dizer, onde a pessoa lê, que o PDF não tem valor legal | pendente |
| RF-15 | Endereço fixo por ato, que não quebra com o tempo | pendente |

### RF-01 tem um detalhe que decide tudo

A verificação não pode ser o código HTTP. O `mostra_edicao.php` responde 200
para chave inválida, com corpo vazio. Um downloader que confie no status grava
o vazio e escreve "ok" no log. O critério é o corpo: tamanho plausível, tipo do
conteúdo, e a assinatura `%PDF` nos primeiros bytes.

### RF-11 é o que separa portal de repositório

Uma norma sozinha não responde a pergunta que as pessoas fazem. A pergunta é
"isso ainda vale?". Sem a cadeia de alterações e revogações, o portal devolve um
texto que pode estar morto há seis anos, e quem lê não tem como saber.

Vai ser a parte mais difícil, porque a relação está escrita em prosa dentro do
ato, não num campo. Fica para depois das fases que a sustentam, e entra com
indicação clara de confiança: "detectado automaticamente" não é a mesma coisa
que "conferido por pessoa".

---

## 3. Requisitos não funcionais

| # | Requisito | Por quê |
|---|---|---|
| RNF-01 | Educado com o servidor de origem: uma requisição por vez, intervalo entre elas, e para na primeira recusa | é um site de governo, e derrubá-lo encerra o projeto |
| RNF-02 | Idempotente: rodar duas vezes a mesma data não duplica nada | **implementado.** cron repete, e vai repetir |
| RNF-03 | Log que diz o que aconteceu de verdade | ver RF-04 |
| RNF-04 | Nenhuma credencial no repositório | regra do projeto |
| RNF-05 | Acessível, WCAG 2.1 AA | é serviço público |
| RNF-06 | Abre em conexão ruim e em telefone modesto | idem |
| RNF-07 | Roda na hospedagem que já existe, sem servidor novo | custo |
| RNF-08 | Falha de coleta avisa alguém, não fica quieta | **parcial.** O Actions manda e-mail quando a execução falha, e a janela de três dias recupera perda pontual. O que ainda não existe é alarme para coleta que para de rodar por completo |

---

## 4. Critérios de aceitação por fase

| Fase | Passa quando |
|---|---|
| 1 | passou em 2026-09-22: edições 171 a 173, e fim de semana como "sem edição" |
| 2 | passou em 2026-09-22: 33 segundos, arquivos idênticos aos locais |
| 3 | decidido em 2026-09-22: não se guarda PDF. Esquema pronto e provado |
| 4 | passou em 2026-09-22: 850 matérias de 3 edições, 166 atos, conferidos contra o PDF |
| 5 | Busca por texto devolve o ato certo |
| 6 | Uma pessoa que nunca viu o portal acha uma norma pelo assunto |

---

## 5. Fora de escopo, por enquanto

- Poder Legislativo e Judiciário. Só o Executivo.
- Municípios.
- Consolidação de texto, ou seja, mostrar a norma já com as alterações aplicadas. É trabalho jurídico, não de software.
- Qualquer coisa que pareça aconselhamento jurídico.

### Uma coisa que NÃO está fora de escopo

Dizer que o PDF coletado **não tem valor legal**. O próprio IOERJ nomeia o
arquivo `Nao_Possui_Valor_Legal_*.pdf`. Um portal que apresente esse texto como
se fosse a publicação oficial engana quem o usa para decidir alguma coisa. É o
RF-16, e ele não é enfeite.

---

## 6. Dúvidas e decisões pendentes

Estão em [STEPS.md](STEPS.md), na seção do mesmo nome, para não haver duas
listas divergindo.
