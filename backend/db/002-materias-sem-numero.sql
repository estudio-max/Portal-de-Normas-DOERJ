-- Ajusta `atos` ao que o Diário realmente publica.
--
-- Rodar depois de `001-esquema.sql`.
--
--
-- POR QUE ESTA MIGRAÇÃO EXISTE
--
-- O `001-esquema.sql` foi escrito antes de eu ter lido um Diário inteiro. Ele
-- supunha que todo ato tem número, como no portal da UFF. A Fase 4 mediu, e a
-- suposição estava errada:
--
--   **entre 77% e 87% das matérias publicadas não têm número.**
--
-- São "ATOS DO SECRETÁRIO", "DESPACHOS DO SECRETÁRIO", "RETIFICAÇÃO" e,
-- sobretudo, movimentação de pessoal. Com `numero NOT NULL`, carregar o Diário
-- de um dia significaria jogar fora quatro quintos dele, ou inventar número
-- para o que não tem. As duas saídas são piores que a coluna aceitar nulo.
--
-- A outra mudança é a chave natural da edição. O IOERJ fecha cada matéria
-- publicada com um `Id: 2765345`, e esse número é dele, não nosso. Ele pode
-- reaparecer numa republicação, portanto a identidade completa é a edição mais
-- esse ID. Recarregar a mesma edição atualiza as mesmas linhas.

ALTER TABLE atos
  -- O identificador da própria Imprensa Oficial. É único na edição: o Diário
  -- pode republicar a mesma matéria, preservando o número editorial.
  ADD COLUMN id_ioerj VARCHAR(16) DEFAULT NULL
      COMMENT 'o "Id:" que fecha a matéria no PDF. Chave natural da origem'
      AFTER edicao_id,

  -- A linha de cabeçalho como o Diário escreveu, sem normalizar. Quando o
  -- reconhecimento errar, é por aqui que se descobre o que ele viu.
  ADD COLUMN cabecalho VARCHAR(255) DEFAULT NULL AFTER ementa_inferida,

  -- Falso quando não há ato numerado na matéria. Não é o mesmo que "numero IS
  -- NULL": uma matéria pode trazer ato numerado e o número falhar na leitura, e
  -- essas duas situações pedem tratamento diferente na curadoria.
  ADD COLUMN reconhecido TINYINT(1) NOT NULL DEFAULT 0 AFTER cabecalho,

  -- Quantos cabeçalhos de ato a matéria traz. Maior que 1 é fila de trabalho:
  -- são vários atos guardados numa linha só, ainda por separar.
  ADD COLUMN atos_no_texto SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER reconhecido,

  MODIFY COLUMN tipo   VARCHAR(60) DEFAULT NULL,
  MODIFY COLUMN numero VARCHAR(32) DEFAULT NULL,

  ADD UNIQUE KEY uq_ioerj (id_ioerj),
  ADD KEY ix_reconhecido (reconhecido);
