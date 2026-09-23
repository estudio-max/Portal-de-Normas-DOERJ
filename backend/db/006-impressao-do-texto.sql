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
