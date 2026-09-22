# Portal de Normas — DOERJ

Contexto para quem (pessoa ou Claude Code) entra neste projeto.

## O que é

Baixar, processar e publicar as normas do **Diário Oficial do Estado do Rio de
Janeiro, Poder Executivo**, no mesmo formato do Portal de Normas e Atos da UFF.

## Duas listas, e a diferença entre elas importa

Este arquivo separa **o que foi verificado contra o site real** do **que foi
recebido de outra sessão e ainda não conferido**. Misturar as duas é como o
projeto começa a mentir: alguém lê uma afirmação herdada, implementa em cima, e
só descobre que era falsa depois de três camadas construídas.

---

## Verificado em 2026-09-22, contra o site real

| O quê | Como se sabe |
|---|---|
| `https://www.ioerj.com.br/` responde 302 para `/portal/` | `curl -I` |
| O portal roda XOOPS; o `portal.ioerj.com.br` é outro site, em WordPress, e é institucional | HTML das duas origens |
| Existe `…/portal/modules/conteudoonline/mostra_edicao.php` | responde 200 |
| **Sem parâmetro, ele devolve exatamente `Erro.`** — 5 bytes | `curl` sem query |
| **Com `?k=<base64>` de uma data, devolve corpo vazio** | testado com `21/09/2026`, `2026-09-21`, `20260921`, `22/09/2026` |

A última linha é a mais importante, e confirma a armadilha que o handoff
anunciava: **o endpoint aceita uma chave malformada sem reclamar.** Ele só diz
`Erro.` quando não há chave nenhuma. Chave presente e inválida sai como resposta
vazia, com status 200.

Consequência prática para quem for escrever o downloader: **200 não é sucesso
aqui.** A verificação tem que ser sobre o corpo — tamanho, tipo do conteúdo,
assinatura `%PDF`. Um downloader que confie no código de status vai gravar
centenas de arquivos vazios e o log vai dizer que deu tudo certo.

### O que não achei

A etapa que traduz **data → GUID**. Os caminhos abaixo responderam 404:
`conteudo.php`, `lista_edicoes.php`, `edicoes.php`, `busca.php`, `pesquisa.php`,
`lista.php`, `consulta.php`, `mostra_lista.php`. A página do módulo
(`/portal/modules/conteudoonline/`) é só a casca do portal, sem seletor de data
no HTML estático — o que sugere que a listagem vem por JavaScript ou por um
bloco que não é servido nessa URL.

Segunda rodada, no mesmo dia, para não repetir o caminho depois:

| Onde procurei | O que achei |
|---|---|
| HTML do módulo, lista de `<script>` | só scripts do tema: jQuery, carrossel, lightbox. Nenhum seletor de data, nenhuma chamada a `mostra_edicao` |
| `themes/IOERJV2/js/main.js` e `governo.js` | 404 disfarçado de 200, com 230 bytes |
| Todos os `href` internos da página | nada aponta para edição do Diário |
| `/do/` | existe, mas responde 403; é de onde o portal serve CSS do tema |
| 12 pontos de entrada dentro de `/do/` | todos 404 |

Conclusão provisória: a listagem de edições não está nesta página. Ou ela mora
noutro host (`transparencia.ioerj.com.br` e o `asps/login.asp` ainda não foram
examinados), ou depende de sessão, ou vem de uma chamada que o HTML estático não
revela. Achar isso passa por abrir o site num navegador e olhar as requisições
de rede, e não por adivinhar nomes de arquivo.

---

## Recebido de outra sessão, **ainda não verificado**

Repassado em 2026-09-22, descrevendo um downloader que funcionava. O código não
chegou a esta máquina. Tratar como pista, não como fato:

- o esquema seria **data em base64 → GUID → `?k=`**;
- havia observações sobre o texto extraído do PDF que não foram detalhadas aqui.

O primeiro item bate parcialmente com o que verifiquei: o `?k=` existe e aceita
base64. Falta a ponte para o GUID.

---

## Regras deste projeto

1. **Nunca inventar um fato sobre o site.** Se não foi testado, vai para a lista
   de baixo com a etiqueta de não verificado.
2. **200 não é sucesso.** Ver acima.
3. **PDF não entra no git.** São ~80 páginas por dia. `dados/` está no
   `.gitignore`; os PDFs vivem como artifact do Actions por 7 dias até a Fase 3
   definir o destino permanente.
4. **Nada de credencial no repositório**, nem em exemplo, nem em teste.
5. O trabalho segue `REQUIREMENTS.md`, `ARCHITECTURE.md` e `STEPS.md`, nessa
   ordem, e eles são atualizados com o que mudou de verdade — não com o que se
   pretendia fazer.

## Risco conhecido, ainda não medido

O runner do GitHub Actions fica nos Estados Unidos, e sites de governo estadual
às vezes recusam endereço estrangeiro. Se o download funcionar na máquina local
e falhar no Actions, as saídas são cron na hospedagem ou runner self-hosted. Ver
a Fase 2 do `STEPS.md`.
