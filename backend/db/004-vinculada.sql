-- A vinculada que publicou, dentro do sistema da secretaria.
--
-- Rodar depois de `003-relacao-parcial.sql`.
--
--
-- POR QUE ISTO É UMA COLUNA, E NÃO UM DETALHE
--
-- No Diário, FAPERJ, UERJ, UENF, CECIERJ e FAETEC publicam sob o nome da
-- secretaria a que estão vinculadas. Quem lê o cabeçalho vê sempre "Secretaria
-- de Estado de Ciência, Tecnologia e Inovação", e o nome de quem de fato
-- publicou fica escondido nas primeiras linhas da matéria.
--
-- Sem separar as duas coisas, o sistema inteiro de CT&I do Estado vira um
-- balaio só, e não há como dar a cada vinculada o seu espaço organizado e
-- pesquisável.
--
-- `unidade` guarda o nome como o Diário escreveu. `unidade_slug` é o
-- normalizado, para agrupar — porque a mesma entidade aparece com grafias
-- diferentes, inclusive "EDUCAÇÃO SUPERIOR A DISTÂNCIA" e "À DISTÂNCIA" na
-- mesma semana.

ALTER TABLE atos
  ADD COLUMN unidade VARCHAR(200) DEFAULT NULL
      COMMENT 'a vinculada que publicou, como o Diário escreveu'
      AFTER orgao_slug,
  ADD COLUMN unidade_slug VARCHAR(120) DEFAULT NULL
      COMMENT 'normalizado, para agrupar grafias diferentes da mesma entidade'
      AFTER unidade,
  ADD KEY ix_unidade (unidade_slug);
