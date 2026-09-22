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

## Como o site funciona. Verificado em 2026-09-22, baixando PDF de verdade

São três passos:

| # | Endereço | O que faz |
|---|---|---|
| 1 | `do_ultima_edicao.php` | redireciona por `<meta refresh>` para o passo 2, com a data de hoje |
| 2 | `do_seleciona_edicao.php?data=<base64 de AAAAMMDD>` | HTML com a lista de cadernos do dia |
| 3 | `mostra_edicao.php?k=<chave>` | o PDF |

**O token da listagem é base64 três vezes** sobre `<GUID><timestamp Unix>`.
Três camadas, não uma.

**A chave do passo 3 não é o GUID.** O `viewer-min.js` monta a URL enfiando uma
letra no meio do GUID, na posição 12:

    k = guid[:12] + "P" + guid[12:]      documento inteiro
    k = guid[:12] + "D" + guid[12:] + n  só a página n

O `P`, o `D`, o `?` e o `k=` estão no fonte como `String.fromCharCode(80)`,
`(68)`, `(63)` e `(107)`. Ofuscação leve: não impede ninguém, só custa tempo.

O GUID também aparece limpo no HTML do visualizador, como `var pd = "..."`.

### A armadilha do 200

`mostra_edicao.php` responde `Erro.` (5 bytes) sem chave nenhuma, e responde
**200 com corpo vazio** para chave malformada. **200 não é sucesso aqui.** A
conferência é sobre o conteúdo: `Content-Type`, tamanho mínimo, assinatura
`%PDF`.

Foi isto que atrasou a descoberta: `?k=<base64 da data>` devolvia vazio, e o
vazio parecia chave inválida. Eram nome de parâmetro e formato de valor errados
ao mesmo tempo.

### O que mais se sabe, testado

- Datas passadas funcionam. Testei até 2010, e o acervo parece ir mais longe.
- Sábado, domingo e feriado devolvem **zero cadernos**, sem erro. É o jeito
  limpo de detectar dia sem edição.
- O número de cadernos muda com a época: 5 hoje, 11 em 2010, quando Ministério
  Público, Defensoria, Justiça Federal, do Trabalho e Eleitoral saíam no DOERJ.
- Dia com edição extra **repete o nome do caderno**. 15/01/2024 tem duas
  "Parte I (Poder Executivo)".
- O servidor manda `Content-Disposition: filename="Nao_Possui_Valor_Legal_*.pdf"`.
- **A chave é permanente.** A chave da edição de 15/01/2010 continuava servindo
  o arquivo em 22/09/2026, e a de hoje continuou valendo horas depois de
  capturada. O timestamp mora no token da listagem, não na chave do PDF. É isso
  que torna possível referenciar o PDF na origem em vez de guardá-lo.

### Este PDF não tem valor legal

O nome do arquivo diz isso, e é o próprio IOERJ dizendo. O que se coleta serve
para consulta e busca, e não substitui a publicação oficial. O portal tem que
dizer isso onde a pessoa lê, e não num rodapé.

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
