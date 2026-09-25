-- Uma republicação conserva o Id editorial do IOERJ, mas pertence a outra
-- edição. O Id é único dentro da edição, não no acervo inteiro.

ALTER TABLE atos
  DROP INDEX uq_ioerj,
  ADD UNIQUE KEY uq_edicao_ioerj (edicao_id, id_ioerj);
