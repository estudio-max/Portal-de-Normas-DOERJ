# Árvore de termos de CT&I da SECTI-RJ

**Gerado de `tools/vocabulario.py` por `tools/gerar_arvore.py`.** Não edite
este arquivo à mão: mexa no módulo e gere de novo, senão os dois divergem e o
documento passa a descrever uma ferramenta que não existe mais.

A árvore não foi inventada. Sai da **Minuta do Regimento Interno da nova SECTI,
versão 16**, e da **Lei estadual nº 9.809, de 22 de julho de 2022**, que o
regimento aponta como fundamento.

Isso muda a natureza da coisa. Vocabulário montado por quem programa reflete o
que quem programa imagina que a secretaria faz. Vocabulário tirado do regimento
reflete o que ela declara fazer — e quando alguém perguntar por que determinado
ato entrou na lente, a resposta é um artigo, e não uma opinião.

**Sobre a grafia.** Os termos aparecem sem acento e às vezes pela metade —
"inovac", "tecnolog", "foruns oficia". Não é erro: a busca roda sobre o texto
normalizado, e o radical casa com todas as flexões de uma vez. "inovac" pega
inovação, inovações, inovador e inovadora; "foruns oficia" pega fórum oficial e
fóruns oficiais.

---

## Tronco: as âncoras

Nome próprio criado pela legislação de CT&I do Estado. Quem cita, está falando
do sistema — e por isso entram sozinhas, com confiança **alta**, sem depender de
mais nenhuma palavra.

- **lei 9809** — lei estadual nº 9.809
- **sistecti** — sistecti
- **conecti** — conecti
- **fatec** — fundo de apoio ao desenvolvimento tecnologico ou fatec
- **polo virtual** — polo virtual de inovacao
- **estrategia estadual** — estrategia estadual de ciencia
- **ict** — icts ou instituicao ou oes cientific
- **marco legal** — lei complementar nº 182 ou marco legal da inovacao ou lei nº 10.973

## As entidades do sistema

Ato delas é do recorte, **inclusive o de pessoal**: saber quem entra e quem sai
da FAPERJ é parte de entender a pasta.

A ordem abaixo é a ordem em que são procuradas, e ela importa. Todas publicam
sob o nome da SECTI, então a secretaria vem por último — se viesse primeiro,
casaria sempre, a vinculada nunca, e a lente que dá a cada uma o seu espaço
ficaria vazia.

- **faperj** — faperj ou fundacao carlos chagas filho
- **uerj** — uerj ou universidade do estado do rio de janeiro
- **uenf** — uenf ou universidade estadual do norte fluminense
- **cecierj** — cecierj ou educacao superior a distancia
- **faetec** — faetec ou fundacao de apoio a escola tecnica
- **subsis** — subsis
- **subcon** — subcon
- **subinov** — subinov
- **secti** — secretaria de estado de ciencia

---

## Os três ramos

Não são "ciência / tecnologia / inovação". São as **três subsecretarias**, que é
como a própria SECTI dividiu o assunto — e a divisão dela responde melhor: a
ciência mora no conhecimento, a inovação nos ambientes produtivos, e a
tecnologia atravessa os dois, que é como ela se comporta na prática. Um ramo só
para "tecnologia" seria artificial.


### Governança do sistema estadual

**SUBSIS** · Regimento, art. 26; Lei 9.809/2022

- politica estadual de ciencia
- sistema estadual de ciencia
- sistemas municipal ou is de ciencia
- consorcios intermunicipa
- plano de acao. … ciencia ou inovacao
- mapeamento tecnologico
- prospeccao tecnologica
- diagnostico. … tecnologic
- indicadores. … ciencia ou inovacao ou tecnolog
- cadastro estadual de icts
- redes de pesquisa
- grupos de pesquisa
- entidades vinculadas
- supervisao finalistica
- autonomia universitaria
- conselho estadual de ciencia
- camara tecnica. … ciencia ou inovacao
- foruns oficia

### Conhecimento, pesquisa e formação

**SUBCON** · Regimento, arts. 34 a 40

- pesquisa cientifica
- producao cientifica
- pos-graduacao
- ensino superior
- educacao tecnica ou tecnologica ou profissionalizante
- ensino tecnico ou tecnologico
- formacao. … recursos humanos
- capacitacao. … ciencia ou tecnolog ou inovacao
- bolsa de estimulo a inovacao
- bolsa de extensao tecnologica
- bolsa de pesquisa ou iniciacao ou mestrado ou doutorado ou pos-doutorado
- iniciacao cientifica
- compartilhamento de laboratorios
- capital intelectual
- tecnologias socia
- extensao tecnologica
- inclusao produtiva
- popularizacao da ciencia
- cultura cientifica
- divulgacao cientifica
- equidade racial ou de genero. … ciencia ou tecnolog ou inovacao
- laboratorio ou os de pesquisa
- pesquisadores ou as

### Inovação e ambientes produtivos

**SUBINOV** · Regimento, arts. 41 a 47

- parques tecnologic
- polos tecnologic
- incubadora
- aceleradora
- ambientes promotores da inovacao
- ambientes de inovacao
- startups
- startup rio
- empreendimentos inovador
- agencias de inovacao
- nucleos de inovacao tecnologica
- nits
- propriedade intelectual ou industrial
- transferencia de tecnologia
- encomenda tecnologica
- bonus tecnologico
- subvencao economica
- compras publicas em inovacao
- poder de compra. … inovacao
- participacao societaria. … inovacao
- inventor independente
- centros de pesquisa e desenvolvimento
- pesquisa, desenvolvimento e inovacao
- p&d ou pd&i
- inovacao aberta

---

## Termos genéricos: entram, mas marcados

Sozinhos não bastam. "Tecnologia" aparece em contrato de impressora e "inovação"
em jargão de atribuição de cargo. A matéria entra na base com confiança
**baixa**, e a tela pode escolher não mostrá-la enquanto ninguém conferir.

- tecnolog
- inovac
- cientific
- ciencia e tecnologia
- ciencia, tecnologia
- ciencias
- laboratori

---

## O ruído: apagado antes de qualquer busca

### A palavra mais traiçoeira do vocabulário jurídico é "ciência"

Em Diário Oficial ela quer dizer **ser notificado** muito mais vezes do que quer
dizer o campo do conhecimento: "tomar ciência do débito", "após a ciência do
lançamento", "fica o contribuinte cientificado".

Medido no corpus: **51 das 63 matérias que entraram por "ciência" eram isso** —
81% de erro num termo só, arrastando junto 48 matérias da SEFAZ cancelando
inscrição estadual, que não têm nada de CT&I.

E há uma armadilha dentro da armadilha. A primeira correção incluía `de` entre
os verbos de notificação, e passou a comer o nome da própria pasta: "Secretaria
de Estado **de Ciência**, Tecnologia e Inovação" virava "Secretaria de Estado,
Tecnologia e Inovação", e 148 matérias da SECTI deixaram de ser reconhecidas
como dela.

Os dois casos estão travados em teste, em `vocabulario.py`.

- dar ou ter ou tomar ou teve ou tomou ou deu ou apos a ciencia
- ciencia d palavra
- cientificar ou cientificado ou cientificada
- pesquisa de preco ou pesquisa de mercado
- melhoria ou inovacao
- inovacao em seus processos
