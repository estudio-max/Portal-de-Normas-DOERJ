<?php

declare(strict_types=1);

/**
 * As consultas do portal.
 *
 * Um arquivo só, e não um repositório por tabela: são poucas consultas e todas
 * falam do mesmo assunto. Separar em camadas aqui seria organizar a estante
 * antes de ter os livros.
 */
final class Acervo
{
    /** Os rótulos das onze categorias, na ordem em que a tela os mostra. */
    public const NATUREZAS = [
        'contratos'    => 'Contratos e convênios',
        'despachos'    => 'Despachos em processos',
        'compras'      => 'Compras e licitações',
        'academico'    => 'Ensino e vida acadêmica',
        'pessoal'      => 'Pessoal',
        'comissoes'    => 'Comissões e fiscalização',
        'governanca'   => 'Governança e normas',
        'retificacoes' => 'Retificações e republicações',
        'orcamento'    => 'Orçamento e finanças',
        'contencioso'  => 'Julgamento e contencioso',
        'fomento'      => 'Fomento e bolsas',
    ];

    /** As três subsecretarias da SECTI, que são os ramos de CT&I. */
    public const RAMOS = [
        'governanca'   => 'Governança do sistema estadual',
        'conhecimento' => 'Conhecimento, pesquisa e formação',
        'inovacao'     => 'Inovação e ambientes produtivos',
    ];

    public const ENTIDADES = [
        'secti'   => 'SECTI',
        'faperj'  => 'FAPERJ',
        'uerj'    => 'UERJ',
        'uenf'    => 'UENF',
        'cecierj' => 'CECIERJ',
        'faetec'  => 'FAETEC',
    ];

    public const POR_PAGINA = 20;

    /** @return array<string,int> */
    public static function panorama(): array
    {
        $linha = Banco::um(
            'SELECT COUNT(*) AS atos, SUM(e_cti) AS cti,'
            . ' COUNT(DISTINCT data_pub) AS dias, MIN(data_pub) AS primeiro,'
            . ' MAX(data_pub) AS ultimo FROM atos'
        ) ?? [];
        return array_map(
            static fn ($v) => is_numeric($v) ? (int) $v : $v,
            $linha
        );
    }

    /** @return array<int,array<string,mixed>> */
    public static function porEntidade(): array
    {
        return Banco::todos(
            'SELECT entidade_sistema, COUNT(*) AS atos FROM atos'
            . ' WHERE entidade_sistema IS NOT NULL'
            . ' GROUP BY entidade_sistema ORDER BY atos DESC'
        );
    }

    /** @return array<int,array<string,mixed>> */
    public static function foraDoSistema(): array
    {
        // Confiança baixa fica de fora aqui de propósito: esta lista existe
        // para mostrar onde há CT&I fora da SECTI, e um contrato de impressora
        // que entrou pela palavra "tecnologia" não é isso.
        return Banco::todos(
            "SELECT orgao, COUNT(*) AS atos FROM atos"
            . " WHERE e_cti = 1 AND entidade_sistema IS NULL"
            . " AND confianca IN ('alta','media')"
            . " GROUP BY orgao ORDER BY atos DESC LIMIT 12"
        );
    }

    /** @return array<string,int> */
    public static function porNatureza(): array
    {
        $linhas = Banco::todos(
            'SELECT natureza, COUNT(*) AS n FROM ato_natureza GROUP BY natureza'
        );
        return array_column($linhas, 'n', 'natureza');
    }

    /**
     * A busca, com os filtros combinando entre si.
     *
     * @return array{itens: array<int,array<string,mixed>>, total: int}
     */
    public static function buscar(array $f, int $pagina = 1): array
    {
        $onde = [];
        $p = [];

        if (!empty($f['q'])) {
            // `LIKE` e não `MATCH`: o índice de texto completo do MySQL ignora
            // palavra com menos de quatro letras e não casa pedaço de palavra,
            // e quem procura "DECRETO 50.485" ou "SEI-150001" precisa das duas
            // coisas. Com o acervo neste tamanho, a diferença de velocidade não
            // aparece; quando aparecer, aí se troca.
            //
            // Quatro marcadores diferentes para o mesmo valor, e não `:q`
            // repetido: com preparo nativo — que é o que usamos, porque a
            // emulação transforma parâmetro em concatenação — **o MySQL aceita
            // cada nome uma vez só**. Repetido, ele devolve "Invalid parameter
            // number" e a busca inteira cai.
            $onde[] = '(a.ementa LIKE :q1 OR a.cabecalho LIKE :q2'
                . ' OR a.numero LIKE :q3 OR c.texto LIKE :q4)';
            $termo = '%' . $f['q'] . '%';
            $p['q1'] = $p['q2'] = $p['q3'] = $p['q4'] = $termo;
        }
        if (!empty($f['natureza'])) {
            $onde[] = 'EXISTS (SELECT 1 FROM ato_natureza n'
                . ' WHERE n.ato_id = a.id AND n.natureza = :natureza)';
            $p['natureza'] = $f['natureza'];
        }
        if (!empty($f['ramo'])) {
            $onde[] = 'EXISTS (SELECT 1 FROM ato_ramo r'
                . ' WHERE r.ato_id = a.id AND r.ramo = :ramo)';
            $p['ramo'] = $f['ramo'];
        }
        if (!empty($f['entidade'])) {
            $onde[] = 'a.entidade_sistema = :entidade';
            $p['entidade'] = $f['entidade'];
        }
        if (!empty($f['cti'])) {
            $onde[] = 'a.e_cti = 1';
        }
        if (!empty($f['tipo'])) {
            $onde[] = 'a.tipo = :tipo';
            $p['tipo'] = $f['tipo'];
        }
        if (!empty($f['status'])) {
            $onde[] = 'a.status = :status';
            $p['status'] = $f['status'];
        }
        if (!empty($f['de'])) {
            $onde[] = 'a.data_pub >= :de';
            $p['de'] = $f['de'];
        }
        if (!empty($f['ate'])) {
            $onde[] = 'a.data_pub <= :ate';
            $p['ate'] = $f['ate'];
        }

        $junta = !empty($f['q']) ? ' LEFT JOIN ato_corpo c ON c.ato_id = a.id' : '';
        $filtro = $onde ? ' WHERE ' . implode(' AND ', $onde) : '';

        $total = (int) Banco::valor(
            'SELECT COUNT(*) FROM atos a' . $junta . $filtro,
            $p
        );

        // O deslocamento entra interpolado porque `LIMIT` não aceita parâmetro
        // em preparo de servidor. É inteiro forçado logo acima, e não vem de
        // texto do visitante.
        $pagina = max(1, $pagina);
        $salto = ($pagina - 1) * self::POR_PAGINA;

        // As relações vêm como texto concatenado, e não numa segunda consulta
        // por linha: vinte atos por página dariam vinte idas ao banco para
        // mostrar uma etiqueta.
        $itens = Banco::todos(
            'SELECT a.id, a.tipo, a.numero, a.data_pub, a.data_ato, a.orgao,'
            . ' a.unidade, a.ementa, a.ementa_inferida, a.cabecalho, a.rotulo, a.processo,'
            . ' a.e_cti, a.confianca, a.entidade_sistema, a.pagina, a.status,'
            . ' (SELECT GROUP_CONCAT(DISTINCT r.tipo_relacao ORDER BY r.tipo_relacao)'
            . '  FROM ato_relacoes r WHERE r.ato_id = a.id) AS relacoes'
            . ' FROM atos a' . $junta . $filtro
            . ' ORDER BY a.data_pub DESC, a.numero'
            . ' LIMIT ' . self::POR_PAGINA . ' OFFSET ' . $salto,
            $p
        );

        return ['itens' => $itens, 'total' => $total];
    }

    /** @return array<string,mixed>|null */
    public static function ato(string $id): ?array
    {
        $ato = Banco::um(
            'SELECT a.*, c.texto, e.data_pub AS edicao_data, e.caderno,'
            . ' e.numero AS edicao_numero, e.paginas, e.url_pdf'
            . ' FROM atos a'
            . ' LEFT JOIN ato_corpo c ON c.ato_id = a.id'
            . ' LEFT JOIN edicoes e ON e.id = a.edicao_id'
            . ' WHERE a.id = :id',
            ['id' => $id]
        );
        if (!$ato) {
            return null;
        }

        $ato['naturezas'] = array_column(
            Banco::todos(
                'SELECT natureza, origem FROM ato_natureza WHERE ato_id = :id',
                ['id' => $id]
            ),
            'origem',
            'natureza'
        );
        $ato['ramos'] = array_column(
            Banco::todos(
                'SELECT ramo, origem FROM ato_ramo WHERE ato_id = :id',
                ['id' => $id]
            ),
            'origem',
            'ramo'
        );
        $ato['relacoes'] = Banco::todos(
            'SELECT tipo_relacao, ato_destino_texto, ato_destino_id, externo,'
            . ' parcial, dispositivo, origem'
            . ' FROM ato_relacoes WHERE ato_id = :id ORDER BY tipo_relacao',
            ['id' => $id]
        );
        // Quem alterou ou revogou este ato. É a pergunta que as pessoas fazem,
        // e ela se responde do outro lado da tabela.
        $ato['recebidas'] = Banco::todos(
            'SELECT r.tipo_relacao, r.parcial, r.dispositivo, r.origem,'
            . ' o.id, o.tipo, o.numero, o.data_pub'
            . ' FROM ato_relacoes r JOIN atos o ON o.id = r.ato_id'
            . ' WHERE r.ato_destino_id = :id ORDER BY o.data_pub DESC',
            ['id' => $id]
        );

        return $ato;
    }

    /** @return array<int,string> */
    public static function tipos(): array
    {
        return array_column(
            Banco::todos(
                'SELECT tipo, COUNT(*) AS n FROM atos WHERE tipo IS NOT NULL'
                . ' GROUP BY tipo HAVING n > 1 ORDER BY n DESC LIMIT 14'
            ),
            'tipo'
        );
    }
}
