<?php
declare(strict_types=1);
ob_start();

$panorama = Acervo::panorama();
$entidades = Acervo::porEntidade();
$fora = Acervo::foraDoSistema();
$naturezas = Acervo::porNatureza();
?>

<h1>O que o Estado publicou, de um jeito em que dê para achar</h1>

<p class="prosa">
  Os atos do Poder Executivo do Rio de Janeiro saem todo dia útil no Diário
  Oficial. Para ler um deles é preciso saber a data, abrir o PDF e procurar —
  quem não sabe a data não acha. Aqui dá para procurar pelo assunto.
</p>

<form class="busca-grande" action="/busca" method="get" role="search">
  <label for="q">Buscar no acervo</label>
  <div class="busca-grande__linha">
    <input type="search" id="q" name="q" autocomplete="off"
           placeholder="número do ato, órgão, assunto, processo SEI">
    <button type="submit" class="botao">Buscar</button>
  </div>
</form>

<p class="numeros">
  <strong><?= number_format($panorama['atos'] ?? 0, 0, ',', '.') ?></strong> matérias publicadas
  em <strong><?= (int) ($panorama['edicoes'] ?? 0) ?></strong> edições,
  de <?= data_br($panorama['primeiro'] ?? null) ?>
  a <?= data_br($panorama['ultimo'] ?? null) ?>.
</p>

<h2>Por categoria</h2>
<p class="prosa apoio">
  O que o ato faz. Uma matéria pode estar em mais de uma — um despacho que
  autoriza um contrato é as duas coisas.
</p>

<ul class="grade">
<?php foreach (Acervo::NATUREZAS as $chave => $nome): ?>
  <li>
    <a href="<?= e(url_com(['natureza' => $chave], '/busca')) ?>">
      <span class="grade__nome"><?= e($nome) ?></span>
      <span class="grade__n"><?= number_format($naturezas[$chave] ?? 0, 0, ',', '.') ?></span>
    </a>
  </li>
<?php endforeach; ?>
</ul>

<h2>Ciência, tecnologia e inovação</h2>
<p class="prosa apoio">
  <strong><?= number_format($panorama['cti'] ?? 0, 0, ',', '.') ?></strong>
  matérias entraram no recorte de CT&amp;I. O vocabulário que define esse
  recorte sai do regimento interno da SECTI e da Lei estadual nº 9.809/2022 —
  não foi inventado aqui.
</p>

<div class="duas-colunas">
  <section>
    <h3>O sistema da SECTI</h3>
    <p class="apoio">
      As vinculadas publicam sob o nome da secretaria. Aqui cada uma tem o seu
      espaço.
    </p>
    <ul class="lista-simples">
<?php foreach ($entidades as $linha): ?>
      <li>
        <a href="<?= e(url_com(['entidade' => $linha['entidade_sistema']], '/busca')) ?>">
          <?= e(Acervo::ENTIDADES[$linha['entidade_sistema']] ?? $linha['entidade_sistema']) ?>
        </a>
        <span class="apoio"><?= (int) $linha['atos'] ?></span>
      </li>
<?php endforeach; ?>
    </ul>
  </section>

  <section>
    <h3>CT&amp;I nas outras pastas</h3>
    <p class="apoio">
      Ciência e inovação não acontecem só na SECTI. Estes são os órgãos que
      decidiram sobre o tema e que hoje ninguém vê juntos.
    </p>
    <ul class="lista-simples">
<?php foreach (array_slice($fora, 0, 8) as $linha): ?>
      <li>
        <a href="<?= e(url_com(['q' => $linha['orgao'], 'cti' => 1], '/busca')) ?>">
          <?= e($linha['orgao'] ?: 'sem órgão identificado') ?>
        </a>
        <span class="apoio"><?= (int) $linha['atos'] ?></span>
      </li>
<?php endforeach; ?>
    </ul>
  </section>
</div>

<h2>Por ramo</h2>
<p class="prosa apoio">
  Os três ramos são as três subsecretarias da SECTI. Só as matérias com
  conteúdo temático recebem ramo: o sistema publica sobretudo ato
  administrativo.
</p>
<ul class="grade grade--larga">
<?php foreach (Acervo::RAMOS as $chave => $nome): ?>
  <li>
    <a href="<?= e(url_com(['ramo' => $chave], '/busca')) ?>">
      <span class="grade__nome"><?= e($nome) ?></span>
    </a>
  </li>
<?php endforeach; ?>
</ul>

<?php
$conteudo = ob_get_clean();
$titulo = 'Início';
$descricao = 'Atos do Poder Executivo do Estado do Rio de Janeiro, publicados '
    . 'no Diário Oficial, com busca por assunto.';
require __DIR__ . '/layout.php';
