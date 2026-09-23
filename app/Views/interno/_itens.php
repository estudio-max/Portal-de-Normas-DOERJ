<?php
/**
 * A tela comum do 100 Dias e do Regimento × Diário: cada item com quantas
 * matérias do Diário tratam dele, e — ao escolher um — quais são.
 *
 * Tabela, e não gráfico: são de 5 a 22 itens com um número cada, e o que importa
 * é ler o nome do item ao lado do número. O zero ganha destaque, porque é o que
 * esta tela existe para mostrar.
 *
 * Quem inclui define: $itens (da config interna), $rotulo (fn item => nome),
 * $detalhe (fn item => frase), $titulo_pagina, $explica, $painel.
 *
 * @var array $itens
 * @var callable $rotulo
 * @var callable $detalhe
 * @var string $titulo_pagina
 * @var string $explica
 * @var string $painel
 */
declare(strict_types=1);
ob_start();

$itens = Interno::contar($itens);
$escolhido = isset($_GET['item']) && ctype_digit((string) $_GET['item']) && isset($itens[(int) $_GET['item']])
    ? (int) $_GET['item'] : null;
$sem = count(array_filter($itens, static fn ($i) => $i['n'] === 0));
?>

<header class="cabeca">
  <h1><?= e($titulo_pagina) ?></h1>
  <p class="apoio"><?= e($explica) ?></p>
</header>

<?php if (!$itens): ?>
<div class="quadro vazio">
  <p class="vazio__titulo">A configuração interna não está neste servidor.</p>
  <p class="vazio__dica">O arquivo <code>config/interno.php</code> precisa ser copiado para cá.</p>
</div>
<?php else: ?>

<div class="numeros-prazo">
  <p class="numero-prazo"><strong><?= count($itens) ?></strong><span>itens</span></p>
  <p class="numero-prazo<?= $sem ? ' numero-prazo--alerta' : '' ?>">
    <strong><?= $sem ?></strong><span>sem nenhuma matéria no Diário</span>
  </p>
</div>

<div class="quadro">
  <div class="tabela-rolante">
  <table class="tabela-atos tabela-itens">
    <thead>
      <tr>
        <th scope="col">Item</th>
        <th scope="col" class="col-numero">Matérias no Diário</th>
      </tr>
    </thead>
    <tbody>
<?php foreach ($itens as $k => $i): ?>
      <tr<?= $k === $escolhido ? ' class="escolhido"' : '' ?>>
        <td>
          <a class="especie__nome" href="/interno/?p=<?= e($painel) ?>&amp;item=<?= $k ?>#materias"><?= e($rotulo($i)) ?></a>
<?php if ($detalhe($i) !== ''): ?>
          <p class="ementa"><?= e($detalhe($i)) ?></p>
<?php endif; ?>
        </td>
        <td class="col-numero">
<?php if ($i['n'] === 0): ?>
          <span class="selo selo--revogado">nenhuma</span>
<?php else: ?>
          <strong><?= number_format($i['n'], 0, ',', '.') ?></strong>
<?php endif; ?>
        </td>
      </tr>
<?php endforeach; ?>
    </tbody>
  </table>
  </div>
</div>

<?php if ($escolhido !== null): ?>
<?php $materias = Interno::materias($itens[$escolhido]); ?>
<section class="quadro faixa-prazos" id="materias">
  <h2><?= e($rotulo($itens[$escolhido])) ?>
    <span class="apoio">(<?= $itens[$escolhido]['n'] > count($materias) ? 'as ' . count($materias) . ' mais recentes de ' . number_format($itens[$escolhido]['n'], 0, ',', '.') : count($materias) ?>)</span></h2>
<?php if (!$materias): ?>
  <p class="vazio__dica">O Diário não publicou nada que a busca deste item encontre, no período que o acervo cobre.</p>
<?php else: ?>
  <ul class="lista-materias">
<?php foreach ($materias as $m): ?>
    <li>
      <a href="/ato/<?= e($m['id']) ?>"><?= e($m['tipo'] && $m['numero'] ? $m['tipo'] . ' nº ' . $m['numero'] : (rotulo_legivel($m['rotulo']) ?: 'Matéria')) ?></a>
      <span class="apoio"><?= data_br($m['data_pub']) ?> · <?= e(orgao_curto($m['orgao'])) ?></span>
      <p class="ementa"><?= e($m['ementa'] ?: resumo($m['inicio'], 260)) ?></p>
    </li>
<?php endforeach; ?>
  </ul>
<?php endif; ?>
</section>
<?php endif; ?>

<div class="ressalva prosa">
  <p>
    <strong>"Nenhuma" quer dizer que o Diário não mostra, e não que nada foi
    feito.</strong> Muita coisa acontece sem virar publicação oficial, e o acervo
    ainda não cobre todos os anos. O número serve para perguntar, não para
    concluir.
  </p>
</div>
<?php endif; ?>

<?php
$conteudo = ob_get_clean();
$titulo = $titulo_pagina;
$larga = true;
require dirname(__DIR__) . '/layout.php';
