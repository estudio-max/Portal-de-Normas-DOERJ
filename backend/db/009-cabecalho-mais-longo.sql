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
