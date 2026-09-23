<?php
/**
 * @var array $filtros
 * @var array $resultado
 * @var int $pagina
 */
declare(strict_types=1);
ob_start();

$total = $resultado['total'];
$paginas = (int) ceil($total / Acervo::POR_PAGINA);
$naturezas = Acervo::porNatureza();

/** Os filtros em vigor, para a pessoa poder tirar um de cada vez. */
$ativos = [];
if (!empty($filtros['q']))        $ativos[] = ['q', 'Busca: “' . $filtros['q'] . '”'];
if (!empty($filtros['natureza'])) $ativos[] = ['natureza', Acervo::NATUREZAS[$filtros['natureza']] ?? $filtros['natureza']];
if (!empty($filtros['ramo']))     $ativos[] = ['ramo', Acervo::RAMOS[$filtros['ramo']] ?? $filtros['ramo']];
if (!empty($filtros['entidade'])) $ativos[] = ['entidade', Acervo::ENTIDADES[$filtros['entidade']] ?? $filtros['entidade']];
if (!empty($filtros['tipo']))     $ativos[] = ['tipo', $filtros['tipo']];
if (!empty($filtros['cti']))      $ativos[] = ['cti', 'Só ciência e inovação'];
if (!empty($filtros['de']))       $ativos[] = ['de', 'De ' . data_br($filtros['de'])];
if (!empty($filtros['ate']))      $ativos[] = ['ate', 'Até ' . data_br($filtros['ate'])];
?>

<h1 class="oculto-visualmente">Busca no acervo</h1>

<form class="busca-grande" action="/busca" method="get" role="search">
  <label for="q">Buscar no acervo</label>
  <div class="busca-grande__linha">
    <input type="search" id="q" name="q" autocomplete="off"
           value="<?= e($filtros['q'] ?? '') ?>"
           placeholder="número do ato, órgão, assunto, processo SEI">
    <button type="submit" class="botao">Buscar</button>
  </div>
<?php foreach (['natureza', 'ramo', 'entidade', 'tipo', 'cti', 'de', 'ate'] as $oculto): ?>
<?php if (!empty($filtros[$oculto])): ?>
  <input type="hidden" name="<?= $oculto ?>" value="<?= e((string) $filtros[$oculto]) ?>">
<?php endif; ?>
<?php endforeach; ?>
</form>

<?php if ($ativos): ?>
<nav class="filtros" aria-label="Filtros aplicados">
  <span class="apoio">Filtrando por:</span>
<?php foreach ($ativos as [$chave, $rotulo]): ?>
  <a class="marca" href="<?= e(url_com([$chave => null])) ?>">
    <?= e($rotulo) ?> <span aria-hidden="true">×</span>
    <span class="oculto-visualmente">— remover este filtro</span>
  </a>
<?php endforeach; ?>
  <a class="apoio" href="/busca">limpar tudo</a>
</nav>
<?php endif; ?>

<p class="numeros" role="status">
<?php if ($total === 0): ?>
  Nenhuma matéria com esses filtros.
<?php else: ?>
  <strong><?= number_format($total, 0, ',', '.') ?></strong>
  <?= $total === 1 ? 'matéria' : 'matérias' ?>.
<?php if ($paginas > 1): ?>
  Página <?= $pagina ?> de <?= $paginas ?>.
<?php endif; ?>
<?php endif; ?>
</p>

<?php if ($total === 0): ?>
<div class="ressalva prosa">
  <p>
    Vale conferir se a busca não está estreita demais. O acervo tem oito
    edições entre 2010 e 2026, e não o Diário inteiro — se o ato que você
    procura é de uma data que ainda não foi coletada, ele não está aqui.
  </p>
</div>
<?php endif; ?>

<ol class="resultados">
<?php foreach ($resultado['itens'] as $a): ?>
  <li class="resultado">
    <a class="resultado__titulo" href="/ato/<?= e($a['id']) ?>">
<?php if ($a['tipo'] && $a['numero']): ?>
      <?= e($a['tipo']) ?> nº <?= e($a['numero']) ?>
<?php elseif ($a['cabecalho']): ?>
      <?= e(mb_strimwidth($a['cabecalho'], 0, 90, '…')) ?>
<?php else: ?>
      Matéria de <?= data_br($a['data_pub']) ?>
<?php endif; ?>
    </a>

    <p class="resultado__origem apoio">
      <?= data_br($a['data_pub']) ?>
<?php if ($a['unidade'] || $a['orgao']): ?>
      · <?= e($a['unidade'] ?: $a['orgao']) ?>
<?php endif; ?>
<?php if ($a['pagina']): ?>
      · p. <?= e($a['pagina']) ?>
<?php endif; ?>
    </p>

<?php if ($a['ementa']): ?>
    <p class="resultado__ementa">
      <?= e(mb_strimwidth($a['ementa'], 0, 220, '…')) ?>
<?php if ($a['ementa_inferida']): ?>
      <span class="selo" title="Deduzida do bloco em caixa alta, e não de um campo publicado como ementa">ementa deduzida</span>
<?php endif; ?>
    </p>
<?php endif; ?>

<?php if ($a['e_cti']): ?>
    <p>
      <span class="selo selo--cti">ciência e inovação</span>
<?php if ($a['entidade_sistema']): ?>
      <span class="selo"><?= e(Acervo::ENTIDADES[$a['entidade_sistema']] ?? $a['entidade_sistema']) ?></span>
<?php endif; ?>
<?php if ($a['confianca'] === 'baixa'): ?>
      <span class="selo selo--fraco" title="Entrou por termo genérico, sem confirmação. Pode não ser do tema.">indício fraco</span>
<?php endif; ?>
    </p>
<?php endif; ?>
  </li>
<?php endforeach; ?>
</ol>

<?php if ($paginas > 1): ?>
<nav class="paginacao" aria-label="Páginas de resultado">
<?php if ($pagina > 1): ?>
  <a href="<?= e(url_com(['pagina' => $pagina - 1]) . (str_contains(url_com(['pagina' => null]), '?') ? '&' : '?') . 'pagina=' . ($pagina - 1)) ?>">← Anterior</a>
<?php endif; ?>
  <span class="apoio">Página <?= $pagina ?> de <?= $paginas ?></span>
<?php if ($pagina < $paginas): ?>
  <a href="<?= e(url_com(['pagina' => null]) . (str_contains(url_com(['pagina' => null]), '?') ? '&' : '?') . 'pagina=' . ($pagina + 1)) ?>">Próxima →</a>
<?php endif; ?>
</nav>
<?php endif; ?>

<?php
$conteudo = ob_get_clean();
$titulo = $filtros['q'] ? 'Busca: ' . $filtros['q'] : 'Busca';
require __DIR__ . '/layout.php';
