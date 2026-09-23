<?php

/**
 * Modelo de configuração. Copie para `config/config.php` e preencha.
 *
 * `config/config.php` NUNCA é versionado — ver o `.gitignore`. Senha de banco
 * não entra em repositório, não entra em documentação e não passa por conversa.
 */

declare(strict_types=1);

return [
    'ambiente' => 'desenvolvimento', // desenvolvimento | producao
    'debug'    => true,              // sempre false em produção

    'banco' => [
        'host'    => '127.0.0.1',
        'porta'   => 3306,
        'nome'    => 'doerj',
        'usuario' => '',
        'senha'   => '',
    ],

    /*
     * O aviso que aparece no rodapé de toda página.
     *
     * Enquanto este endereço for da hospedagem particular do responsável
     * técnico, ele precisa dizer isso: publicar em nome do órgão é ato do
     * órgão, e quem chega tem direito de saber onde está.
     */
    'homologacao' => true,
];
