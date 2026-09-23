<?php

/**
 * Carrega configuração, abre o banco e define os ajudantes que todas as
 * páginas usam.
 *
 * Sem framework e sem autoload de pacote: são cinco arquivos, e uma camada de
 * carregamento aqui seria mais código para resolver um problema que não existe.
 */

declare(strict_types=1);

define('RAIZ', dirname(__DIR__));

require RAIZ . '/app/Banco.php';
require RAIZ . '/app/Acervo.php';

/** @return array<string,mixed> */
function config(): array
{
    static $config = null;
    if ($config === null) {
        $arquivo = RAIZ . '/config/config.php';
        if (!is_file($arquivo)) {
            http_response_code(500);
            exit('Falta config/config.php. Copie de config/config.exemplo.php.');
        }
        $config = require $arquivo;
    }
    return $config;
}

function config_valor(string $chave, mixed $padrao = null): mixed
{
    return config()[$chave] ?? $padrao;
}

/**
 * Escapa para HTML.
 *
 * O nome é curto porque aparece em toda interpolação de view, e função de
 * escape que dá trabalho de escrever é função que alguém esquece.
 */
function e(?string $texto): string
{
    return htmlspecialchars($texto ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** 2026-09-22 vira 22/09/2026. */
function data_br(?string $iso): string
{
    if (!$iso) {
        return '—';
    }
    $d = DateTimeImmutable::createFromFormat('Y-m-d', substr($iso, 0, 10));
    return $d ? $d->format('d/m/Y') : $iso;
}

/**
 * Monta uma URL preservando os filtros que já estavam valendo.
 *
 * Quem está filtrando por órgão e clica numa categoria espera continuar
 * filtrado por órgão. Sem isto, cada clique zera o que a pessoa montou.
 */
function url_com(array $mudancas, string $caminho = '/busca'): string
{
    $atual = $_GET;
    foreach ($mudancas as $chave => $valor) {
        if ($valor === null || $valor === '') {
            unset($atual[$chave]);
        } else {
            $atual[$chave] = $valor;
        }
    }
    unset($atual['pagina']);
    $query = http_build_query($atual);
    return $caminho . ($query ? '?' . $query : '');
}

function ver(string $view, array $dados = []): void
{
    extract($dados, EXTR_SKIP);
    require RAIZ . '/app/Views/' . $view . '.php';
}
