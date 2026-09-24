# REQUIREMENTS.md — Portal de Normas DOERJ

**Versão:** 0.3, de 2026-09-24
**O que mudou da 0.2:** a importação completa passa a ser planejada para rodar
automaticamente na HostGator, com publicação direta e sem revisão prévia.

**O que mudou da 0.1:** o produto deixou de ser um portal de normas genérico.
Ganhou um recorte — ciência, pesquisa e inovação — e um público que inclui a
gestão da SECTI-RJ, a alta gestão do Estado e os órgãos de controle.

---

## 1. O que é e para quem

Um lugar onde se enxerga o que o Estado do Rio de Janeiro decidiu, gastou e
entregou em ciência, pesquisa e inovação, a partir do que ele próprio publicou
no Diário Oficial.

O Diário é público e quase inacessível: para ler um ato é preciso saber o dia da
publicação, abrir o PDF e procurar. Quem não sabe a data não acha. E ninguém
consegue olhar dois anos de uma pasta e dizer o que foi feito.

### Três lentes sobre o mesmo acervo

| # | Lente | Para quê |
|---|---|---|
| 1 | **CT&I em todas as pastas** | ciência, tecnologia e inovação não acontecem só na SECTI. Saúde, Educação, Ambiente e Fazenda decidem sobre CT&I o tempo todo, e hoje ninguém vê isso junto |
| 2 | **Histórico da SECTI-RJ** | a gestão atual precisa saber o que foi feito antes dela, e a sociedade precisa poder conferir |
| 3 | **Cada vinculada no seu espaço** | FAPERJ, UERJ, UENF, CECIERJ e FAETEC publicam sob o nome da secretaria. Hoje viram um balaio só |

A lente 1 é a que dá insumo para decisão: mostra onde o Estado já investe em
CT&I fora da SECTI, e portanto onde há parceria possível e onde há sobreposição.

### Quem usa

| Perfil | O que quer |
|---|---|
| Gestão da SECTI | o que a pasta fez, quanto custou, e o que as outras pastas fazem em CT&I |
| Governador e alta gestão | resultado da pasta em números, sem depender de relatório produzido pela própria pasta |
| Órgãos de controle (TCE, CGE, MP) | rastrear um contrato ou um programa do início ao fim, pela fonte oficial |
| Pesquisador e universidade | editais, bolsas, fomento, e o que mudou nas regras |
| Servidor do Estado | a norma que rege o que ele executa hoje |
| Jornalista e sociedade | o que foi decidido, quanto custou, e se foi entregue |
| Cidadão | entender uma regra que o afeta, sem vocabulário jurídico |
| Fornecedor do Estado | editais, prazos e normas de contratação |

Vale o mesmo princípio do Mapa de CT&I: **escreva para o porteiro e para o
doutor.** Quem chega sabendo o número do decreto acha rápido. Quem chega sabendo
só o assunto também.

---

## 2. Requisitos funcionais

### Coleta e base

| # | Requisito | Status |
|---|---|---|
| RF-01 | Baixar o PDF do DOERJ Poder Executivo de uma data | **implementado** |
| RF-02 | Baixar um intervalo de datas, para recompor o acervo | **implementado** |
| RF-03 | Rodar sozinho todo dia útil | **implementado** |
| RF-04 | Não gravar arquivo vazio nem dar sucesso falso | **implementado** |
| RF-05 | ~~Guardar o PDF~~ — guardar o endereço e a impressão digital | revisto |
| RF-06 | Extrair o texto do PDF | **implementado** |
| RF-07 | Separar o Diário em matérias | **implementado** |
| RF-08 | Identificar tipo, número, data e órgão | **implementado** |
| RF-09 | Extrair a ementa | parcial — deduzida, e marcada como tal |
| RF-10 | Banco com busca por texto | **implementado** |
| RF-11 | Ligar um ato ao que ele altera ou revoga | parcial — o declarado, com parcial x total |
| RF-12 | Busca por número, data, órgão e assunto | pendente |
| RF-14 | Dizer de onde veio e quando foi coletado | pendente |
| RF-16 | Dizer que o PDF não tem valor legal | pendente |
| RF-17 | Identificar a vinculada que publicou | **implementado** |
| RF-30 | Mascarar CPF e documento de identidade antes de gravar | **implementado** |
| RF-33 | Ocultar endereço de pessoa natural em auto de infração | **implementado** |
| RF-31 | Não ser indexado por buscador | **implementado** — falta subir |
| RF-32 | Ler a capa e registrar quem comandava cada pasta em cada data | **implementado** |
| RF-34 | Baixar, extrair, classificar e carregar novas edições automaticamente no banco publicado | desenho aprovado; implementação pendente |

**RF-17 existe porque o Diário esconde a autoria.** FAPERJ, UERJ, UENF, CECIERJ
e FAETEC publicam sob "Secretaria de Estado de Ciência, Tecnologia e Inovação".
Sem separar, não há como dar a cada uma o seu espaço.

**RF-30 e RF-31 andam juntos, e o motivo é o mesmo.**

O Diário é publicação oficial e o CPF está lá, à vista. A diferença é o que
acontece depois: um PDF por dia, que exige saber a data, é uma coisa. Um acervo
de anos com busca por texto é outra — o mesmo dado passa a permitir montar o
histórico de uma pessoa em segundos. Indexado por buscador, vira terceira coisa.

A LGPD trata dessa diferença. Publicidade legal não autoriza reuso ilimitado.
E a finalidade deste projeto é transparência sobre **o que o Estado decidiu e
gastou** — para isso o CPF de ninguém é necessário.

O nome do servidor fica. Nomeação e exoneração são atos públicos, e esconder o
nome esvaziaria a transparência que motiva o projeto. Sai o documento, que não
acrescenta nada à fiscalização e acrescenta tudo ao risco.

**O mascaramento acontece na extração, antes de gravar.** O banco nunca vê o
número. Mascarar na tela deixaria o dado no banco, no backup e no dump, e
bastaria uma consulta mal feita para ele reaparecer. O que não se guarda não
vaza. O PDF original continua no IOERJ, com tudo, para quem tiver base legal.

Medido em 8 edições de 2010 a 2026: **1.249 documentos ocultados** em 2.012
matérias. O próprio IOERJ já publica parte dos CPFs mascarados — `041.XXX.127-96`
— o que mostra que a direção é a mesma.

**RF-33 e a linha que ele traça.** Auto de infração traz nome, CPF e endereço
de casa. Fiscalização ambiental e de trânsito não é objeto deste portal, então o
endereço residencial não precisa ficar fácil de achar aqui — ele continua no PDF
do IOERJ, para quem tiver necessidade legítima.

Mas **endereço de empresa fica.** A LGPD protege pessoa natural, e autuação
contra empresa é exatamente o que o portal existe para mostrar: esconder onde
fica a fábrica autuada protegeria quem não precisa de proteção. O documento ao
lado do nome diz o que é — CNPJ é empresa, CPF é pessoa — e quando aparecem os
dois vale o mais protetivo.

Medido nas 8 edições: 91 endereços de pessoa ocultados, 11 de pessoa jurídica
preservados. Entre eles, a Prefeitura de Itaboraí autuada pelo INEA.

E fora de auto de infração o endereço nunca sai: ali "ENDEREÇO:" é onde se
entrega proposta de licitação ou onde é a sessão, e apagar isso tiraria do
portal informação que ele existe para mostrar. São 33 casos no corpus.

**Sobre o RF-31, uma ressalva honesta:** `robots.txt` é pedido, não cadeado.
Buscador que respeita a convenção obedece; raspador determinado não. A medida
que vale mais é o cabeçalho `X-Robots-Tag: noindex`, e nem ele impede quem não
quiser obedecer. Não indexar reduz alcance; não é proteção.

### As três lentes

| # | Requisito | Status |
|---|---|---|
| RF-18 | Classificar cada matéria por tema de CT&I | pendente |
| RF-19 | Lente 1: CT&I de todas as pastas, num lugar só | pendente |
| RF-20 | Lente 2: linha do tempo da SECTI e do seu sistema | pendente |
| RF-21 | Lente 3: espaço próprio e pesquisável por vinculada | pendente |
| RF-22 | Busca que funciona em qualquer das três lentes | pendente |

**RF-18 tem uma armadilha medida, não suposta.** 17% das matérias mencionam
termo de CT&I, mas **"pesquisa de preços" é licitação, não ciência**. A
classificação precisa de exclusões explícitas, e o que for classificado por
regra automática tem que dizer que foi.

### Números, custo e execução

| # | Requisito | Status |
|---|---|---|
| RF-23 | Extrair valor em R$ de cada matéria que traga um | pendente |
| RF-24 | Extrair processo SEI, contrato e vigência | pendente |
| RF-25 | Ler os anexos de crédito suplementar: programa de trabalho, natureza de despesa, fonte e valor | pendente |
| RF-26 | Ligar atos do mesmo processo SEI numa linha do tempo | pendente |
| RF-27 | Mostrar, por pasta e por período, como o dinheiro se reparte entre folha, custeio, investimento e repasse a terceiro setor | pendente |
| RF-28 | Comparar o que foi orçado com o que foi entregue | pendente |

**O que foi medido, e sustenta esses requisitos:**

| Sinal | Presença em 850 matérias |
|---|---|
| Valor em R$ | 26% — 803 valores, somando R$ 3,2 bilhões em três dias |
| Processo SEI | **91%** |
| Número de contrato | 10% |
| Prazo ou vigência | 13% |
| Natureza de despesa | só nos decretos de crédito suplementar, e ali em peso |

O processo SEI em 91% das matérias é o achado que viabiliza o RF-26: é a chave
que liga o edital, o contrato, o aditivo e o pagamento do mesmo objeto.

**RF-27 responde a uma pergunta que hoje se responde de ouvido.** A suspeita é
que a maior parte do orçamento vai para folha e material, e quase nada para
projeto e ação voltada à sociedade. Os códigos de natureza de despesa permitem
medir isso em vez de supor:

| Código | O que é |
|---|---|
| `3190` | pessoal e encargos — a folha |
| `3390` | outras despesas correntes — material e serviço |
| `4490` | investimento |
| `3350` e `4450` | repasse a instituição sem fins lucrativos, onde mora boa parte do projeto com a sociedade |

Os códigos aparecem nos anexos dos decretos de crédito suplementar, junto do
programa de trabalho e da fonte. **Casar cada código com o seu valor exige ler a
tabela pela geometria da página**, e não por expressão regular: no texto
achatado, o código e o R$ ficam em pedaços distantes um do outro.

### Apresentação

| # | Requisito | Status |
|---|---|---|
| RF-13 | Página de cada ato, com link para o PDF de origem | pendente |
| RF-15 | Endereço fixo por ato, que não quebra com o tempo | **implementado** |
| RF-29 | Os números aparecem como parte natural da consulta, e não como painel à parte com nome de inteligência | pendente |

**Sobre o RF-29.** A capacidade analítica é a parte mais valiosa da ferramenta,
e é justamente por isso que ela não se anuncia. Um portal de transparência que
se apresenta como instrumento de inteligência convida a ser lido como
instrumento político — e aí perde as duas coisas: a confiança de quem consulta e
a serventia para quem decide.

O caminho é o oposto. Cada ato mostra o seu valor, o seu processo e o seu
histórico como informação comum. As somas aparecem onde fazem sentido: por
pasta, por período, por programa. Quem precisa do panorama chega nele navegando,
e não clicando num botão chamado "análise".

Isso não esconde nada. Tudo que a ferramenta mostra é publicação oficial, e a
origem de cada número fica a um clique.

---

## 3. Requisitos não funcionais

| # | Requisito | Por quê | Status |
|---|---|---|---|
| RNF-01 | Educado com o servidor de origem | é site de governo, e derrubá-lo encerra o projeto | **implementado** |
| RNF-02 | Idempotente | cron repete, e vai repetir | **implementado** |
| RNF-03 | Log que diz o que aconteceu de verdade | ver RF-04 | **implementado** |
| RNF-04 | Nenhuma credencial no repositório | regra do projeto | **implementado** |
| RNF-05 | Acessível, WCAG 2.1 AA | é serviço público | pendente |
| RNF-06 | Abre em conexão ruim e em telefone modesto | idem | pendente |
| RNF-07 | Roda na hospedagem que já existe | custo | domínio de pé em `doerj.fanara.com.br` |
| RNF-08 | Falha de coleta avisa alguém | um mês sem coletar só se descobre tarde | parcial |
| RNF-09 | Todo número mostra de qual ato saiu | ver abaixo | pendente |
| RNF-10 | O que foi deduzido por regra automática aparece marcado | proveniência não é enfeite | parcial |
| RNF-11 | Nenhum CPF, documento de identidade ou endereço residencial no banco | LGPD, e minimização: o que não se guarda não vaza | **implementado** |
| RNF-12 | `robots.txt`, `<meta robots>` e `X-Robots-Tag` recusando indexação | mesma razão do RNF-11 | **implementado** — falta subir |
| RNF-13 | Uma execução automática não concorre com outra e mantém backup anterior à carga | cron escreve em produção sem operador | desenho aprovado; implementação pendente |

**RNF-09 é o que separa esta ferramenta de uma planilha.** Se a tela diz que a
SECTI aplicou determinado valor num programa, tem que haver o caminho até o
decreto que publicou aquele número. Sem isso, quem for questionado por um órgão
de controle não tem como responder, e a ferramenta vira passivo em vez de ativo.

---

## 4. Critérios de aceitação por fase

| Fase | Passa quando | Estado |
|---|---|---|
| 1 | Baixa o PDF de uma data e recusa data inválida | passou em 2026-09-22 |
| 2 | O mesmo, rodando no GitHub Actions | passou em 2026-09-22 |
| 3 | Decidido onde o acervo mora | só texto, PDF por referência |
| 4 | De um Diário de verdade saem as matérias | 850 matérias, 3 edições |
| 5 | Banco carregado, busca devolve o ato certo | banco pronto; API pendente |
| 6 | Classificação temática conferida à mão contra o PDF | pendente |
| 7 | As três lentes respondem | pendente |
| 8 | Valores casados com natureza de despesa, cada número mostrando sua origem | pendente |
| 9 | O cron publica uma edição nova, repete sem duplicar e deixa backup e log verificáveis | desenho aprovado; implementação pendente |

---

## 5. Fora de escopo

- Poder Legislativo e Judiciário. Só o Executivo.
- Municípios.
- Consolidação de texto — mostrar a norma já com as alterações aplicadas. É
  trabalho jurídico, não de software.
- Qualquer coisa que pareça aconselhamento jurídico.
- **Execução orçamentária completa.** Ver o limite abaixo.

### O limite honesto da parte orçamentária

O Diário publica **movimentação**, e não o orçamento inteiro. Crédito
suplementar, contrato, empenho e repasse aparecem; a Lei Orçamentária Anual e a
execução consolidada vivem no SIAFE-Rio e no portal da Transparência.

Então a ferramenta responde bem **"para onde o dinheiro se moveu, e em favor de
quê"**, e não responde **"quanto a pasta gastou no ano"**.

Isso precisa estar escrito na tela, e não só aqui. Um número que parece ser o
total e não é, lido por um órgão de controle, custa mais caro que número nenhum.

Se a pergunta do total for necessária, o caminho é cruzar com a Transparência:
outra fonte, outra fase, outra decisão.

### Uma coisa que NÃO está fora de escopo

Dizer que o PDF coletado **não tem valor legal**. O próprio IOERJ nomeia o
arquivo `Nao_Possui_Valor_Legal_*.pdf`. Um portal que apresente esse texto como
se fosse a publicação oficial engana quem o usa para decidir. É o RF-16.

---

## 6. Dúvidas e decisões pendentes

Estão em [STEPS.md](STEPS.md), na seção do mesmo nome, para não haver duas
listas divergindo.
