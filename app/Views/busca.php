<?php
/**
 * A lista de atos, no desenho do Portal de Normas e Atos da UFF.
 *
 * O modelo é o `src/components/ActTable.tsx` daquele portal, e a ordem da tela
 * é a dele: um quadro com a busca e os três filtros de uso comum (espécie, ano,
 * status) mais o botão "Mais filtros"; as etiquetas do que está filtrado; a
 * contagem com a ordenação ao lado; e um quadro com a tabela e a paginação
 * numerada. No celular a tabela vira cartões, como lá.
 *
 * O que muda é o que tinha de mudar. As cores e a fonte são as do Mapa de CT&I.
 * A UFF é um aplicativo React que filtra enquanto se digita; aqui é formulário
 * comum, e um script de doze linhas faz o select aplicar ao ser escolhido. Sem
 * script, o botão Buscar faz o mesmo — a página funciona igual.
 *
 * @var array $filtros
 * @var array $resultado
 * @var int $pagina
 */
declare(strict_types=1);
ob_start();

$total = $resultado['total'];
$paginas = (int) ceil($total / Acervo::POR_PAGINA);
$orgaos = Acervo::orgaos();

// Cada etiqueta leva o nome do campo junto do valor ("Órgão: Saúde"), porque o
// valor solto não diz de onde veio. E cada uma é o próprio botão de remover.
$etiquetas = [];
$poe = static function (string $chave, string $rotulo) use (&$etiquetas, $filtros): void {
    if (!empty($filtros[$chave])) {
        $etiquetas[] = [$chave, $rotulo];
    }
};
$poe('q', 'Busca: ' . $filtros['q']);
$poe('tipo', 'Espécie: ' . $filtros['tipo']);
$poe('ano', 'Ano: ' . $filtros['ano']);
$poe('status', 'Status: ' . ($filtros['status'] === 'Ativo' ? 'Vigente' : $filtros['status']));
$poe('orgao', 'Órgão: ' . orgao_curto($orgaos[$filtros['orgao']] ?? $filtros['orgao']));
$poe('natureza', 'Categoria: ' . (Acervo::NATUREZAS[$filtros['natureza']] ?? ''));
$poe('entidade', 'Sistema SECTI: ' . (Acervo::ENTIDADES[$filtros['entidade']] ?? ''));
$poe('ramo', 'Subsecretaria: ' . (Acervo::RAMOS[$filtros['ramo']] ?? ''));
$poe('cti', 'Só ciência, tecnologia e inovação');
$poe('de', 'De ' . data_br($filtros['de']));
$poe('ate', 'Até ' . data_br($filtros['ate']));

$avancados = count(array_filter([
    $filtros['orgao'], $filtros['natureza'], $filtros['entidade'], $filtros['ramo'], $filtros['cti'],
]));

$classe_status = ['Ativo' => 'selo--vigente', 'Alterado' => 'selo--alterado', 'Revogado' => 'selo--revogado'];
$classe_relacao = ['Revoga' => 'selo--revogado', 'Altera' => 'selo--alterado'];

$nome_do = static function (array $a): string {
    if ($a['tipo'] && $a['numero']) {
        return $a['tipo'] . ' nº ' . $a['numero'];
    }
    if ($a['rotulo']) {
        return rotulo_legivel($a['rotulo']);
    }
    return 'Matéria de ' . data_br($a['data_pub']);
};
// A ementa, ou — em 83% das matérias, que não têm — o começo do texto. Duas
// linhas na tela; o resto no `title`, como faz a UFF.
$ementa_do = static fn (array $a): string => $a['ementa']
    ? (string) $a['ementa']
    : resumo($a['inicio'] ?? '', 400);

$ordem = $filtros['ordem'] ?: 'data';
$sentido = $filtros['dir'] ?: 'desc';

$link_pagina = static function (int $n): string {
    $base = url_com([]);
    return $base . (str_contains($base, '?') ? '&' : '?') . 'pagina=' . $n;
};

$icone_documento = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" '
    . 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
    . '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
    . '<path d="M9 13h6M9 17h6"/></svg>';
?>

<header class="cabeca">
  <h1>Atos e normas</h1>
  <p class="apoio">
    Encontre decretos, resoluções, portarias, editais e os demais atos do Poder
    Executivo do Estado do Rio de Janeiro.
  </p>
</header>

<form id="filtros" class="quadro quadro--filtros" action="/busca" method="get" role="search">
  <div class="busca">
    <label for="q" class="oculto-visualmente">Buscar atos</label>
    <svg class="busca__lupa" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
         stroke-width="2" stroke-linecap="round" aria-hidden="true" focusable="false">
      <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
    </svg>
    <input type="search" id="q" name="q" autocomplete="off"
           value="<?= e($filtros['q']) ?>"
           placeholder="Buscar por número, ementa, processo ou órgão"
           aria-describedby="q-ajuda">
    <button type="submit" class="busca__botao">Buscar</button>
  </div>
  <p id="q-ajuda" class="ajuda">
    Aceita número do ato, palavras da ementa, número de processo e nome de órgão.
  </p>

  <div class="grade-filtros">
    <p class="campo">
      <label for="f-tipo">Espécie</label>
      <select id="f-tipo" name="tipo" data-aplica>
        <option value="">Todas</option>
<?php foreach (Acervo::tipos() as $t): ?>
        <option value="<?= e($t) ?>"<?= $filtros['tipo'] === $t ? ' selected' : '' ?>><?= e($t) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <p class="campo">
      <label for="f-ano">Ano</label>
      <select id="f-ano" name="ano" data-aplica>
        <option value="">Todos</option>
<?php foreach (Acervo::anos() as $a): ?>
        <option value="<?= $a['ano'] ?>"<?= $filtros['ano'] === (string) $a['ano'] ? ' selected' : '' ?>><?= e(Acervo::rotuloDoAno($a)) ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <p class="campo">
      <label for="f-status">Status</label>
      <select id="f-status" name="status" data-aplica>
        <option value="">Todos</option>
<?php foreach (['Ativo' => 'Vigentes', 'Revogado' => 'Revogados', 'Alterado' => 'Alterados'] as $k => $nome): ?>
        <option value="<?= $k ?>"<?= $filtros['status'] === $k ? ' selected' : '' ?>><?= $nome ?></option>
<?php endforeach; ?>
      </select>
    </p>

    <details class="mais-filtros">
      <summary class="mais-filtros__botao">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" aria-hidden="true" focusable="false">
          <path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/>
          <circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>
        </svg>
        Mais filtros
<?php if ($avancados > 0): ?>
        <span class="contador"><?= $avancados ?><span class="oculto-visualmente"> em uso</span></span>
<?php endif; ?>
      </summary>

      <div class="mais-filtros__painel">
        <p class="campo">
          <label for="f-orgao">Órgão</label>
          <select id="f-orgao" name="orgao" data-aplica>
            <option value="">Todos</option>
<?php foreach ($orgaos as $slug => $nome): ?>
            <option value="<?= e($slug) ?>"<?= $filtros['orgao'] === $slug ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
          </select>
        </p>

        <p class="campo">
          <label for="f-natureza">Categoria</label>
          <select id="f-natureza" name="natureza" data-aplica>
            <option value="">Todas</option>
<?php foreach (Acervo::NATUREZAS as $k => $nome): ?>
            <option value="<?= e($k) ?>"<?= $filtros['natureza'] === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
          </select>
        </p>

        <p class="campo">
          <label for="f-entidade">Sistema SECTI</label>
          <select id="f-entidade" name="entidade" data-aplica>
            <option value="">Todas as pastas</option>
<?php foreach (Acervo::ENTIDADES as $k => $nome): ?>
            <option value="<?= e($k) ?>"<?= $filtros['entidade'] === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
          </select>
        </p>

        <p class="campo">
          <label for="f-ramo">Subsecretaria</label>
          <select id="f-ramo" name="ramo" data-aplica>
            <option value="">Todas</option>
<?php foreach (Acervo::RAMOS as $k => $nome): ?>
            <option value="<?= e($k) ?>"<?= $filtros['ramo'] === $k ? ' selected' : '' ?>><?= e($nome) ?></option>
<?php endforeach; ?>
          </select>
        </p>

        <fieldset class="recortes">
          <legend>Recortes</legend>
          <label>
            <input type="checkbox" name="cti" value="1" data-aplica<?= $filtros['cti'] ? ' checked' : '' ?>>
            Só ciência, tecnologia e inovação
          </label>
        </fieldset>

        <button type="submit" class="botao-leve">Aplicar</button>
      </div>
    </details>
  </div>
<?php foreach (['de', 'ate'] as $oculto): ?>
<?php if (!empty($filtros[$oculto])): ?>
  <input type="hidden" name="<?= $oculto ?>" value="<?= e($filtros[$oculto]) ?>">
<?php endif; ?>
<?php endforeach; ?>
  <input type="hidden" name="dir" value="<?= e($sentido) ?>">
</form>

<?php if ($etiquetas): ?>
<div class="etiquetas">
<?php foreach ($etiquetas as [$chave, $rotulo]): ?>
  <a class="etiqueta" href="<?= e(url_com([$chave => null])) ?>">
    <?= e($rotulo) ?>
    <span aria-hidden="true">×</span><span class="oculto-visualmente"> — remover este filtro</span>
  </a>
<?php endforeach; ?>
  <a class="etiquetas__limpar" href="/busca">Limpar filtros</a>
</div>
<?php endif; ?>

<div class="contagem">
  <p class="contagem__total" role="status">
    <?= number_format($total, 0, ',', '.') ?> <?= $total === 1 ? 'ato encontrado' : 'atos encontrados' ?>
  </p>
<?php if ($total > 1): ?>
  <p class="ordenar">
    <label for="ordem">Ordenar por</label>
    <select id="ordem" name="ordem" form="filtros" data-aplica>
<?php foreach (Acervo::ORDENS as $k => [$rotulo]): ?>
      <option value="<?= $k ?>"<?= $ordem === $k ? ' selected' : '' ?>><?= $rotulo ?></option>
<?php endforeach; ?>
    </select>
    <a class="ordenar__sentido" href="<?= e(url_com(['dir' => $sentido === 'desc' ? 'asc' : 'desc'])) ?>"
       aria-label="<?= $sentido === 'desc' ? 'Ordenar do menor para o maior' : 'Ordenar do maior para o menor' ?>"
       title="<?= $sentido === 'desc' ? 'Maior primeiro' : 'Menor primeiro' ?>">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="m7 15 5 5 5-5M7 9l5-5 5 5"/>
      </svg>
    </a>
    <noscript><button type="submit" form="filtros" class="botao-leve">Ordenar</button></noscript>
  </p>
<?php endif; ?>
</div>

<div class="quadro quadro--resultados">
<?php if ($total === 0): ?>
  <div class="vazio">
    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" aria-hidden="true" focusable="false">
      <circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h0"/>
    </svg>
    <p class="vazio__titulo">Nenhum ato corresponde a esta consulta.</p>
    <p class="vazio__dica">
<?php if ($etiquetas): ?>
      Tente remover um dos filtros ou usar menos palavras na busca. A busca
      encontra a palavra inteira ou o começo dela: <em>tecnolog</em> encontra
      <em>tecnologia</em>, mas <em>arte</em> não encontra <em>Duarte</em>.
<?php else: ?>
      Tente usar menos palavras, ou buscar pelo número do ato.
<?php endif; ?>
    </p>
    <p class="vazio__dica">
      O acervo ainda não é o Diário inteiro. Se o ato é de uma data que não foi
      coletada, ele não está aqui, e a falta é nossa. A página
      <a href="/sobre">sobre o portal</a> diz o que já entrou.
    </p>
<?php if ($etiquetas): ?>
    <a class="botao-leve" href="/busca">Limpar filtros</a>
<?php endif; ?>
  </div>
<?php else: ?>

  <ol class="cartoes">
<?php foreach ($resultado['itens'] as $a): ?>
    <li class="cartao-ato">
      <div class="cartao-ato__topo">
        <a class="cartao-ato__nome" href="/ato/<?= e($a['id']) ?>"><?= e($nome_do($a)) ?></a>
        <span class="selo <?= $classe_status[$a['status']] ?? '' ?>"><?= $a['status'] === 'Ativo' ? 'Vigente' : e($a['status']) ?></span>
      </div>
      <p class="cartao-ato__meta">
        <span><?= data_br($a['data_pub']) ?></span>
        <span><?= e(orgao_curto($a['orgao'] ?: $a['unidade'])) ?></span>
      </p>
      <p class="cartao-ato__ementa"><?= e($ementa_do($a)) ?></p>
<?php if (!empty($a['processo'])): ?>
      <p class="processo">Processo: <?= e($a['processo']) ?></p>
<?php endif; ?>
<?php if ($a['e_cti']): ?>
      <span class="selo selo--cti">CT&amp;I</span>
<?php endif; ?>
    </li>
<?php endforeach; ?>
  </ol>

  <div class="tabela-rolante">
  <table class="tabela-atos">
    <caption class="oculto-visualmente">
      Atos encontrados, com espécie e número, ementa, órgão, data, relações e status.
    </caption>
    <thead>
      <tr>
        <th scope="col" class="col-especie">Espécie e número</th>
        <th scope="col">Ementa</th>
        <th scope="col" class="col-orgao">Órgão</th>
        <th scope="col" class="col-data">Data</th>
        <th scope="col" class="col-relacoes">Relações</th>
        <th scope="col" class="col-status">Status</th>
        <th scope="col" class="col-acao">Ação</th>
      </tr>
    </thead>
    <tbody>
<?php foreach ($resultado['itens'] as $a): ?>
<?php $ementa = $ementa_do($a); ?>
      <tr>
        <td>
          <div class="especie">
            <span class="especie__icone"><?= $icone_documento ?></span>
            <span>
              <span class="especie__nome"><?= e($nome_do($a)) ?></span>
<?php if ($a['e_cti']): ?>
              <span class="selo selo--cti">CT&amp;I</span>
<?php endif; ?>
            </span>
          </div>
        </td>
        <td>
<?php if ($ementa !== ''): ?>
          <p class="ementa" title="<?= e($ementa) ?>"><?= e($ementa) ?></p>
<?php else: ?>
          <p class="ementa">Sem ementa no Diário.</p>
<?php endif; ?>
<?php if (!empty($a['processo'])): ?>
          <a class="processo" href="<?= e(url_com(['q' => $a['processo']], '/busca')) ?>"><?= e($a['processo']) ?></a>
<?php endif; ?>
        </td>
        <td class="col-orgao" title="<?= e(trim(($a['orgao'] ?? '') . ' ' . ($a['unidade'] ?? ''))) ?>">
          <span class="orgao"><?= e(orgao_curto($a['orgao'] ?: $a['unidade'])) ?></span>
        </td>
        <td class="col-data"><?= data_br($a['data_pub']) ?></td>
        <td class="col-relacoes">
<?php if (!empty($a['relacoes'])): ?>
          <span class="relacoes">
<?php foreach (explode(',', $a['relacoes']) as $r): ?>
            <span class="selo selo--relacao <?= $classe_relacao[$r] ?? '' ?>"><?= e($r) ?></span>
<?php endforeach; ?>
          </span>
<?php else: ?>
          <span class="nada">—</span>
<?php endif; ?>
        </td>
        <td class="col-status">
          <span class="selo <?= $classe_status[$a['status']] ?? '' ?>"><?= $a['status'] === 'Ativo' ? 'Vigente' : e($a['status']) ?></span>
        </td>
        <td class="col-acao">
          <a href="/ato/<?= e($a['id']) ?>">Ver ato<span class="oculto-visualmente">: <?= e($nome_do($a)) ?></span> <span aria-hidden="true">›</span></a>
        </td>
      </tr>
<?php endforeach; ?>
    </tbody>
  </table>
  </div>

<?php if ($paginas > 1): ?>
  <nav class="paginacao" aria-label="Paginação dos resultados">
<?php if ($pagina > 1): ?>
    <a class="paginacao__passo" href="<?= e($link_pagina($pagina - 1)) ?>">‹ Anterior</a>
<?php else: ?>
    <span class="paginacao__passo" aria-disabled="true">‹ Anterior</span>
<?php endif; ?>
<?php foreach (janela_paginas($pagina, $paginas) as $n): ?>
<?php if ($n === null): ?>
    <span class="paginacao__buraco" aria-hidden="true">…</span>
<?php elseif ($n === $pagina): ?>
    <a class="paginacao__numero" href="<?= e($link_pagina($n)) ?>" aria-current="page" aria-label="Página <?= $n ?>"><?= number_format($n, 0, ',', '.') ?></a>
<?php else: ?>
    <a class="paginacao__numero" href="<?= e($link_pagina($n)) ?>" aria-label="Página <?= $n ?>"><?= number_format($n, 0, ',', '.') ?></a>
<?php endif; ?>
<?php endforeach; ?>
<?php if ($pagina < $paginas): ?>
    <a class="paginacao__passo" href="<?= e($link_pagina($pagina + 1)) ?>">Próxima ›</a>
<?php else: ?>
    <span class="paginacao__passo" aria-disabled="true">Próxima ›</span>
<?php endif; ?>
  </nav>
<?php endif; ?>
<?php endif; ?>
</div>

<script src="<?= e(ativo('/assets/js/busca.js')) ?>" defer></script>

<?php
$conteudo = ob_get_clean();
$titulo = $filtros['q'] ? 'Busca: ' . $filtros['q'] : 'Atos e normas';
$larga = true;
require __DIR__ . '/layout.php';
