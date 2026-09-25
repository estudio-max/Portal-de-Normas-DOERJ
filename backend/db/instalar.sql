-- Instalação completa do Portal de Normas DOERJ.
--
-- **Gerado de `backend/db/*.sql` por `tools/gerar_instalador.py`.** Não edite
-- à mão: mexa nas migrações e gere de novo, senão os dois divergem.
--
-- Para **banco vazio**, num arquivo só — é o que o phpMyAdmin da hospedagem
-- compartilhada aceita sem drama. Quem já tem o banco de pé aplica as
-- migrações uma a uma, na ordem do nome: o instalador cria tabela, e
-- `CREATE TABLE` em banco que já tem a tabela falha.
--
-- **Não cria o banco e não escolhe o banco.** Isso é do painel da hospedagem:
-- um `CREATE DATABASE` aqui falharia por falta de permissão ou, pior,
-- acertaria no banco errado.

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;


-- ========================================================================
-- 001-esquema.sql
-- ========================================================================
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


-- ========================================================================
-- 002-materias-sem-numero.sql
-- ========================================================================
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


-- ========================================================================
-- 003-relacao-parcial.sql
-- ========================================================================
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


-- ========================================================================
-- 004-vinculada.sql
-- ========================================================================
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


-- ========================================================================
-- 005-classificacao.sql
-- ========================================================================
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


-- ========================================================================
-- 006-impressao-do-texto.sql
-- ========================================================================
-- Uma impressão digital que sobrevive ao download.
--
-- Rodar depois de `005-classificacao.sql`.
--
--
-- CORREÇÃO DE UMA AFIRMAÇÃO ERRADA
--
-- A `001` diz, num comentário, que `edicoes.sha256` "permite provar depois que
-- o texto publicado aqui veio daqueles bytes". **Isso não se sustenta**, e só
-- apareceu quando o mesmo Diário foi baixado duas vezes:
--
--     baixada 1: 2.685.461 bytes, sha 3486f7fd...
--     baixada 2: 2.685.457 bytes, sha 8dd77124...
--
-- O IOERJ **gera um PDF novo a cada requisição**. O conteúdo é idêntico — 41
-- páginas, mesma data de criação interna, mesmo texto — mas o envelope muda.
-- O hash dos bytes identifica a cópia que nós lemos, e nada mais: ninguém
-- consegue rebaixar o arquivo e chegar ao mesmo número.
--
-- Como a promessa era justamente permitir conferência por terceiro, ela estava
-- vazia. Pior que vazia: um órgão de controle que tentasse usá-la concluiria
-- que o acervo foi adulterado, quando o que mudou foi o envelope.
--
--
-- O QUE FUNCIONA
--
-- O hash do **texto extraído e normalizado** é estável. As duas cópias acima
-- dão `2eb68d274928f0e3...`, com os mesmos 662.100 caracteres.
--
-- Esse é o número que serve de âncora: quem quiser conferir baixa o Diário da
-- data, extrai o texto, normaliza o espaço em branco e compara. O `sha256` dos
-- bytes continua guardado, porque registra o que foi lido naquele dia — mas
-- agora com o nome certo do que ele é.

ALTER TABLE edicoes
  ADD COLUMN sha256_texto CHAR(64) DEFAULT NULL
      COMMENT 'do texto extraído e normalizado. Estável entre downloads, ao contrário do sha256 dos bytes'
      AFTER sha256,
  ADD COLUMN caracteres INT UNSIGNED DEFAULT NULL
      COMMENT 'tamanho do texto normalizado, para conferência rápida'
      AFTER sha256_texto;

ALTER TABLE edicoes
  MODIFY COLUMN sha256 CHAR(64) DEFAULT NULL
      COMMENT 'dos bytes da cópia lida naquele dia. NÃO se reproduz: o IOERJ gera um PDF novo a cada requisição';


-- ========================================================================
-- 007-processo.sql
-- ========================================================================
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


-- ========================================================================
-- 008-rotulo.sql
-- ========================================================================
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


-- ========================================================================
-- 009-cabecalho-mais-longo.sql
-- ========================================================================
-- O cabeçalho cabia em 255 caracteres até uma instrução normativa de 378.
--
-- Não é caso raro que dá para ignorar: uma edição inteira, com 352 matérias,
-- deixou de carregar por causa de uma linha. O carregador grava cada edição numa
-- transação, o que é certo — meia edição no banco seria pior —, mas significa
-- que um campo apertado derruba tudo o que vem junto.
--
-- O extrator agora corta em 400. A coluna vai a 500 para que o corte dele seja
-- a única regra que decide, e não a largura da coluna: quando os dois limites
-- são iguais, quem bate primeiro é sorte.
--
-- O texto completo nunca esteve em risco. Vive em `ato_corpo`, e o cabeçalho é
-- derivado dele para efeito de título e de busca.

ALTER TABLE atos MODIFY COLUMN cabecalho VARCHAR(500) NULL
    COMMENT 'Bloco em caixa alta que abre a matéria. Cortado em 400 na extração.';


-- ========================================================================
-- 010-prazos.sql
-- ========================================================================
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


-- ========================================================================
-- 011-identidade-da-publicacao.sql
-- ========================================================================
-- Uma republicação conserva o Id editorial do IOERJ, mas pertence a outra
-- edição. O Id é único dentro da edição, não no acervo inteiro.

ALTER TABLE atos
  DROP INDEX uq_ioerj,
  ADD UNIQUE KEY uq_edicao_ioerj (edicao_id, id_ioerj);


SET FOREIGN_KEY_CHECKS = 1;
