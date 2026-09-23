<?php
/** @var array $ato */
declare(strict_types=1);
ob_start();

/*
 * O título da ficha, na ordem do que informa mais.
 *
 * 84% das matérias não têm ato numerado, e para elas o rótulo que o próprio
 * Diário usa — "EXTRATO DE TERMO ADITIVO", "DESPACHO DO ORDENADOR DE DESPESAS"
 * — diz muito mais que "Matéria de 22/09/2026", que era o que aparecia antes e
 * não informava nada.
 */
$titulo_ato = ($ato['tipo'] && $ato['numero'])
    ? $ato['tipo'] . ' nº ' . $ato['numero']
    : ($ato['cabecalho'] ?: ($ato['rotulo'] ?: 'Matéria de ' . data_br($ato['data_pub'])));

/** Quem revogou de vez este ato — só revogação total derruba a norma. */
$revogado = array_filter(
    $ato['recebidas'],
    static fn ($r) => $r['tipo_relacao'] === 'Revoga' && !$r['parcial']
);
$parciais = array_filter(
    $ato['recebidas'],
    static fn ($r) => (bool) $r['parcial']
);
?>

<p class="voltar"><a href="javascript:history.back()">← Voltar</a></p>

<h1><?= e($titulo_ato) ?></h1>

<?php if ($revogado): ?>
<div class="aviso aviso--revogado">
  <strong>Esta norma foi revogada.</strong>
<?php foreach ($revogado as $r): ?>
  <p>
    Pelo <a href="/ato/<?= e($r['id']) ?>"><?= e($r['tipo'] ?: 'ato') ?>
    <?= $r['numero'] ? 'nº ' . e($r['numero']) : '' ?></a>,
    de <?= data_br($r['data_pub']) ?>.
<?php if ($r['origem'] === 'automatico'): ?>
    <span class="selo selo--fraco">detectado automaticamente</span>
<?php endif; ?>
  </p>
<?php endforeach; ?>
</div>
<?php elseif ($parciais): ?>
<div class="aviso">
  <strong>Esta norma continua em vigor, mas teve dispositivos alterados.</strong>
<?php foreach ($parciais as $r): ?>
  <p>
    <?= e($r['tipo_relacao']) ?> <?= e($r['dispositivo'] ?: 'dispositivo') ?>,
    pelo <a href="/ato/<?= e($r['id']) ?>"><?= e($r['tipo'] ?: 'ato') ?>
    <?= $r['numero'] ? 'nº ' . e($r['numero']) : '' ?></a>
    de <?= data_br($r['data_pub']) ?>.
  </p>
<?php endforeach; ?>
</div>
<?php endif; ?>

<dl class="ficha">
  <dt>Publicado em</dt>
  <dd><?= data_br($ato['data_pub']) ?><?= $ato['pagina'] ? ', página ' . e($ato['pagina']) : '' ?></dd>

<?php if ($ato['data_ato'] && $ato['data_ato'] !== $ato['data_pub']): ?>
  <dt>Data do ato</dt>
  <dd><?= data_br($ato['data_ato']) ?></dd>
<?php endif; ?>

<?php if ($ato['orgao']): ?>
  <dt>Órgão</dt>
  <dd><?= e($ato['orgao']) ?></dd>
<?php endif; ?>

<?php if ($ato['unidade']): ?>
  <dt>Publicado por</dt>
  <dd><?= e($ato['unidade']) ?></dd>
<?php endif; ?>

<?php if (!empty($ato['processo'])): ?>
  <dt>Processo</dt>
  <dd>
    <a href="<?= e(url_com(['q' => $ato['processo']], '/busca')) ?>"><?= e($ato['processo']) ?></a>
    <span class="apoio">— ver os outros atos do mesmo processo</span>
  </dd>
<?php endif; ?>

  <dt>Vigência</dt>
  <dd>
    <span class="selo <?= ['Ativo'=>'selo--vigente','Alterado'=>'selo--alterado','Revogado'=>'selo--revogado'][$ato['status']] ?? '' ?>">
      <?= $ato['status'] === 'Ativo' ? 'Vigente' : e($ato['status']) ?>
    </span>
<?php if ($ato['status'] === 'Ativo'): ?>
    <span class="apoio">— nenhum ato deste acervo o revogou</span>
<?php endif; ?>
  </dd>

  <dt>Identificador na Imprensa Oficial</dt>
  <dd><?= e($ato['id_ioerj'] ?: '—') ?></dd>
</dl>

<?php if ($ato['ementa']): ?>
<h2>Ementa</h2>
<p class="prosa"><?= e($ato['ementa']) ?></p>
<?php if ($ato['ementa_inferida']): ?>
<p class="apoio">
  <span class="selo">deduzida</span>
  Esta ementa foi deduzida do bloco em caixa alta que segue o cabeçalho. O
  Diário não publica a ementa num campo próprio, então o que está acima é
  leitura automática, não transcrição de um campo.
</p>
<?php endif; ?>
<?php endif; ?>

<?php if ($ato['naturezas'] || $ato['ramos'] || $ato['e_cti']): ?>
<h2>Classificação</h2>
<p class="selos">
<?php foreach ($ato['naturezas'] as $chave => $origem): ?>
  <a class="selo" href="<?= e(url_com(['natureza' => $chave], '/busca')) ?>">
    <?= e(Acervo::NATUREZAS[$chave] ?? $chave) ?>
  </a>
<?php endforeach; ?>
<?php foreach ($ato['ramos'] as $chave => $origem): ?>
  <a class="selo selo--cti" href="<?= e(url_com(['ramo' => $chave], '/busca')) ?>">
    <?= e(Acervo::RAMOS[$chave] ?? $chave) ?>
  </a>
<?php endforeach; ?>
<?php if ($ato['entidade_sistema']): ?>
  <a class="selo selo--cti" href="<?= e(url_com(['entidade' => $ato['entidade_sistema']], '/busca')) ?>">
    <?= e(Acervo::ENTIDADES[$ato['entidade_sistema']] ?? $ato['entidade_sistema']) ?>
  </a>
<?php endif; ?>
</p>

<p class="apoio">
  Classificação automática, feita por vocabulário — ninguém conferiu.
<?php if ($ato['porque_cti']): ?>
  Entrou no recorte de CT&amp;I porque <?= e($ato['porque_cti']) ?><?php
  if ($ato['confianca']): ?>, com confiança <?= e($ato['confianca']) ?><?php
  endif; ?>.
<?php endif; ?>
<?php if ($ato['confianca'] === 'baixa'): ?>
  <strong>Confiança baixa quer dizer que entrou só por termo genérico</strong>,
  como "tecnologia" ou "inovação" — pode não ser do tema.
<?php endif; ?>
</p>
<?php endif; ?>

<?php if ($ato['relacoes']): ?>
<h2>O que este ato faz com outras normas</h2>
<ul class="relacoes">
<?php foreach ($ato['relacoes'] as $r): ?>
  <li>
    <strong><?= e($r['tipo_relacao']) ?></strong>
<?php if ($r['parcial']): ?>
    <?= e($r['dispositivo'] ?: 'um dispositivo') ?> d<?= 'a' ?>
<?php endif; ?>
<?php if ($r['ato_destino_id']): ?>
    <a href="/ato/<?= e($r['ato_destino_id']) ?>"><?= e($r['ato_destino_texto']) ?></a>
<?php else: ?>
    <?= e($r['ato_destino_texto']) ?>
<?php if ($r['externo']): ?>
    <span class="apoio">(norma de outro poder, fora deste acervo)</span>
<?php else: ?>
    <span class="apoio">(ainda não localizada no acervo)</span>
<?php endif; ?>
<?php endif; ?>
<?php if ($r['parcial']): ?>
    <span class="selo" title="Atinge só este dispositivo, e não a norma inteira">parcial</span>
<?php endif; ?>
  </li>
<?php endforeach; ?>
</ul>
<p class="apoio">
  Estas relações foram detectadas automaticamente, e só entram quando o próprio
  ato declara o que faz. Menção de passagem a outra norma não vira relação:
  seria fácil, e faria o portal dizer que normas vivas foram revogadas.
</p>
<?php endif; ?>

<h2>Texto publicado</h2>
<div class="texto">
<?php foreach (paragrafos($ato['texto'] ?? '') as $p): ?>
  <p><?= e($p) ?></p>
<?php endforeach; ?>
</div>

<h2>Na fonte</h2>
<p class="prosa">
<?php if (!empty($ato['url_pdf'])): ?>
  <a href="<?= e($ato['url_pdf']) ?>" rel="noopener">Abrir o Diário de
  <?= data_br($ato['edicao_data'] ?? $ato['data_pub']) ?> no site do IOERJ</a>
<?php if (!empty($ato['paginas'])): ?>
  (<?= (int) $ato['paginas'] ?> páginas)
<?php endif; ?>
<?php else: ?>
  O endereço do PDF desta edição ainda não foi registrado.
<?php endif; ?>
</p>
<p class="ressalva prosa">
  O texto acima foi extraído automaticamente do PDF e pode ter falhas de
  leitura. <strong>O arquivo de origem não tem valor legal</strong> — quem
  precisa da publicação oficial deve consultar o IOERJ. CPF, documento de
  identidade e endereço residencial de particular foram removidos antes da
  publicação aqui.
</p>

<?php
$conteudo = ob_get_clean();
$titulo = $titulo_ato;
$descricao = $ato['ementa'] ? mb_strimwidth($ato['ementa'], 0, 150, '…') : null;
require __DIR__ . '/layout.php';
