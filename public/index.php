<?php
/**
 * Página de espera, enquanto o portal não existe.
 *
 * O domínio já está de pé e o portal não. Sem este arquivo, o endereço mostra a
 * página padrão da hospedagem ou a listagem do diretório — as duas contam ao
 * visitante coisas sobre o servidor que não são da conta dele.
 *
 * A identidade visual é a do Mapa de CT&I: mesmas cores, mesma fonte, mesma
 * diagramação. São dois produtos da mesma secretaria.
 *
 * Os cabeçalhos de recusa de indexação também saem daqui, e a repetição em
 * relação ao `.htaccess` é deliberada: de lá eles cobrem arquivo estático, que
 * não passa pelo PHP; daqui eles sobrevivem a um servidor sem `mod_headers` ou
 * que ignore `.htaccess`.
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
<title>Portal de Normas do DOERJ — SECTI-RJ</title>
<meta name="description" content="Atos do Poder Executivo do Estado do Rio de Janeiro publicados no Diário Oficial.">
<!--
  A fonte é pré-carregada sem `?v=`: o `@font-face` no CSS aponta para o caminho
  literal, e endereço diferente faz o navegador baixar o arquivo duas vezes.
-->
<link rel="preload" href="/assets/fontes/nunito-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/base.css">
</head>
<body>

<header class="cabecalho">
  <div class="cabecalho__marca">
    <!--
      Documento com dobra: diz Diário Oficial sem escrever, e conversa com o
      alfinete de mapa do outro produto. Traço grosso porque em 2,3rem um traço
      fino some.
    -->
    <svg class="cabecalho__simbolo" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round"
         stroke-linejoin="round" aria-hidden="true" focusable="false">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>
      <path d="M14 3v5h5"/>
      <path d="M9 13h6M9 17h4"/>
    </svg>
    <a href="/" class="cabecalho__titulo">
      <strong>SECTI-RJ</strong>
      <span>Portal de Normas do Diário Oficial</span>
    </a>
  </div>
</header>

<main class="pagina">
  <h1>Atos do Poder Executivo do Estado do Rio de Janeiro</h1>

  <div class="prosa">
    <p>
      Este endereço vai reunir o que o Estado publicou no Diário Oficial, de um
      jeito em que dê para achar uma norma sem saber o dia em que ela saiu.
    </p>

    <p><strong>Ainda está em construção.</strong> Não há nada para consultar por enquanto.</p>

    <p class="ressalva">
      Quando estiver no ar, os textos virão do Diário Oficial publicado pela
      Imprensa Oficial do Estado do Rio de Janeiro. <strong>O arquivo de origem
      não tem valor legal</strong> — é o próprio IOERJ que o nomeia assim. Para
      uso que exija a publicação oficial, consulte
      <a href="https://www.ioerj.com.br/">ioerj.com.br</a>.
    </p>
  </div>
</main>

<footer class="rodape">
  <p>
    Fonte: Diário Oficial do Estado do Rio de Janeiro, Parte I — Poder Executivo,
    publicado pela Imprensa Oficial do Estado do Rio de Janeiro.
  </p>
  <p>
    Ambiente de homologação. Não é publicação oficial do órgão.
  </p>
</footer>

</body>
</html>
