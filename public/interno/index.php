<?php

/**
 * A porta da área interna.
 *
 * DOIS CADEADOS. O primeiro é do servidor: esta pasta é protegida pela
 * "Privacidade de diretório" do cPanel, que pede usuário e senha antes de o PHP
 * sequer rodar. O usuário e a senha são criados lá, pelo João, e não passam por
 * este código nem pelo repositório.
 *
 * O segundo é este arquivo, e ele falha fechado: sem o servidor dizer quem
 * entrou, a página responde 403. Se a proteção do cPanel sumir — alguém a
 * desmarca, uma publicação sobrescreve o `.htaccess` desta pasta —, a área fica
 * trancada, e não aberta.
 *
 * SÓ `REMOTE_USER`. Ela é preenchida pelo Apache depois de conferir a senha. Já
 * `PHP_AUTH_USER` vem do cabeçalho que o próprio visitante manda: numa pasta sem
 * proteção, qualquer um escreveria ali o nome que quisesse e entraria.
 *
 * As rotas vão pelo `?p=`, e não por caminho: um endereço como
 * `/interno/prazos` não existe como arquivo, e o `.htaccess` da raiz o mandaria
 * para o portal público. Pelo `?p=`, toda requisição da área cai neste arquivo,
 * dentro da pasta protegida.
 */

declare(strict_types=1);

require dirname(__DIR__, 2) . '/app/bootstrap.php';
require RAIZ . '/app/Interno.php';

$debug = (bool) config_valor('debug', false);
ini_set('display_errors', $debug ? '1' : '0');
error_reporting(E_ALL);

cabecalhos_de_seguranca();
// Página interna não fica guardada em computador compartilhado nem em proxy.
header('Cache-Control: no-store, private');

$quem = (string) ($_SERVER['REMOTE_USER'] ?? $_SERVER['REDIRECT_REMOTE_USER'] ?? '');

// Sem senha só na máquina de desenvolvimento, e só se o config local pedir.
// As duas condições juntas: a chave sozinha num servidor esquecido não abre nada.
$local = (bool) config_valor('interno_local_sem_senha', false)
    && in_array($_SERVER['REMOTE_ADDR'] ?? '', ['127.0.0.1', '::1'], true);

if ($quem === '' && !$local) {
    http_response_code(403);
    ver('interno/fechado');
    exit;
}

$paineis = [
    'prazos'    => 'Prazos e compromissos',
    'cem-dias'  => '100 Dias',
    'regimento' => 'Regimento × Diário',
];
$p = (string) ($_GET['p'] ?? 'prazos');
if (!isset($paineis[$p])) {
    $p = 'prazos';
}

try {
    ver('interno/' . $p, ['paineis' => $paineis, 'painel' => $p, 'quem' => $quem ?: 'local']);
} catch (Throwable $erro) {
    error_log((string) $erro);
    http_response_code(500);
    ver('erro', [
        'codigo' => 500,
        'mensagem' => $debug ? $erro->getMessage() : 'Algo falhou aqui do nosso lado.',
    ]);
}
