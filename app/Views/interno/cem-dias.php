<?php
/** As ações do Planejamento 100 Dias, e o que o Diário mostra de cada uma. */
declare(strict_types=1);

$itens = Interno::config()['cem_dias'];
$rotulo = static fn (array $i): string => $i['acao'];
$detalhe = static fn (array $i): string => $i['detalhe'] ?? '';
$titulo_pagina = '100 Dias';
$explica = 'As ações do Planejamento 100 Dias da Inovação, e quantas matérias do '
    . 'Diário Oficial tratam de cada uma. Escolha uma ação para ver quais são.';

require __DIR__ . '/_itens.php';
