-- O rótulo com que o Diário abre a matéria.
--
-- Rodar depois de `007-processo.sql`.
--
-- 84% das matérias não têm ato numerado. Sem esta coluna, a lista mostra
-- "Matéria de 22/09/2026" em linha após linha — informação nenhuma, repetida
-- vinte vezes por página.
--
-- O Diário já resolve isso sozinho: abre cada matéria com uma etiqueta —
-- "EXTRATO DE TERMO ADITIVO", "DESPACHO DO ORDENADOR DE DESPESAS",
-- "RETIFICAÇÃO". É a etiqueta dele, não uma inventada aqui.

ALTER TABLE atos
  ADD COLUMN rotulo VARCHAR(80) DEFAULT NULL
      COMMENT 'a etiqueta com que o Diário abre a matéria, quando não há ato numerado'
      AFTER cabecalho;
