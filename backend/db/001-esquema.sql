-- Esquema do Portal de Normas DOERJ.
--
-- Decalcado do Portal de Normas e Atos da UFF, para quem cuida dos dois não ter
-- que aprender duas modelagens. Os nomes de tabela e de coluna seguem os de lá
-- onde o sentido é o mesmo, e só divergem onde o DOERJ é diferente de verdade.
--
-- MySQL 5.7 ou mais novo. InnoDB, utf8mb4.
--
--
-- O QUE FICA GUARDADO, E O QUE NÃO FICA
--
-- O PDF **não** fica. Fica o texto extraído e o endereço do PDF na origem.
--
-- Isso só é possível porque a chave do IOERJ é permanente: a chave da edição de
-- 15/01/2010 continuava servindo o arquivo em 22/09/2026, o mesmo dia em que foi
-- capturada a de hoje. O endereço é durável, não é link de sessão.
--
-- Em compensação, o endereço aponta para servidor de terceiro, e não para o
-- nosso. Se o IOERJ mudar o esquema, todos os links quebram de uma vez e não há
-- cópia para onde correr. Duas defesas baratas, e as duas estão aqui:
--
--   1. `edicoes.guid` guarda o identificador cru. Se a forma de montar a URL
--      mudar, a URL se remonta de uma vez só, com um UPDATE.
--   2. `edicoes.sha256` guarda a impressão digital do arquivo lido.
--
--      **ATENÇÃO: a frase que estava aqui estava errada.** Ela dizia que este
--      hash permitiria provar depois que o texto veio daqueles bytes. Não
--      permite: o IOERJ gera um PDF novo a cada requisição, e o mesmo Diário
--      baixado duas vezes dá hashes diferentes. Quem serve para isso é o
--      `sha256_texto`, criado na migração `006`. Leia-a antes de confiar neste
--      campo.
--
-- Nenhuma das duas devolve o arquivo. Se o acervo de origem sumir, o portal
-- continua funcionando como texto e perde a prova. É a troca que a decisão de
-- não guardar PDF implica, e está escrita aqui para não ser redescoberta com
-- espanto daqui a dois anos.

SET NAMES utf8mb4;
SET time_zone = '-03:00';


-- ---------------------------------------------------------------------------
-- edicoes — um caderno do Diário, de um dia
-- ---------------------------------------------------------------------------
-- Equivale ao `boletins` da UFF. Mudou de nome porque no DOERJ a unidade
-- publicada é a edição de um caderno, e o mesmo dia tem vários cadernos.

CREATE TABLE edicoes (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,

  data_pub       DATE         NOT NULL,
  caderno        VARCHAR(80)  NOT NULL COMMENT 'Parte I (Poder Executivo), Parte IB..., como o IOERJ escreve',
  caderno_slug   VARCHAR(80)  NOT NULL COMMENT 'parte-i-poder-executivo. O mesmo que o downloader usa no nome do arquivo',

  -- Dia com edição extra repete o caderno. 15/01/2024 tem duas "Parte I".
  sequencia      TINYINT UNSIGNED NOT NULL DEFAULT 1,

  -- O que aparece na capa: ANO LII - Nº 173.
  ano_romano     VARCHAR(12)  DEFAULT NULL,
  numero         VARCHAR(12)  DEFAULT NULL,

  guid           CHAR(36)     NOT NULL COMMENT 'identificador do IOERJ. A URL se monta a partir dele',
  url_pdf        VARCHAR(255) NOT NULL COMMENT 'endereço do PDF na origem. O arquivo não fica aqui',

  paginas        SMALLINT UNSIGNED DEFAULT NULL,
  bytes          INT UNSIGNED      DEFAULT NULL,
  sha256         CHAR(64)          DEFAULT NULL COMMENT 'do PDF de onde o texto saiu. Ver o cabeçalho',

  coletado_em    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  extraido_em    TIMESTAMP    NULL DEFAULT NULL COMMENT 'nulo enquanto o texto não foi separado em atos',

  PRIMARY KEY (id),
  UNIQUE KEY uq_edicao (data_pub, caderno_slug, sequencia),
  UNIQUE KEY uq_guid (guid),
  KEY ix_data (data_pub),
  KEY ix_pendente (extraido_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------------
-- atos — cada norma, individualmente
-- ---------------------------------------------------------------------------

CREATE TABLE atos (
  -- Id legível, como na UFF: entra na URL pública e sobrevive a reimportação.
  -- Ex.: 2026-09-22-decreto-49123.
  id             VARCHAR(191) NOT NULL,
  edicao_id      INT UNSIGNED DEFAULT NULL,

  tipo           VARCHAR(60)  NOT NULL COMMENT 'Decreto, Resolução, Portaria, Deliberação...',
  numero         VARCHAR(32)  NOT NULL,
  ano            SMALLINT UNSIGNED DEFAULT NULL,
  data_ato       DATE         DEFAULT NULL COMMENT 'a data da assinatura, que não é sempre a da publicação',
  data_pub       DATE         NOT NULL,

  -- No DOERJ o que organiza é a estrutura do Executivo estadual, não unidades
  -- de universidade. `orgao` é o que vem escrito; `orgao_slug` é o normalizado,
  -- porque a mesma secretaria aparece com grafias diferentes ao longo dos anos.
  orgao          VARCHAR(200) DEFAULT NULL,
  orgao_slug     VARCHAR(120) DEFAULT NULL,

  ementa         TEXT         DEFAULT NULL,

  -- A UFF aprendeu isto na marra e vale repetir: ementa deduzida não é ementa
  -- publicada, e misturar as duas faz o portal afirmar o que ninguém escreveu.
  ementa_inferida TINYINT(1)  NOT NULL DEFAULT 0,

  signatario     VARCHAR(200) DEFAULT NULL,
  pagina         VARCHAR(8)   DEFAULT NULL,

  status         ENUM('Ativo','Alterado','Revogado') NOT NULL DEFAULT 'Ativo',

  -- Quem disse que o status é esse. Enquanto a cadeia de alterações for
  -- detectada por regra automática, quem lê tem direito de saber disso.
  status_origem  ENUM('automatico','conferido') NOT NULL DEFAULT 'automatico',

  criado_em      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY ix_tipo (tipo),
  KEY ix_numero (numero),
  KEY ix_ano (ano),
  KEY ix_data_pub (data_pub),
  KEY ix_orgao (orgao_slug),
  KEY ix_status (status),
  KEY ix_edicao (edicao_id),
  FULLTEXT KEY ft_ementa (ementa),
  CONSTRAINT fk_ato_edicao FOREIGN KEY (edicao_id)
    REFERENCES edicoes (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------------
-- ato_corpo — o texto inteiro, separado
-- ---------------------------------------------------------------------------
-- Tabela à parte, como na UFF. O texto é grande e quase nunca é lido junto com
-- a listagem: deixá-lo na mesma tabela faria toda consulta de busca arrastar
-- megabytes que ninguém pediu.

CREATE TABLE ato_corpo (
  ato_id  VARCHAR(191) NOT NULL,
  texto   MEDIUMTEXT   DEFAULT NULL,

  PRIMARY KEY (ato_id),
  FULLTEXT KEY ft_texto (texto),
  CONSTRAINT fk_corpo_ato FOREIGN KEY (ato_id)
    REFERENCES atos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------------------
-- ato_relacoes — o que altera o quê
-- ---------------------------------------------------------------------------
-- É isto que responde "essa norma ainda vale?", que é a pergunta que as pessoas
-- realmente fazem. A relação está escrita em prosa dentro do ato, não num
-- campo, então quase sempre começa como texto solto e só depois vira ligação.
--
-- Por isso `ato_destino_texto` é obrigatório e `ato_destino_id` não é: dá para
-- registrar "altera a Resolução nº 123" antes de saber qual registro é esse.

CREATE TABLE ato_relacoes (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ato_id            VARCHAR(191) NOT NULL,

  tipo_relacao      ENUM('Altera','Revoga','Retifica','Republica','Regulamenta','Cita')
                    NOT NULL,

  ato_destino_texto VARCHAR(200) NOT NULL COMMENT 'como o ato se refere ao outro, em prosa',
  ato_destino_id    VARCHAR(191) DEFAULT NULL COMMENT 'nulo enquanto não se sabe qual é',
  externo           TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'aponta para norma que não é do DOERJ',

  origem            ENUM('automatico','conferido') NOT NULL DEFAULT 'automatico',
  detalhes          VARCHAR(255) DEFAULT NULL,

  PRIMARY KEY (id),
  KEY ix_ato (ato_id),
  KEY ix_destino (ato_destino_id),
  KEY ix_tipo (tipo_relacao),
  CONSTRAINT fk_rel_ato FOREIGN KEY (ato_id)
    REFERENCES atos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
