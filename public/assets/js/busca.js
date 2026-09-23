/*
 * O filtro se aplica ao ser escolhido, como no Portal de Normas da UFF.
 *
 * É o único script do portal. Sem ele a página funciona igual: o botão Buscar
 * envia o mesmo formulário. `el.form` acha o formulário também para o select de
 * ordenação, que fica fora dele na tela e se liga pelo atributo `form`.
 */
document.querySelectorAll('[data-aplica]').forEach(function (el) {
  el.addEventListener('change', function () {
    if (el.form) el.form.submit();
  });
});
