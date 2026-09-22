-- Distingue "revoga a norma" de "revoga um artigo da norma".
--
-- Rodar depois de `002-materias-sem-numero.sql`.
--
--
-- O CASO QUE OBRIGOU ESTA COLUNA
--
-- A Resolução SES/SMS 4.281, de 17/09/2026, faz duas coisas com a Resolução
-- Conjunta SES/SMS/RJ nº 564, de 2018:
--
--     "Fica alterado o art. 1º da Resolução Conjunta ... nº 564"
--     "Fica revogado  o art. 2º da Resolução Conjunta ... nº 564"
--
-- As duas relações são verdadeiras. Mas **a Resolução 564 continua em vigor**:
-- o que caiu foi um artigo dela.
--
-- Sem esta coluna, um portal que lesse `tipo_relacao = 'Revoga'` marcaria a
-- Resolução 564 como revogada e diria a quem consulta que uma norma viva está
-- morta. Esse é exatamente o erro que este projeto existe para não cometer.
--
-- Regra que vale para quem for escrever a tela: **só revogação com
-- `parcial = 0` derruba o status da norma alvo.**

ALTER TABLE ato_relacoes
  ADD COLUMN parcial TINYINT(1) NOT NULL DEFAULT 0
      COMMENT 'atinge só um artigo ou dispositivo, e não a norma inteira'
      AFTER externo,
  ADD COLUMN dispositivo VARCHAR(60) DEFAULT NULL
      COMMENT 'qual artigo ou anexo, como o ato escreveu'
      AFTER parcial;
