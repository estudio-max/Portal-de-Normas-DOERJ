<?php

/**
 * Carrega configuração, abre o banco e define os ajudantes que todas as
 * páginas usam.
 *
 * Sem framework e sem autoload de pacote: são cinco arquivos, e uma camada de
 * carregamento aqui seria mais código para resolver um problema que não existe.
 */

declare(strict_types=1);

define('RAIZ', dirname(__DIR__));

require RAIZ . '/app/Banco.php';
require RAIZ . '/app/Acervo.php';

/** @return array<string,mixed> */
function config(): array
{
    static $config = null;
    if ($config === null) {
        $arquivo = RAIZ . '/config/config.php';
        if (!is_file($arquivo)) {
            http_response_code(500);
            exit('Falta config/config.php. Copie de config/config.exemplo.php.');
        }
        $config = require $arquivo;
    }
    return $config;
}

function config_valor(string $chave, mixed $padrao = null): mixed
{
    return config()[$chave] ?? $padrao;
}

/**
 * Escapa para HTML.
 *
 * O nome é curto porque aparece em toda interpolação de view, e função de
 * escape que dá trabalho de escrever é função que alguém esquece.
 */
function e(?string $texto): string
{
    return htmlspecialchars($texto ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** 2026-09-22 vira 22/09/2026. */
function data_br(?string $iso): string
{
    if (!$iso) {
        return '—';
    }
    $d = DateTimeImmutable::createFromFormat('Y-m-d', substr($iso, 0, 10));
    return $d ? $d->format('d/m/Y') : $iso;
}

/**
 * Monta uma URL preservando os filtros que já estavam valendo.
 *
 * Quem está filtrando por órgão e clica numa categoria espera continuar
 * filtrado por órgão. Sem isto, cada clique zera o que a pessoa montou.
 */
function url_com(array $mudancas, string $caminho = '/busca'): string
{
    $atual = $_GET;
    foreach ($mudancas as $chave => $valor) {
        if ($valor === null || $valor === '') {
            unset($atual[$chave]);
        } else {
            $atual[$chave] = $valor;
        }
    }
    unset($atual['pagina']);
    $query = http_build_query($atual);
    return $caminho . ($query ? '?' . $query : '');
}

/**
 * As primeiras linhas úteis de uma matéria, para quando o Diário não publicou
 * ementa — o caso de 83% delas.
 *
 * Toda matéria começa repetindo a hierarquia em caixa alta: SECRETARIA DE
 * ESTADO DE POLÍCIA MILITAR, DIRETORIA GERAL DE SAÚDE, DESPACHO DO ORDENADOR.
 * Isso já está nas colunas de órgão e de espécie, e se ficasse aqui gastaria as
 * duas linhas de resumo repetindo o que a pessoa acabou de ler. Então o corte é
 * nas linhas sem nenhuma letra minúscula, que é o que distingue o preâmbulo do
 * texto do ato.
 *
 * Quando a poda não deixa nenhuma minúscula — matéria que é só tabela, ou só
 * nomes em caixa alta — o texto volta inteiro: numa planilha de orçamento, o
 * cabeçalho da tabela é justamente o que explica as linhas de baixo.
 */
function resumo(?string $texto, int $largura = 190): string
{
    if ($texto === null || trim($texto) === '') {
        return '';
    }
    $corpo = preg_replace('/^(?:[^\p{Ll}\n]*\n)+/u', '', $texto) ?: '';
    // Sem nenhuma minúscula no que sobrou, a poda não achou texto de ato: é
    // tabela de anexo, lista de nomes, planilha de orçamento. Aí o corte só
    // esconderia o cabeçalho da tabela, que é a parte que explica o resto.
    if (!preg_match('/\p{Ll}/u', $corpo)) {
        $corpo = $texto;
    }
    $corpo = trim(preg_replace('/\s+/u', ' ', $corpo) ?? '');
    // mb_strimwidth cola a reticência onde a conta bateu, e quando isso cai num
    // espaço sai um " …" solto.
    return preg_replace('/\s+…$/u', '…', mb_strimwidth($corpo, 0, $largura, '…')) ?? '';
}

/**
 * Remonta os parágrafos do texto publicado, para leitura em tela.
 *
 * O Diário é composto em coluna de pouco mais de sete centímetros, e quebra a
 * linha onde a coluna acaba — no meio da frase, quase sempre. Reproduzir essas
 * quebras numa tela larga dá um texto em serrote, que foi como este portal
 * nasceu e não servia para ler.
 *
 * **A junção acontece só aqui, na exibição.** O texto guardado continua fiel ao
 * que o PDF traz: é dele que sai a busca, e é ele que alguém confere contra a
 * fonte. Se esta regra errar, o que se perde é a aparência de uma página, e não
 * o acervo.
 *
 * A regra é conservadora de propósito: só junta quando a linha seguinte
 * **começa em minúscula**, que é sinal inequívoco de frase interrompida.
 * Cabeçalho, artigo, assinatura e item de lista começam em maiúscula ou em
 * número, e ficam onde estão.
 *
 * @return array<int,string>
 */
function paragrafos(?string $texto): array
{
    if (!$texto) {
        return [];
    }

    $saida = [];
    foreach (preg_split('/\R/u', $texto) as $linha) {
        $linha = trim($linha);
        if ($linha === '') {
            continue;
        }

        $anterior = $saida ? $saida[count($saida) - 1] : null;
        $fechou = $anterior !== null && preg_match('/[.:;!?]$/u', $anterior);

        // Palavra de ligação no fim da linha: a frase está no meio, e o que vem
        // a seguir continua dela mesmo em caixa alta. É o caso do Diário
        // escrever "FAPERJ VINCULADA À" e seguir com "SECRETARIA DE ESTADO..."
        // na linha de baixo — sem isto, as duas ficariam separadas.
        $pendurada = $anterior !== null && preg_match(
            '/\b(a|à|às|ao|aos|o|os|as|de|da|do|das|dos|e|em|no|na|nos|nas|'
            . 'para|por|pelo|pela|com|que|ou|um|uma|seu|sua|este|esta|entre|'
            . 'sobre|sob)$/ui',
            $anterior
        );

        $continua = $anterior !== null && !$fechou && (
            // Começa em minúscula: sinal inequívoco de frase interrompida.
            preg_match('/^\p{Ll}/u', $linha) || $pendurada
        );

        if ($continua) {
            $saida[count($saida) - 1] = $anterior . ' ' . $linha;
        } else {
            $saida[] = $linha;
        }
    }
    return $saida;
}

function ver(string $view, array $dados = []): void
{
    extract($dados, EXTR_SKIP);
    require RAIZ . '/app/Views/' . $view . '.php';
}
