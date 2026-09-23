<?php
/** As competências do art. 3º do regimento, e o que o Diário mostra de cada uma. */
declare(strict_types=1);

$itens = Interno::config()['regimento'];
$rotulo = static fn (array $i): string => 'Art. 3º, ' . $i['inciso'] . ' — ' . $i['tema'];
$detalhe = static fn (array $i): string => '';
$titulo_pagina = 'Regimento × Diário';
$explica = 'As competências que a minuta do regimento dá à SECTI, e quantas matérias '
    . 'do Diário Oficial tratam de cada uma. Competência sem matéria é uma pergunta '
    . 'a fazer: foi feito sem publicar, ou não foi feito?';

require __DIR__ . '/_itens.php';
