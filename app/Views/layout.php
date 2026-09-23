<?php
/**
 * O esqueleto de toda página.
 *
 * @var string $conteudo  já escapado pela view que chamou
 * @var string $titulo
 * @var string|null $descricao
 */
declare(strict_types=1);

$homologacao = (bool) config_valor('homologacao', true);
$caminho = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$atual = static fn (string $r): string => str_starts_with($caminho, $r)
    ? ' aria-current="page"' : '';
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!--
  A recusa de indexação sai daqui e do .htaccess, e a repetição é deliberada:
  de lá ela cobre arquivo estático; daqui ela sobrevive a um servidor sem
  mod_headers. Ver docs/publicacao.md.
-->
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<title><?= e($titulo) ?> — DOERJ fácil</title>
<?php if (!empty($descricao)): ?>
<meta name="description" content="<?= e($descricao) ?>">
<?php endif; ?>
<link rel="preload" href="/assets/fontes/nunito-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="<?= e(ativo('/assets/css/base.css')) ?>">
</head>
<body>

<a class="pular" href="#conteudo">Pular para o conteúdo</a>

<header class="cabecalho">
  <div class="cabecalho__marca">
    <svg class="cabecalho__simbolo" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2" stroke-linecap="round"
         stroke-linejoin="round" aria-hidden="true" focusable="false">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>
      <path d="M14 3v5h5"/>
      <path d="M9 13h6M9 17h4"/>
    </svg>
    <a href="/" class="cabecalho__titulo">
      <strong>DOERJ fácil</strong>
      <span>Diário Oficial do Estado do Rio de Janeiro</span>
    </a>
  </div>
<?php if (!empty($paineis)): ?>
  <nav class="cabecalho__nav" aria-label="Painéis da área interna">
<?php foreach ($paineis as $chave => $nome): ?>
    <a href="/interno/?p=<?= e($chave) ?>"<?= ($painel ?? '') === $chave ? ' aria-current="page"' : '' ?>><?= e($nome) ?></a>
<?php endforeach; ?>
    <a href="/">Portal público</a>
  </nav>
<?php else: ?>
  <nav class="cabecalho__nav" aria-label="Navegação principal">
    <a href="/"<?= $caminho === '/' ? ' aria-current="page"' : '' ?>>Início</a>
    <a href="/busca"<?= $atual('/busca') ?>>Buscar</a>
    <a href="/busca?cti=1"<?= '' ?>>Ciência, tecnologia e inovação</a>
    <a href="/sobre"<?= $atual('/sobre') ?>>Sobre</a>
  </nav>
<?php endif; ?>
</header>
<?php if (!empty($paineis)): ?>
<p class="faixa-interna">
  Área interna da SECTI. O conteúdo desta página não é público — não o encaminhe
  nem imprima para fora da equipe.
</p>
<?php endif; ?>

<main class="pagina<?= !empty($larga) ? ' pagina--larga' : '' ?>" id="conteudo">
<?= $conteudo ?>
</main>

<footer class="rodape">
  <p>
    Fonte: Diário Oficial do Estado do Rio de Janeiro, Parte I — Poder
    Executivo, publicado pela
    <a href="https://www.ioerj.com.br/">Imprensa Oficial do Estado</a>.
    <strong>O arquivo de origem não tem valor legal</strong> — é o próprio IOERJ
    que o nomeia assim. Para uso que exija a publicação oficial, consulte a fonte.
  </p>
  <p>
    A classificação por categoria e por tema é automática, feita por
    vocabulário, e está marcada como tal em cada ato. Ela erra, e por isso
    aparece identificada em vez de silenciosa.
  </p>
<?php if ($homologacao): ?>
  <p>Ambiente de homologação. Não é publicação oficial do órgão.</p>
<?php endif; ?>
</footer>

</body>
</html>
