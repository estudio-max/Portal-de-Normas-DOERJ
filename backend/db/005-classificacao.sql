-- Os dois eixos de classificação.
--
-- Rodar depois de `004-vinculada.sql`.
--
--
-- POR QUE SÃO DUAS TABELAS, E NÃO DUAS COLUNAS
--
-- Uma matéria faz mais de uma coisa ao mesmo tempo, e isso não é exceção: um
-- despacho que autoriza a celebração de um contrato é despacho **e** contrato;
-- um edital de pregão para equipar laboratório é compra **e** contrato.
--
-- Medido em 2.012 matérias: a maioria das classificadas recebe duas ou três
-- categorias. Uma coluna só obrigaria a escolher uma, e a escolha seria
-- arbitrária — a tela mostraria "Contratos" para um ato que a pessoa procurava
-- em "Compras", e ela concluiria que o acervo não tem.
--
--
-- POR QUE A ORIGEM VIAJA JUNTO COM CADA LINHA
--
-- Nada disto foi conferido por pessoa. A classificação sai de vocabulário, e
-- vocabulário erra. `origem` começa em 'automatico' e vira 'conferido' quando
-- alguém olhar — e a tela tem que mostrar a diferença a quem lê, do mesmo jeito
-- que `ementa_inferida` faz com a ementa.
--
-- Sem isso, o portal afirma com a mesma cara o que a máquina supôs e o que a
-- pessoa confirmou.

ALTER TABLE atos
  ADD COLUMN e_cti TINYINT(1) NOT NULL DEFAULT 0
      COMMENT 'passou no recorte de ciência, tecnologia e inovação'
      AFTER unidade_slug,
  ADD COLUMN confianca ENUM('alta','media','baixa') DEFAULT NULL
      COMMENT 'alta: âncora legal ou entidade do sistema. baixa: só termo genérico'
      AFTER e_cti,
  ADD COLUMN porque_cti VARCHAR(80) DEFAULT NULL
      COMMENT 'o que fez a matéria entrar no recorte, para poder ser contestado'
      AFTER confianca,
  ADD COLUMN entidade_sistema VARCHAR(20) DEFAULT NULL
      COMMENT 'faperj, uerj, uenf, cecierj, faetec, secti'
      AFTER porque_cti,
  ADD KEY ix_cti (e_cti, confianca),
  ADD KEY ix_entidade_sistema (entidade_sistema);


-- ---------------------------------------------------------------------------
-- Eixo 1 — o que o ato faz. Onze categorias, derivadas dos rótulos que o
-- próprio Diário usa e medidas antes de virarem código.
-- ---------------------------------------------------------------------------

CREATE TABLE ato_natureza (
  ato_id    VARCHAR(191) NOT NULL,
  natureza  VARCHAR(20)  NOT NULL
            COMMENT 'contratos, academico, compras, pessoal, governanca, comissoes, orcamento, fomento, despachos, contencioso, retificacoes',
  origem    ENUM('automatico','conferido') NOT NULL DEFAULT 'automatico',

  PRIMARY KEY (ato_id, natureza),
  KEY ix_natureza (natureza, origem),
  CONSTRAINT fk_natureza_ato FOREIGN KEY (ato_id)
    REFERENCES atos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------------
-- Eixo 2 — o ramo de CT&I, que são as três subsecretarias da SECTI.
--
-- Só as matérias com conteúdo temático recebem ramo, e são poucas: o sistema
-- publica sobretudo ato administrativo. Matéria da FAPERJ sem ramo continua
-- sendo da FAPERJ, pela coluna `entidade_sistema`.
-- ---------------------------------------------------------------------------

CREATE TABLE ato_ramo (
  ato_id  VARCHAR(191) NOT NULL,
  ramo    VARCHAR(20)  NOT NULL
          COMMENT 'governanca (SUBSIS), conhecimento (SUBCON), inovacao (SUBINOV)',
  origem  ENUM('automatico','conferido') NOT NULL DEFAULT 'automatico',

  PRIMARY KEY (ato_id, ramo),
  KEY ix_ramo (ramo, origem),
  CONSTRAINT fk_ramo_ato FOREIGN KEY (ato_id)
    REFERENCES atos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
