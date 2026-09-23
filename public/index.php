<?php

/**
 * Front controller único. Todo o tráfego passa por aqui, via `.htaccess`.
 *
 * Roteamento por `match` e não por tabela de rotas: são quatro caminhos, e uma
 * camada de roteamento seria mais código do que o que ela organizaria.
 */

declare(strict_types=1);

require dirname(__DIR__) . '/app/bootstrap.php';

$debug = (bool) config_valor('debug', false);
ini_set('display_errors', $debug ? '1' : '0');
error_reporting(E_ALL);

/*
 * Os cabeçalhos repetem o que o `.htaccess` já manda, e a repetição é
 * deliberada: de lá eles cobrem arquivo estático, que não passa pelo PHP;
 * daqui eles sobrevivem a um servidor sem `mod_headers` ou que ignore
 * `.htaccess`. Como os dois usam `set`, a resposta sai com um valor só.
 */
header('X-Robots-Tag: noindex, nofollow, noarchive, nosnippet');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: same-origin');
/*
 * Nada de terceiro é carregado: a fonte e o CSS são servidos daqui. Sem
 * `font-src` de propósito — ele cai em `default-src 'self'`, e fonte de CDN
 * entregaria o endereço de rede de cada visitante a mais alguém.
 */
header(
    "Content-Security-Policy: default-src 'self'; img-src 'self' data:; "
    . "style-src 'self'; script-src 'none'; base-uri 'none'; form-action 'self'; "
    . "frame-ancestors 'self'"
);
header('Content-Type: text/html; charset=utf-8');

$caminho = rtrim(parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/', '/');
if ($caminho === '') {
    $caminho = '/';
}

try {
    if ($caminho === '/') {
        ver('home');
    } elseif ($caminho === '/busca') {
        $filtros = [
            'q'        => trim((string) ($_GET['q'] ?? '')),
            'natureza' => (string) ($_GET['natureza'] ?? ''),
            'ramo'     => (string) ($_GET['ramo'] ?? ''),
            'entidade' => (string) ($_GET['entidade'] ?? ''),
            'tipo'     => (string) ($_GET['tipo'] ?? ''),
            'cti'      => (string) ($_GET['cti'] ?? ''),
            'status'   => (string) ($_GET['status'] ?? ''),
            'de'       => (string) ($_GET['de'] ?? ''),
            'ate'      => (string) ($_GET['ate'] ?? ''),
        ];
        // Filtro que não é de uma lista conhecida vira vazio. Não é sobre
        // injeção — a consulta é parametrizada —, é sobre não devolver zero
        // resultado por causa de um valor que nunca existiu.
        $vigencias = ['Ativo' => 1, 'Alterado' => 1, 'Revogado' => 1];
        foreach (['natureza' => Acervo::NATUREZAS, 'ramo' => Acervo::RAMOS,
                  'entidade' => Acervo::ENTIDADES,
                  'status' => $vigencias] as $chave => $validos) {
            if ($filtros[$chave] !== '' && !isset($validos[$filtros[$chave]])) {
                $filtros[$chave] = '';
            }
        }
        $pagina = max(1, (int) ($_GET['pagina'] ?? 1));
        ver('busca', [
            'filtros'   => $filtros,
            'resultado' => Acervo::buscar($filtros, $pagina),
            'pagina'    => $pagina,
        ]);
    } elseif (str_starts_with($caminho, '/ato/')) {
        $id = substr($caminho, strlen('/ato/'));
        $ato = Acervo::ato(rawurldecode($id));
        if (!$ato) {
            http_response_code(404);
            ver('erro', ['codigo' => 404, 'mensagem' => 'Esta matéria não está no acervo.']);
        } else {
            ver('ato', ['ato' => $ato]);
        }
    } elseif ($caminho === '/sobre') {
        ver('sobre');
    } else {
        http_response_code(404);
        ver('erro', ['codigo' => 404, 'mensagem' => 'Página não encontrada.']);
    }
} catch (Throwable $erro) {
    error_log((string) $erro);
    http_response_code(500);
    // Em produção a mensagem do erro não vai para a tela: ela conta ao
    // visitante detalhes do servidor que não são da conta dele.
    ver('erro', [
        'codigo' => 500,
        'mensagem' => $debug ? $erro->getMessage() : 'Algo falhou aqui do nosso lado.',
    ]);
}
