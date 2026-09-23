-- Os prazos dos instrumentos: contratos, convênios, acordos, termos aditivos.
--
-- Pedido do João em 2026-09-23: acordos e metas da SECTI têm data, a gestão
-- atual pode não saber o que foi combinado antes dela, e perder o prazo. O
-- Diário publica o extrato de cada instrumento com a vigência — é daí que sai
-- esta tabela, lida pelo `tools/doerj_prazos.py`.
--
-- Uma linha por INSTRUMENTO, e não por matéria: um único "EXTRATOS DE TERMOS"
-- empilha vários instrumentos, cada um com partes, objeto e prazo próprios.
--
-- O dado é público — é o extrato publicado. O painel que mostra os prazos é que
-- fica na área interna, porque o objetivo dele é avisar a gestão.

CREATE TABLE IF NOT EXISTS ato_prazo (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ato_id       VARCHAR(191) NOT NULL,
  ordem        SMALLINT UNSIGNED NOT NULL COMMENT 'Posição do instrumento dentro da matéria',
  instrumento  VARCHAR(300) DEFAULT NULL COMMENT 'Como o extrato o nomeia: "2º Termo Aditivo ao Contrato nº 001/2024"',
  partes       VARCHAR(500) DEFAULT NULL,
  objeto       VARCHAR(700) DEFAULT NULL,
  valor        VARCHAR(160) DEFAULT NULL COMMENT 'Como publicado. Texto, e não número: "Sem acréscimo de valores" também é valor',
  processo     VARCHAR(60)  DEFAULT NULL,
  assinatura   DATE DEFAULT NULL,
  inicio       DATE DEFAULT NULL,
  fim          DATE DEFAULT NULL,
  como         VARCHAR(40)  NOT NULL COMMENT 'De onde saiu o fim: datas explícitas, ou duração somada a qual início',
  PRIMARY KEY (id),
  KEY ix_ato (ato_id),
  KEY ix_fim (fim),
  CONSTRAINT fk_prazo_ato FOREIGN KEY (ato_id) REFERENCES atos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
