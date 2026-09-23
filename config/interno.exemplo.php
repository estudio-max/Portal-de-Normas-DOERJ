<?php
/**
 * Modelo do `config/interno.php`, que NÃO se versiona.
 *
 * O arquivo de verdade guarda o planejamento interno da SECTI — as ações do
 * Planejamento 100 Dias e as competências do regimento, cada uma com a busca que
 * a representa. Fica fora do git para que, se o repositório for aberto um dia
 * (DP-03), o planejamento não vá junto com o código.
 *
 * Copie para `config/interno.php` e preencha. Formato de `expr`: modo booleano
 * do índice de texto do MySQL — espaço separa alternativas, aspas fazem frase,
 * `*` no fim aceita qualquer final, `+` torna obrigatório. Sem acento.
 */
declare(strict_types=1);

return [
    'cem_dias' => [
        [
            'acao'    => 'Nome da ação',
            'detalhe' => 'O que ela inclui, em uma frase.',
            'expr'    => '"frase exata" palavra prefixo*',
            'so_cti'  => false,
        ],
    ],
    'regimento' => [
        ['inciso' => 'I', 'tema' => 'Tema da competência', 'expr' => '"frase exata"', 'so_cti' => false],
    ],
];
