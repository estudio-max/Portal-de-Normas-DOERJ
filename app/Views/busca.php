<?php
/**
 * A lista de resultados, em tabela.
 *
 * A diagramação é a do Portal de Normas e Atos da UFF: espécie e número, ementa
 * com o processo abaixo, órgão, data, relações, status e a ação. Quem cuida dos
 * dois acervos reconhece a tela sem reaprender nada — e a tabela lê melhor que
 * cartão quando se está comparando vinte atos para achar um.
 *
 * @var array $filtros
 * @var array $resultado
 * @var int $pagina
 */
declare(strict_types=1);
ob_start();

$total = $resultado['total'];
$paginas = (int) ceil($total / Acervo::POR_PAGINA);

/** Os filtros em vigor, para a pessoa poder tirar um de cada vez. */
$ativos = [];
if (!empty($filtros['q']))        $ativos[] = ['q', 'Busca: “' . $filtros['q'] . '”'];
if (!empty($filtros['natureza'])) $ativos[] = ['natureza', Acervo::NATUREZAS[$filtros['natureza']] ?? $filtros['natureza']];
if (!empty($filtros['ramo']))     $ativos[] = ['ramo', Acervo::RAMOS[$filtros['ramo']] ?? $filtros['ramo']];
if (!empty($filtros['entidade'])) $ativos[] = ['entidade', Acervo::ENTIDADES[$filtros['entidade']] ?? $filtros['entidade']];
if (!empty($filtros['tipo']))     $ativos[] = ['tipo', $filtros['tipo']];
if (!empty($filtros['cti']))      $ativos[] = ['cti', 'Só ciência, tecnologia e inovação'];
if (!empty($filtros['status']))   $ativos[] = ['status', $filtros['status']];
if (!empty($filtros['de']))       $ativos[] = ['de', 'De ' . data_br($filtros['de'])];
if (!empty($filtros['ate']))      $ativos[] = ['ate', 'Até ' . data_br($filtros['ate'])];

$classe_status = [
    'Ativo'    => 'selo--vigente',
    'Alterado' => 'selo--alterado',
    'Revogado' => 'selo--revogado',
];
?>

<h1>Atos e normas</h1>
<p class="prosa apoio">
  Encontre decretos, resoluções, portarias, editais e os demais atos do Poder
  Executivo do Estado do Rio de Janeiro.
</p>

<form class="filtrar" action="/busca" method="get" role="search">
  <div class="filtrar__busca">
    <label for="q">Buscar atos</label>
    <input type="search" id="q" name="q" autocomplete="off"
           value="<?= e($filtros['q'] ?? '') ?>"
           aria-describedby="q-ajuda"
           placeholder="número do ato, palavra da ementa, processo, órgão">
    <p class="apoio" id="q-ajuda">
      Aceita número do ato, palavras da ementa, número de processo e nome de órgão.
    </p>
  </div>

  <div class="filtrar__campos">
    <p class="campo">
      <label for="f-tipo">Espécie</label>
      <select id="f-tipo" name="tipo">
        <option value="">Todas</option>
<?php foreach (Acervo::tipos() as $t): ?>
        <option value="<?= e($t) ?>"<?= ($filtros['tipo'] ?? '') === $t ? ' selected' : '' ?>><?= e($t) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <p class="campo">
      <label for="f-natureza">Categoria</label>
      <select id="f-natureza" name="natureza">
        <option value="">Todas</option>
<?php foreach (Acervo::NATUREZAS as $k => $nome): ?>
        <option value="<?= e($k) ?>"<?= ($filtros['natureza'] ?? '') === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <p class="campo">
      <label for="f-status">Vigência</label>
      <select id="f-status" name="status">
        <option value="">Todas</option>
<?php foreach (['Ativo' => 'Vigentes', 'Alterado' => 'Alterados', 'Revogado' => 'Revogados'] as $k => $nome): ?>
        <option value="<?= e($k) ?>"<?= ($filtros['status'] ?? '') === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <p class="campo">
      <label for="f-entidade">Sistema SECTI</label>
      <select id="f-entidade" name="entidade">
        <option value="">Todas as pastas</option>
<?php foreach (Acervo::ENTIDADES as $k => $nome): ?>
        <option value="<?= e($k) ?>"<?= ($filtros['entidade'] ?? '') === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <button type="submit" class="botao">Filtrar</button>
  </div>
<?php foreach (['ramo', 'cti', 'de', 'ate'] as $oculto): ?>
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
  Nenhum ato com esses filtros.
<?php else: ?>
  <strong><?= number_format($total, 0, ',', '.') ?></strong>
  <?= $total === 1 ? 'ato encontrado' : 'atos encontrados' ?>.
<?php if ($paginas > 1): ?>
  <span class="apoio">Página <?= $pagina ?> de <?= number_format($paginas, 0, ',', '.') ?>.</span>
<?php endif; ?>
<?php endif; ?>
</p>

<?php if ($total === 0): ?>
<div class="ressalva prosa">
  <p>
    Vale conferir se a busca não está estreita demais. O acervo tem oito edições
    entre 2010 e 2026, e não o Diário inteiro — se o ato que você procura é de
    uma data que ainda não foi coletada, ele não está aqui, e a falta é nossa.
  </p>
</div>
<?php else: ?>

<div class="tabela-rolante">
<table class="tabela-atos">
  <caption class="oculto-visualmente">
    Atos encontrados, com espécie e número, ementa, órgão, data, relações e
    situação de vigência.
  </caption>
  <thead>
    <tr>
      <th scope="col">Espécie e número</th>
      <th scope="col">Ementa</th>
      <th scope="col">Órgão</th>
      <th scope="col">Data</th>
      <th scope="col">Relações</th>
      <th scope="col">Vigência</th>
      <th scope="col"><span class="oculto-visualmente">Ação</span></th>
    </tr>
  </thead>
  <tbody>
<?php foreach ($resultado['itens'] as $a): ?>
    <tr>
      <td class="col-especie">
        <a href="/ato/<?= e($a['id']) ?>">
<?php if ($a['tipo'] && $a['numero']): ?>
          <?= e($a['tipo']) ?> nº <?= e($a['numero']) ?>
<?php elseif ($a['rotulo']): ?>
          <?= e($a['rotulo']) ?>
<?php else: ?>
          Matéria de <?= data_br($a['data_pub']) ?>
<?php endif; ?>
        </a>
<?php if ($a['e_cti']): ?>
        <span class="selo selo--cti">CT&amp;I</span>
<?php endif; ?>
      </td>

      <td class="col-ementa">
<?php if ($a['ementa']): ?>
        <?= e(mb_strimwidth($a['ementa'], 0, 190, '…')) ?>
<?php if ($a['ementa_inferida']): ?>
        <span class="selo" title="Deduzida do bloco em caixa alta, e não de um campo publicado como ementa">deduzida</span>
<?php endif; ?>
<?php elseif (!empty($a['inicio'])): ?>
        <span class="apoio" title="O Diário não publicou ementa para esta matéria. Estas são as primeiras linhas do texto.">
          <?= e(resumo($a['inicio'])) ?>
        </span>
<?php else: ?>
        <span class="apoio">(sem ementa no Diário)</span>
<?php endif; ?>
<?php if (!empty($a['processo'])): ?>
        <a class="processo" href="<?= e(url_com(['q' => $a['processo']], '/busca')) ?>"><?= e($a['processo']) ?></a>
<?php endif; ?>
      </td>

      <td class="col-orgao"><?= e(mb_strimwidth($a['unidade'] ?: ($a['orgao'] ?: '—'), 0, 42, '…')) ?></td>

      <td class="col-data"><?= data_br($a['data_pub']) ?></td>

      <td class="col-relacoes">
<?php if (!empty($a['relacoes'])): ?>
<?php foreach (explode(',', $a['relacoes']) as $r): ?>
        <span class="selo selo--relacao"><?= e(mb_strtoupper($r, 'UTF-8')) ?></span>
<?php endforeach; ?>
<?php else: ?>
        <span class="apoio">—</span>
<?php endif; ?>
      </td>

      <td class="col-status">
        <span class="selo <?= $classe_status[$a['status']] ?? '' ?>">
          <?= $a['status'] === 'Ativo' ? 'Vigente' : e($a['status']) ?>
        </span>
      </td>

      <td class="col-acao">
        <a href="/ato/<?= e($a['id']) ?>">Ver ato
          <span class="oculto-visualmente">
            <?= e(($a['tipo'] && $a['numero']) ? $a['tipo'] . ' ' . $a['numero'] : ($a['rotulo'] ?: 'de ' . data_br($a['data_pub']))) ?>
          </span>
          <span aria-hidden="true">›</span>
        </a>
      </td>
    </tr>
<?php endforeach; ?>
  </tbody>
</table>
</div>
<?php endif; ?>

<?php if ($paginas > 1): ?>
<?php $base = url_com(['pagina' => null]); $sep = str_contains($base, '?') ? '&' : '?'; ?>
<nav class="paginacao" aria-label="Páginas de resultado">
<?php if ($pagina > 1): ?>
  <a href="<?= e($base . $sep . 'pagina=' . ($pagina - 1)) ?>">← Anterior</a>
<?php endif; ?>
  <span class="apoio">Página <?= $pagina ?> de <?= number_format($paginas, 0, ',', '.') ?></span>
<?php if ($pagina < $paginas): ?>
  <a href="<?= e($base . $sep . 'pagina=' . ($pagina + 1)) ?>">Próxima →</a>
<?php endif; ?>
</nav>
<?php endif; ?>

<?php
$conteudo = ob_get_clean();
$titulo = $filtros['q'] ? 'Busca: ' . $filtros['q'] : 'Atos e normas';
require __DIR__ . '/layout.php';
