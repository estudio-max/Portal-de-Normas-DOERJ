# Republicações do IOERJ: identidade da matéria

## Contexto

O extrator identificou 34 pares de matérias com o mesmo `Id:` do IOERJ em
edições diferentes. A amostra de 03/02/2025 traz a nota "Republicado por
incorreção no D.O. do dia 31/01/2025" e repete o ID `2623228` da publicação
original. Portanto, o identificador editorial não é único no acervo inteiro;
é único somente dentro da edição que o publicou.

Hoje `atos.id_ioerj` tem índice único e o carregador procura uma matéria apenas
por esse campo. Uma republicação atualiza a matéria da edição anterior e some
do histórico.

## Decisão

Guardar cada ocorrência publicada, inclusive republicações, mantendo o
`id_ioerj` exatamente como o Diário o imprimiu. A identidade de origem passa a
ser o par `(edicao_id, id_ioerj)`.

## Alterações

1. Criar migração que remove `uq_ioerj` e cria a unicidade composta
   `uq_edicao_ioerj (edicao_id, id_ioerj)`.
2. Atualizar o instalador completo com a mesma definição para instalações
   novas.
3. Fazer o carregador procurar e atualizar pelo par `(edicao_id, id_ioerj)`.
   Recarregar a mesma edição continua idempotente; carregar uma republicação
   cria uma nova matéria.
4. Manter os URLs existentes. Se uma republicação na mesma data gerar colisão
   no identificador público, o carregador acrescentará de forma determinística
   o caderno e a sequência apenas à nova ocorrência.
5. Corrigir os comentários e a documentação que tratam `id_ioerj` como chave
   global.

## Fora de escopo

- Deduzir relações semânticas entre o original e a republicação.
- Ocultar republicações na interface pública.
- Alterar o texto, o número ou a data publicados pelo Diário.

## Testes e verificação

- Autoteste do carregador: duas edições com o mesmo `id_ioerj` resultam em duas
  inserções; a recarga de uma delas resulta em atualização da própria linha.
- Teste de esquema contra MySQL: a unicidade composta aceita o par repetido em
  edições diferentes e rejeita a duplicação na mesma edição.
- Reprocessar o acervo e carregar uma base local limpa, conferindo que o total
  de matérias sobe de 120.994 IDs globais para 121.028 ocorrências publicadas.
- Executar classificação, relações, prazos e a suíte de regressão antes de
  publicar.

## Riscos e mitigação

A migração muda uma suposição de idempotência. A consulta composta e seus
testes preservam a reexecução segura. O campo editorial permanece intacto e a
edição já existe como entidade própria, de modo que a alteração não exige
inventar IDs de origem nem descartar documentos publicados.
