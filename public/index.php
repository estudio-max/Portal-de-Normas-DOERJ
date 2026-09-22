<?php
/**
 * Página de espera, enquanto o portal não existe.
 *
 * O domínio já está de pé e o portal não. Sem este arquivo, o endereço mostra a
 * página padrão da hospedagem ou a listagem do diretório — as duas contam ao
 * visitante coisas sobre o servidor que não são da conta dele.
 *
 * Os cabeçalhos de recusa de indexação também saem daqui, e a repetição em
 * relação ao `.htaccess` é deliberada: de lá eles cobrem arquivo estático, que
 * não passa pelo PHP; daqui eles sobrevivem a um servidor sem `mod_headers` ou
 * que ignore `.htaccess`. Como é `header()` sem `append`, a resposta sai com um
 * valor só.
 */

declare(strict_types=1);

header('X-Robots-Tag: noindex, nofollow, noarchive, nosnippet');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: same-origin');
header('Content-Type: text/html; charset=utf-8');

// A raiz responde 200; qualquer outro caminho responde 404.
//
// Sem isto, o front controller devolveria esta mesma página com 200 para
// qualquer endereço inventado, e um endereço inventado que responde 200 é uma
// página a mais no índice de quem estiver rastreando — justo o que o
// `X-Robots-Tag` acima tenta evitar.
$caminho = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
if (rtrim($caminho, '/') !== '' && $caminho !== '/index.php') {
    http_response_code(404);
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<title>Portal de Normas do DOERJ</title>
<style>
  :root {
    --tinta: #1b2733;
    --papel: #fbfaf8;
    --traco: #d9d4cc;
    --apoio: #5b6470;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-tema="claro"]) {
      --tinta: #e9edf2; --papel: #161b21; --traco: #333c46; --apoio: #9aa4b0;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 3rem 1rem;
    background: var(--papel);
    color: var(--tinta);
    font: 1rem/1.65 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex;
    justify-content: center;
  }
  main { max-width: 38rem; width: 100%; }
  h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 1.25rem; }
  p { margin: 0 0 1rem; }
  .fonte {
    margin-top: 2rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--traco);
    color: var(--apoio);
    font-size: .9rem;
  }
  a { color: inherit; }
</style>
</head>
<body>
<main>
  <h1>Portal de Normas do Diário Oficial do Estado do Rio de Janeiro</h1>

  <p>
    Este endereço vai reunir os atos do Poder Executivo estadual publicados no
    Diário Oficial, de um jeito em que dê para achar uma norma sem saber o dia
    em que ela saiu.
  </p>

  <p>Ainda está em construção. Não há nada para consultar por enquanto.</p>

  <p class="fonte">
    Os textos vêm do Diário Oficial publicado pela Imprensa Oficial do Estado do
    Rio de Janeiro. <strong>O arquivo de origem não tem valor legal</strong> — é
    o próprio IOERJ que o nomeia assim. Para uso que exija a publicação oficial,
    consulte <a href="https://www.ioerj.com.br/">ioerj.com.br</a>.
  </p>
</main>
</body>
</html>
