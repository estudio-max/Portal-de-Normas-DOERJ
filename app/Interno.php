<?php

declare(strict_types=1);

/**
 * As consultas da área interna.
 *
 * Nada daqui é gravado em tabela: os painéis perguntam ao acervo na hora, pelo
 * índice de texto. Assim não existe coluna "ação dos 100 Dias" que uma consulta
 * pública pudesse deixar escapar. A exceção é `ato_prazo`, e ela não é interna —
 * é o extrato publicado no Diário, lido pelo `tools/doerj_prazos.py`.
 */
final class Interno
{
    /** Quantos dias antes do fim um prazo passa a pedir atenção. */
    public const ALERTA_DIAS = 90;

    /** A SECTI ou uma das sete vinculadas do art. 51, como aparecem nas partes de um extrato. */
    private const PARTE_DO_SISTEMA = '/\b(faperj|uerj|uenf|cecierj|faetec|fatec|funcierj)\b'
        . '|carlos chagas filho|universidade do estado do rio de janeiro|norte fluminense'
        . '|educa[cç][aã]o superior a dist[aâ]ncia|apoio [aà] escola t[eé]cnica'
        . '|secretaria de estado de ci[eê]ncia/iu';

    /** @return array{cem_dias: array, regimento: array} */
    public static function config(): array
    {
        static $c = null;
        if ($c === null) {
            $arquivo = RAIZ . '/config/interno.php';
            $c = is_file($arquivo) ? require $arquivo : [];
            $c += ['cem_dias' => [], 'regimento' => []];
        }
        return $c;
    }

    /** O mesmo filtro nos dois lugares que usam uma expressão. */
    private static function onde(array $item): string
    {
        return 'MATCH(c.texto) AGAINST (:expr IN BOOLEAN MODE)'
            . (!empty($item['so_cti']) ? ' AND a.e_cti = 1' : '');
    }

    /**
     * Quantas matérias o índice acha para cada item.
     *
     * @return array<int,array<string,mixed>> os itens, cada um com `n`
     */
    public static function contar(array $itens): array
    {
        foreach ($itens as $k => $item) {
            $itens[$k]['n'] = (int) Banco::valor(
                'SELECT COUNT(*) FROM ato_corpo c JOIN atos a ON a.id = c.ato_id WHERE '
                . self::onde($item),
                ['expr' => $item['expr']]
            );
        }
        return $itens;
    }

    /** @return array<int,array<string,mixed>> as matérias de um item, as mais novas primeiro */
    public static function materias(array $item, int $limite = 60): array
    {
        return Banco::todos(
            'SELECT a.id, a.data_pub, a.tipo, a.numero, a.rotulo, a.orgao, a.ementa,'
            . ' LEFT(c.texto, 700) AS inicio'
            . ' FROM ato_corpo c JOIN atos a ON a.id = c.ato_id WHERE ' . self::onde($item)
            . ' ORDER BY a.data_pub DESC, a.id LIMIT ' . max(1, min(200, $limite)),
            ['expr' => $item['expr']]
        );
    }

    /**
     * Os instrumentos que vencem numa janela, do que acaba antes ao que acaba
     * depois.
     *
     * UM POR PROCESSO. O mesmo contrato aparece no extrato original e em cada
     * termo aditivo, e cada um traz a sua data de fim. Vale a do extrato mais
     * recente — é o aditivo que prorrogou. Sem isto, o contrato de 2024
     * prorrogado em 2026 apareceria duas vezes, uma delas vencida.
     *
     * O limite é que dois instrumentos distintos no mesmo processo viram um.
     * É raro no acervo — convênio costuma ter processo próprio —, e está dito na
     * tela.
     *
     * @param string $recorte 'sistema' (a SECTI e as vinculadas) ou 'cti' (todo o recorte)
     * @return array<int,array<string,mixed>>
     */
    public static function prazos(string $desde, string $ate, string $recorte): array
    {
        $quem = $recorte === 'cti'
            ? '(a.entidade_sistema IS NOT NULL OR a.e_cti = 1)'
            : 'a.entidade_sistema IS NOT NULL';
        // Traz também o que venceu antes da janela, para saber se um processo
        // foi prorrogado para dentro dela ou para fora.
        $linhas = Banco::todos(
            'SELECT p.*, a.data_pub, a.entidade_sistema, a.orgao, a.unidade'
            . ' FROM ato_prazo p JOIN atos a ON a.id = p.ato_id'
            . ' WHERE ' . $quem
            . ' ORDER BY a.data_pub DESC, p.ato_id, p.ordem'
        );

        $vistos = [];
        $saida = [];
        foreach ($linhas as $l) {
            // Compromisso da SECTI é aquele em que a SECTI ou uma vinculada é
            // PARTE. Matéria que só cita uma vinculada no texto trazia contrato
            // da Polícia Militar e estágio da Procuradoria — 144 de 1.293. Se o
            // extrato não lista as partes (há os que escrevem "CONTRATANTE"),
            // vale quem publicou.
            if ($recorte === 'sistema' && $l['partes'] && !preg_match(self::PARTE_DO_SISTEMA, $l['partes'])) {
                continue;
            }
            // Termo de estágio: por lei a escola do estudante assina junto, e a
            // UERJ aparecia como parte do estágio que a Fazenda concede. Aqui
            // conta só quem concede, que é a primeira parte. O convênio de
            // estágio da UENF com uma empresa continua, porque ali a UENF vem
            // primeiro.
            if ($recorte === 'sistema'
                && preg_match('/est[aá]gi/iu', ($l['instrumento'] ?? '') . ' ' . ($l['objeto'] ?? ''))) {
                $primeira = preg_split('/,?\s+e\s+(?:a|o)\s+|,\s+(?:a|o)\s+estudante/iu', (string) $l['partes'], 2)[0];
                if (!preg_match(self::PARTE_DO_SISTEMA, $primeira)) {
                    continue;
                }
            }
            $chave = $l['processo'] ? 'p:' . strtoupper(preg_replace('/\W/', '', $l['processo'])) : 'i:' . $l['id'];
            if (isset($vistos[$chave])) {
                continue;
            }
            $vistos[$chave] = true;
            if ($l['fim'] >= $desde && $l['fim'] <= $ate) {
                $saida[] = $l;
            }
        }
        usort($saida, static fn ($x, $y) => [$x['fim'], $x['id']] <=> [$y['fim'], $y['id']]);
        return $saida;
    }

    /**
     * A faixa de urgência de um prazo, contada de hoje.
     *
     * @return 'vencido'|'alerta'|'ano'|'depois'
     */
    public static function faixa(string $fim, DateTimeImmutable $hoje): string
    {
        $dias = (int) $hoje->diff(new DateTimeImmutable($fim))->format('%r%a');
        return match (true) {
            $dias < 0 => 'vencido',
            $dias <= self::ALERTA_DIAS => 'alerta',
            $dias <= 365 => 'ano',
            default => 'depois',
        };
    }
}
