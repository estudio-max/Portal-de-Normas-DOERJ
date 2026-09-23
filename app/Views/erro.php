<?php
/** @var int $codigo @var string $mensagem */
declare(strict_types=1);
ob_start();
?>
<h1><?= (int) $codigo === 404 ? 'Não achei' : 'Deu errado' ?></h1>
<p class="prosa"><?= e($mensagem) ?></p>
<?php if ((int) $codigo === 404): ?>
<p class="prosa">
  O acervo tem oito edições entre 2010 e 2026, e não o Diário inteiro. Se o ato
  que você procura é de uma data que ainda não foi coletada, ele não está aqui —
  e nesse caso a falta é nossa, não sua.
</p>
<p><a href="/busca">Buscar no que já existe</a> · <a href="/">Voltar ao início</a></p>
<?php endif; ?>
<?php
$conteudo = ob_get_clean();
$titulo = (int) $codigo === 404 ? 'Não achei' : 'Erro';
require __DIR__ . '/layout.php';
