<?php
/**
 * Prazos e compromissos: o que vence, quando, e o contexto de cada um.
 *
 * Pedido do João em 2026-09-23: a gestão atual pode não saber o que foi
 * combinado antes dela e perder a data. A tela responde a três perguntas, nesta
 * ordem: quantos vencem logo (os números do topo), como os vencimentos se
 * distribuem no tempo (o gráfico), e o que é cada um (a tabela).
 *
 * O GRÁFICO É SVG FEITO AQUI, sem biblioteca e sem script. São colunas por mês,
 * seis meses para trás e dezoito para a frente, empilhadas pela faixa de
 * urgência. A cor segue a urgência e vem sempre com rótulo; o detalhe de cada
 * mês aparece ao passar o mouse, e a tabela logo abaixo é a versão que não
 * depende de enxergar cor.
 *
 * As quatro cores passaram pelo validador de paleta da skill de visualização:
 * vizinhas separadas por ΔE 19 para quem vê todas as cores e 13 para daltônicos,
 * todas acima de 3:1 contra o fundo. O cinza de "já venceu" lê como cinza de
 * propósito — é contexto, e não alerta.
 *
 * @var array $paineis
 * @var string $painel
 */
declare(strict_types=1);
ob_start();

$hoje = new DateTimeImmutable('today');
$primeiro = $hoje->modify('first day of this month')->modify('-6 months');
$ultimo = $hoje->modify('first day of this month')->modify('+18 months')->modify('last day of this month');
$recorte = ($_GET['recorte'] ?? '') === 'cti' ? 'cti' : 'sistema';

$itens = Interno::prazos($primeiro->format('Y-m-d'), $ultimo->format('Y-m-d'), $recorte);

$FAIXAS = [
    'alerta'  => 'Vence em até 90 dias',
    'ano'     => 'Vence em até 1 ano',
    'depois'  => 'Vence depois de 1 ano',
    'vencido' => 'Já venceu',
];
$por_faixa = array_fill_keys(array_keys($FAIXAS), []);
$por_mes = [];
foreach ($itens as $i) {
    $f = Interno::faixa($i['fim'], $hoje);
    $i['faixa'] = $f;
    $i['dias'] = (int) $hoje->diff(new DateTimeImmutable($i['fim']))->format('%r%a');
    $por_faixa[$f][] = $i;
    $por_mes[substr($i['fim'], 0, 7)][$f] = ($por_mes[substr($i['fim'], 0, 7)][$f] ?? 0) + 1;
}

// --------------------------------------------------------------- o gráfico
$MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
$MES_LONGO = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
              'setembro', 'outubro', 'novembro', 'dezembro'];
$meses = [];
for ($m = $primeiro; $m <= $ultimo; $m = $m->modify('+1 month')) {
    $meses[] = $m;
}
$L = 34; $R = 6; $T = 18; $B = 38; $W = 960; $H = 250;
$largura = $W - $L - $R;
$altura = $H - $T - $B;
$faixa_x = $largura / count($meses);
$barra = min(26, $faixa_x * 0.62);
$maior = max([1, ...array_map('array_sum', $por_mes ?: [[0]])]);
$teto = $maior <= 5 ? $maior : (int) (ceil($maior / 5) * 5);
$y = static fn (float $v): float => $T + $altura - $altura * $v / $teto;
$ORDEM = ['vencido', 'alerta', 'ano', 'depois'];

$svg = [];
foreach ([0, $teto / 2, $teto] as $g) {
    $gy = round($y($g), 1);
    $svg[] = "<line class=\"grade\" x1=\"$L\" x2=\"" . ($W - $R) . "\" y1=\"$gy\" y2=\"$gy\"/>";
    $svg[] = '<text class="eixo" x="' . ($L - 6) . '" y="' . ($gy + 4) . '" text-anchor="end">'
        . e(rtrim(rtrim(number_format($g, 1, ',', ''), '0'), ',')) . '</text>';
}
foreach ($meses as $k => $m) {
    $cx = $L + $faixa_x * ($k + 0.5);
    $chave = $m->format('Y-m');
    $contas = $por_mes[$chave] ?? [];
    $total = array_sum($contas);
    $partes = [];
    foreach ($ORDEM as $f) {
        if (!empty($contas[$f])) {
            $partes[] = $contas[$f] . ' ' . mb_strtolower($FAIXAS[$f]);
        }
    }
    $dica = $MES_LONGO[(int) $m->format('n') - 1] . ' de ' . $m->format('Y') . ': '
        . ($total === 0 ? 'nenhum vencimento' : $total . ($total === 1 ? ' vence' : ' vencem')
        . ' — ' . implode('; ', $partes));
    $svg[] = '<g class="mes"><title>' . e($dica) . '</title>';
    // A área de toque é a coluna inteira, e não só a barra: mês com um
    // vencimento só teria dois pixels para apontar.
    $svg[] = '<rect class="alvo" x="' . round($L + $faixa_x * $k, 1) . "\" y=\"$T\" width=\""
        . round($faixa_x, 1) . "\" height=\"$altura\"/>";
    $base = $T + $altura;
    $x0 = $cx - $barra / 2;
    $x1 = $cx + $barra / 2;
    $visiveis = array_values(array_filter($ORDEM, static fn ($f) => !empty($contas[$f])));
    foreach ($visiveis as $n => $f) {
        $h = $altura * $contas[$f] / $teto;
        // 2 px de fundo entre um segmento e o de baixo, para a borda se ver
        // sem depender da cor.
        $yb = $base - ($n > 0 ? 2 : 0);
        $yt = min($base - $h, $yb - 1);
        if ($n === count($visiveis) - 1) {
            // Ponta arredondada só no segmento de cima, o que encosta no ar; a
            // base fica reta, apoiada no eixo.
            $r = min(4, ($yb - $yt) / 2, $barra / 2);
            $svg[] = sprintf(
                '<path class="seg seg--%s" d="M%.1f %.1f V%.1f Q%.1f %.1f %.1f %.1f H%.1f Q%.1f %.1f %.1f %.1f V%.1f Z"/>',
                $f, $x0, $yb, $yt + $r, $x0, $yt, $x0 + $r, $yt, $x1 - $r, $x1, $yt, $x1, $yt + $r, $yb
            );
        } else {
            $svg[] = sprintf('<rect class="seg seg--%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>',
                $f, $x0, $yt, $barra, $yb - $yt);
        }
        $base -= $h;
    }
    $svg[] = '</g>';
    $svg[] = '<text class="eixo" x="' . round($cx, 1) . '" y="' . ($T + $altura + 15) . '" text-anchor="middle">'
        . $MES[(int) $m->format('n') - 1] . '</text>';
    if ($k === 0 || $m->format('n') === '1') {
        $svg[] = '<text class="eixo eixo--ano" x="' . round($cx, 1) . '" y="' . ($T + $altura + 30)
            . '" text-anchor="middle">' . $m->format('Y') . '</text>';
    }
}
// A linha de hoje, no ponto do mês em que hoje está.
$k_hoje = (int) (($hoje->format('Y') - $primeiro->format('Y')) * 12 + $hoje->format('n') - $primeiro->format('n'));
$hx = round($L + $faixa_x * ($k_hoje + ($hoje->format('j') - 1) / (int) $hoje->format('t')), 1);
$svg[] = "<line class=\"hoje\" x1=\"$hx\" x2=\"$hx\" y1=\"" . ($T - 6) . '" y2="' . ($T + $altura) . '"/>';
$svg[] = "<text class=\"hoje__rotulo\" x=\"$hx\" y=\"" . ($T - 8) . '" text-anchor="middle">hoje</text>';

$resumo_grafico = sprintf(
    '%d instrumentos vencem entre %s e %s: %d em até 90 dias, %d em até 1 ano, %d depois, e %d já venceram nos últimos seis meses.',
    count($itens), $MES[(int) $primeiro->format('n') - 1] . '/' . $primeiro->format('Y'),
    $MES[(int) $ultimo->format('n') - 1] . '/' . $ultimo->format('Y'),
    count($por_faixa['alerta']), count($por_faixa['ano']), count($por_faixa['depois']), count($por_faixa['vencido'])
);

$falta = static function (int $dias): string {
    if ($dias < 0) {
        return 'venceu há ' . -$dias . ($dias === -1 ? ' dia' : ' dias');
    }
    return $dias === 0 ? 'vence hoje' : 'faltam ' . $dias . ($dias === 1 ? ' dia' : ' dias');
};
?>

<header class="cabeca">
  <h1>Prazos e compromissos</h1>
  <p class="apoio">
    Os contratos, convênios, acordos e termos aditivos publicados no Diário, pela
    data em que acabam. Para que um compromisso firmado antes desta gestão não
    vença sem que ninguém perceba.
  </p>
</header>

<form class="quadro quadro--filtros filtro-interno" action="/interno/" method="get">
  <input type="hidden" name="p" value="prazos">
  <p class="campo">
    <label for="recorte">Quais instrumentos</label>
    <select id="recorte" name="recorte" data-aplica>
      <option value="sistema"<?= $recorte === 'sistema' ? ' selected' : '' ?>>Da SECTI e das vinculadas</option>
      <option value="cti"<?= $recorte === 'cti' ? ' selected' : '' ?>>De todo o recorte de ciência, tecnologia e inovação</option>
    </select>
  </p>
  <noscript><button type="submit" class="botao-leve">Mostrar</button></noscript>
</form>

<div class="numeros-prazo">
  <p class="numero-prazo numero-prazo--alerta">
    <strong><?= count($por_faixa['alerta']) ?></strong>
    <span><span class="marca-faixa marca-faixa--alerta" aria-hidden="true"></span>vencem em até 90 dias</span>
  </p>
  <p class="numero-prazo">
    <strong><?= count($por_faixa['ano']) ?></strong>
    <span><span class="marca-faixa marca-faixa--ano" aria-hidden="true"></span>vencem em até 1 ano</span>
  </p>
  <p class="numero-prazo">
    <strong><?= count($por_faixa['vencido']) ?></strong>
    <span><span class="marca-faixa marca-faixa--vencido" aria-hidden="true"></span>venceram nos últimos 6 meses</span>
  </p>
</div>

<figure class="quadro grafico-prazos">
  <figcaption>
    <strong>Vencimentos por mês</strong>
    <span class="apoio">Passe o mouse sobre um mês para ver o detalhe.</span>
  </figcaption>
  <ul class="legenda">
<?php foreach ($ORDEM as $f): ?>
    <li><span class="marca-faixa marca-faixa--<?= $f ?>" aria-hidden="true"></span><?= e($FAIXAS[$f]) ?></li>
<?php endforeach; ?>
  </ul>
  <svg viewBox="0 0 <?= $W ?> <?= $H ?>" role="img" aria-label="<?= e($resumo_grafico) ?>" class="grafico">
    <?= implode("\n    ", $svg) ?>
  </svg>
</figure>

<?php if (!$itens): ?>
<div class="quadro vazio">
  <p class="vazio__titulo">Nenhum prazo nesta janela.</p>
  <p class="vazio__dica">
    Ou os prazos ainda não foram lidos do acervo, ou nenhum extrato publicado
    tem vigência que termine entre <?= data_br($primeiro->format('Y-m-d')) ?> e
    <?= data_br($ultimo->format('Y-m-d')) ?>.
  </p>
</div>
<?php endif; ?>

<?php foreach (['alerta', 'ano', 'depois', 'vencido'] as $f): ?>
<?php if ($por_faixa[$f]): ?>
<section class="quadro faixa-prazos">
  <h2><span class="marca-faixa marca-faixa--<?= $f ?>" aria-hidden="true"></span><?= e($FAIXAS[$f]) ?>
    <span class="apoio">(<?= count($por_faixa[$f]) ?>)</span></h2>
  <div class="tabela-rolante">
  <table class="tabela-atos tabela-prazos">
    <thead>
      <tr>
        <th scope="col" class="col-data">Termina</th>
        <th scope="col">Instrumento e partes</th>
        <th scope="col">Objeto</th>
        <th scope="col" class="col-valor">Valor</th>
        <th scope="col" class="col-acao">Fonte</th>
      </tr>
    </thead>
    <tbody>
<?php foreach ($f === 'vencido' ? array_reverse($por_faixa[$f]) : $por_faixa[$f] as $i): ?>
      <tr>
        <td class="col-data">
          <strong><?= data_br($i['fim']) ?></strong>
          <span class="apoio prazo-falta"><?= e($falta($i['dias'])) ?></span>
        </td>
        <td>
          <span class="especie__nome"><?= e($i['instrumento'] ?: 'Instrumento sem nome no extrato') ?></span>
          <p class="ementa"><?= e($i['partes'] ?: '') ?></p>
        </td>
        <td><p class="ementa" title="<?= e($i['objeto'] ?? '') ?>"><?= e($i['objeto'] ?: '—') ?></p></td>
        <td class="col-valor"><?= e($i['valor'] ?: '—') ?></td>
        <td class="col-acao">
          <a href="/ato/<?= e($i['ato_id']) ?>">Ver extrato<span class="oculto-visualmente"> de <?= e($i['instrumento'] ?? '') ?></span> <span aria-hidden="true">›</span></a>
          <span class="apoio prazo-como" title="De onde saiu a data de término"><?= e($i['como']) ?></span>
        </td>
      </tr>
<?php endforeach; ?>
    </tbody>
  </table>
  </div>
</section>
<?php endif; ?>
<?php endforeach; ?>

<div class="ressalva prosa">
  <p>
    <strong>De onde vêm estes prazos.</strong> Dos extratos publicados no Diário
    Oficial. Um compromisso cujo extrato saiu antes do período que o acervo cobre
    não aparece aqui — por isso o acervo está sendo estendido para os anos
    anteriores.
  </p>
  <p>
    Vale um por processo: quando o contrato foi prorrogado, conta o termo aditivo
    mais recente. E a data de término, quando o extrato não a escreve por extenso,
    é calculada — a coluna "Fonte" diz de onde saiu cada uma.
  </p>
</div>

<script src="<?= e(ativo('/assets/js/busca.js')) ?>" defer></script>

<?php
$conteudo = ob_get_clean();
$titulo = 'Prazos e compromissos';
$larga = true;
require dirname(__DIR__) . '/layout.php';
