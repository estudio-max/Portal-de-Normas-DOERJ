-- O número do processo, e um índice para a vigência.
--
-- Rodar depois de `006-impressao-do-texto.sql`.
--
-- `processo` aparece em **91% das matérias**, e é a chave que liga edital,
-- contrato, aditivo e pagamento do mesmo objeto. Sem ele, cada ato é um ponto
-- solto; com ele, dá para seguir uma decisão do começo ao fim.
--
-- Dois formatos convivem: o SEI atual (`SEI-260003/010809/2024`) e o antigo
-- (`E-26/003.123/2010`), que ainda aparece nas edições de 2010 e 2013. A coluna
-- guarda como o ato escreveu, sem normalizar — normalizar formato de processo é
-- palpite sobre uma numeração que não é nossa.

ALTER TABLE atos
  ADD COLUMN processo VARCHAR(40) DEFAULT NULL
      COMMENT 'número do processo, como o ato escreve. Liga os atos do mesmo objeto'
      AFTER entidade_sistema,
  ADD KEY ix_processo (processo);
