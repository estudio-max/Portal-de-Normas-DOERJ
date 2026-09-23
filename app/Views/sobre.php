<?php
declare(strict_types=1);
ob_start();
?>
<h1>Sobre este portal</h1>

<div class="prosa">
<p>
  O Diário Oficial do Estado do Rio de Janeiro publica todo dia útil os atos do
  Poder Executivo. É informação pública e quase inacessível: para ler um ato é
  preciso saber a data, abrir o PDF daquele dia e procurar. Quem não sabe a data
  não acha.
</p>

<h2>De onde vem o conteúdo</h2>
<p>
  Da Parte I — Poder Executivo, publicada pela Imprensa Oficial do Estado. O
  arquivo é baixado, o texto é extraído e cada matéria publicada vira um
  registro, separada pelo identificador que a própria Imprensa Oficial coloca no
  fim de cada uma.
</p>
<p class="ressalva">
  <strong>O arquivo de origem não tem valor legal.</strong> É o próprio IOERJ
  que o nomeia assim. Este portal serve para consultar, buscar e pesquisar — não
  substitui a publicação oficial.
</p>

<h2>O que foi retirado, e por quê</h2>
<p>
  CPF, documento de identidade e endereço residencial de particular não entram
  aqui. São removidos na extração, antes de qualquer gravação: o banco nunca
  chega a vê-los.
</p>
<p>
  O nome de servidor fica. Nomeação e exoneração são atos públicos, e esconder o
  nome esvaziaria a transparência que motiva o projeto. O que sai é o documento,
  que não acrescenta nada à fiscalização e acrescenta tudo ao risco.
</p>
<p>
  O Diário é publicação oficial e esses dados estão lá. A diferença é o que
  acontece depois: um PDF por dia, que exige saber a data, é uma coisa; um
  acervo de anos com busca por texto é outra. Por isso este portal também pede
  aos buscadores que não o indexem.
</p>

<h2>A classificação é automática</h2>
<p>
  As categorias e os temas saem de vocabulário, não de leitura humana. Cada ato
  mostra como foi classificado e por quê, e a marca de automático aparece junto.
  Ela erra — e aparecer identificada é o que permite a quem lê descontar o erro.
</p>
<p>
  O vocabulário de ciência, tecnologia e inovação vem do regimento interno da
  SECTI e da Lei estadual nº 9.809/2022. Não foi inventado aqui, e é por isso
  que cada termo pode ser conferido contra um artigo.
</p>

<h2>O que este portal não responde</h2>
<p>
  <strong>Quanto a pasta gastou.</strong> O Diário publica movimentação
  orçamentária — crédito suplementar, contrato, empenho —, e não o orçamento.
  A Lei Orçamentária e a execução consolidada vivem no SIAFE-Rio e no portal da
  Transparência. Somar o que aparece aqui e chamar de gasto do órgão seria
  produzir um número errado com aparência de certo.
</p>
</div>
<?php
$conteudo = ob_get_clean();
$titulo = 'Sobre';
require __DIR__ . '/layout.php';
