<?php
/**
 * O que aparece a quem chega à área interna sem ter entrado.
 *
 * Não diz como a proteção funciona nem por que está fechada: quem pode entrar
 * já sabe a quem pedir, e quem não pode não precisa saber mais que isto.
 */
declare(strict_types=1);
ob_start();
?>
<h1>Área restrita</h1>
<p class="prosa">
  Esta parte do portal é da equipe da Secretaria de Estado de Ciência,
  Tecnologia e Inovação, e só abre com usuário e senha.
</p>
<p class="prosa">
  Se você faz parte da equipe e ainda não tem acesso, peça a quem administra o
  portal. O resto do acervo continua aberto em <a href="/busca">Buscar</a>.
</p>
<?php
$conteudo = ob_get_clean();
$titulo = 'Área restrita';
require dirname(__DIR__) . '/layout.php';
