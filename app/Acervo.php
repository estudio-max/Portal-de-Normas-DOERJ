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

    /**
     * As ordenações da lista, as mesmas do Portal de Normas da UFF.
     *
     * O SQL sai daqui, e não do endereço: a ordem entra no `ORDER BY`, que não
     * aceita parâmetro, então o que vem do visitante só escolhe uma chave desta
     * lista. A data de publicação desempata sempre, para a ordem não mudar entre
     * uma página e a seguinte.
     */
    public const ORDENS = [
        'data'    => ['Data', 'a.data_pub %s, a.numero %s'],
        'especie' => ['Espécie e número', 'COALESCE(a.tipo, a.rotulo) %s, a.numero %s, a.data_pub DESC'],
        'orgao'   => ['Órgão', 'a.orgao %s, a.data_pub DESC'],
        'status'  => ['Status', 'a.status %s, a.data_pub DESC'],
    ];

    /** @return array<string,int> */
    public static function panorama(): array
    {
        $linha = Banco::um(
            // `dias` e `edicoes` não são a mesma conta, e a home chamava um
            // pelo nome do outro: 179 dias de publicação viraram "179 edições"
            // onde havia 214. O Diário sai uma vez por dia útil, mas publica
            // suplemento quando precisa, e o suplemento é edição.
            'SELECT COUNT(*) AS atos, SUM(e_cti) AS cti,'
            . ' COUNT(DISTINCT data_pub) AS dias,'
            . ' (SELECT COUNT(*) FROM edicoes) AS edicoes,'
            . ' MIN(data_pub) AS primeiro, MAX(data_pub) AS ultimo FROM atos'
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
     * O termo escrito para o índice de texto completo, ou `null` quando ele não
     * serve e a busca tem de varrer tudo.
     *
     * Duas formas, conforme o que a pessoa digitou:
     *
     * - **Uma palavra só** vira `palavra*`, busca por prefixo. Sem o asterisco,
     *   quem digita "tecnolog" recebia as dez matérias que trazem essa letra
     *   solta e nenhuma das milhares que falam de tecnologia — pior que lento,
     *   porque parece uma resposta.
     * - **Mais de uma palavra**, ou palavra com pontuação como "SEI-260005",
     *   vira frase entre aspas. Aspas exigem as palavras juntas e na ordem, que
     *   é o que `LIKE '%a b%'` também faz. E fora das aspas o hífen significaria
     *   "sem esta palavra" no modo booleano, o que inverteria a busca.
     *
     * Devolve `null` quando nenhum token chega a três caracteres, que é o
     * mínimo que o InnoDB indexa: peneirar por um termo que o índice não conhece
     * devolveria vazio e esconderia o que o `LIKE` acharia.
     *
     * **O que esta peneira não sabe achar** é pedaço no meio de palavra —
     * "Duarte" procurando por "arte". É o preço aceito para a busca responder
     * em meio segundo em vez de quatro e meio, e a tela de resultado vazio diz
     * isso a quem procura.
     */
    private static function frase(string $q): ?string
    {
        $tokens = preg_split('/[^\p{L}\p{N}]+/u', trim($q), -1, PREG_SPLIT_NO_EMPTY) ?: [];
        $uteis = array_filter($tokens, static fn($t) => mb_strlen($t) >= 3);
        if (!$uteis) {
            return null;
        }
        if (count($tokens) === 1) {
            return $tokens[0] . '*';
        }
        return '"' . str_replace('"', ' ', $q) . '"';
    }

    /**
     * O `ORDER BY` pedido, sempre de dentro de `ORDENS`.
     *
     * O `a.id` no fim é o desempate que faltava. Metade das matérias de um dia
     * não tem número, e sem uma chave única no fim o MySQL fica livre para
     * devolver os empatados em qualquer ordem — e a mesma matéria pode cair em
     * duas páginas, ou em nenhuma.
     */
    private static function ordem(array $f): string
    {
        $sql = (self::ORDENS[$f['ordem'] ?? ''] ?? self::ORDENS['data'])[1];
        $dir = ($f['dir'] ?? '') === 'asc' ? 'ASC' : 'DESC';
        return str_replace('%s', $dir, $sql) . ', a.id';
    }

    /** @return array<int,int> Os anos que o acervo tem, do mais recente. */
    public static function anos(): array
    {
        return array_map('intval', array_column(
            Banco::todos('SELECT DISTINCT YEAR(data_pub) AS ano FROM atos ORDER BY ano DESC'),
            'ano'
        ));
    }

    /**
     * Os órgãos, para o filtro, em ordem alfabética.
     *
     * Ficam de fora os nomes que começam por "D.O." ou "do Estado": são o
     * cabeçalho de página de 2010, que o extrator da época leu como nome de
     * órgão. Estão no acervo, mas oferecer "D.O. 23 Ano XXXVI" como órgão no
     * menu seria mostrar o defeito como se fosse opção.
     *
     * @return array<string,string> slug => nome
     */
    public static function orgaos(): array
    {
        $linhas = Banco::todos(
            "SELECT orgao_slug, MIN(orgao) AS orgao FROM atos"
            . " WHERE orgao_slug <> '' AND orgao NOT LIKE 'D.O.%'"
            . " AND orgao NOT LIKE 'do Estado%'"
            . " GROUP BY orgao_slug ORDER BY orgao"
        );
        return array_column($linhas, 'orgao', 'orgao_slug');
    }

    /**
     * A busca, com os filtros combinando entre si.
     *
     * Até 2026-09-23 havia aqui uma segunda tentativa: quando a peneira do
     * índice não achava nada, a busca refazia varrendo o texto inteiro, para o
     * caso de alguém procurar um pedaço no meio de uma palavra. Saiu depois de
     * medida. Em todos os termos testados — números de ato como "50.477" e
     * "4.312/2009", processos inteiros e pela metade, nomes —, quando o índice
     * achava zero a varredura também achava zero. Ela nunca devolveu nada, e
     * custava 10 segundos a cada erro de digitação.
     *
     * @return array{itens: array<int,array<string,mixed>>, total: int}
     */
    public static function buscar(array $f, int $pagina = 1): array
    {
        $onde = [];
        $p = [];

        if (!empty($f['q'])) {
            // A PENEIRA E A CONFIRMAÇÃO
            //
            // O `LIKE '%termo%'` não usa índice: o MySQL lê as linhas todas,
            // sempre. Com 1.979 atos isso custava 30 ms e não incomodava
            // ninguém. Com 50 mil e 152 milhões de caracteres passou a custar
            // **4,5 segundos**, que é tempo de a pessoa achar que o site quebrou.
            //
            // O `MATCH` sobre o índice `ft_texto` responde a mesma coisa em 4
            // milésimos. Mas ele casa palavra inteira, e quem procura um pedaço
            // — "tecnolog" dentro de "tecnologia" — não acharia nada.
            //
            // Então os dois juntos: o índice **peneira** as linhas candidatas e
            // o `LIKE` **confirma** cada uma. O resultado é o do `LIKE` sozinho
            // para palavra inteira e começo de palavra, e a busca custa 0,1 s.
            // Termo curto demais para o índice vai direto ao `LIKE` — ver
            // `frase()`.
            //
            // Quatro marcadores diferentes para o mesmo valor, e não `:q`
            // repetido: com preparo nativo — que é o que usamos, porque a
            // emulação transforma parâmetro em concatenação — **o MySQL aceita
            // cada nome uma vez só**. Repetido, ele devolve "Invalid parameter
            // number" e a busca inteira cai.
            if (($frase = self::frase($f['q'])) !== null) {
                $onde[] = 'MATCH(c.texto) AGAINST (:ft IN BOOLEAN MODE)';
                $p['ft'] = $frase;
            }
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
        // O ano vira intervalo de datas, e não `YEAR(a.data_pub) = :ano`:
        // função aplicada à coluna impede o MySQL de usar o índice de data.
        if (!empty($f['ano'])) {
            $onde[] = 'a.data_pub BETWEEN :ano_ini AND :ano_fim';
            $p['ano_ini'] = $f['ano'] . '-01-01';
            $p['ano_fim'] = $f['ano'] . '-12-31';
        }
        if (!empty($f['orgao'])) {
            $onde[] = 'a.orgao_slug = :orgao';
            $p['orgao'] = $f['orgao'];
        }

        // A ORDEM DAS TABELAS DECIDE SE O ÍNDICE É USADO
        //
        // Escrito como `atos a LEFT JOIN ato_corpo c`, o MySQL é obrigado a
        // começar por `atos` — é o que `LEFT JOIN` significa — e a peneira do
        // índice de texto, que vive em `ato_corpo`, só pode ser aplicada depois
        // de já ter varrido 39 mil linhas. A contagem levava 3 segundos mesmo
        // com o `MATCH` no `WHERE`.
        //
        // Invertido, com junção interna a partir de `ato_corpo`, o otimizador
        // entra pelo índice: 25 milésimos. A junção interna não perde nada,
        // porque a relação é de um para um — 50.062 atos, 50.062 corpos, zero
        // órfãos, garantidos pela chave estrangeira.
        //
        // O corpo entra mesmo sem busca porque 83% das matérias não trazem
        // ementa, e sem o começo do texto a linha da lista fica muda: uma data,
        // um órgão e nada que diga do que o ato trata.
        $de = !empty($f['q'])
            ? 'ato_corpo c JOIN atos a ON a.id = c.ato_id'
            : 'atos a JOIN ato_corpo c ON c.ato_id = a.id';
        $filtro = $onde ? ' WHERE ' . implode(' AND ', $onde) : '';

        // A contagem dispensa o corpo quando ninguém busca texto: arrastar 152
        // milhões de caracteres para contar linhas custava 2,2 segundos.
        $conta = !empty($f['q']) ? $de : 'atos a';
        $total = (int) Banco::valor(
            'SELECT COUNT(*) FROM ' . $conta . $filtro,
            $p
        );

        // O deslocamento entra interpolado porque `LIMIT` não aceita parâmetro
        // em preparo de servidor. É inteiro forçado logo acima, e não vem de
        // texto do visitante.
        $pagina = max(1, $pagina);
        $salto = ($pagina - 1) * self::POR_PAGINA;

        // PRIMEIRO A PÁGINA, DEPOIS O TEXTO
        //
        // Pedir o texto junto com o `OFFSET` fazia o MySQL ler o começo de
        // cada matéria que ia pular: para mostrar a página 2.504, lia 50 mil
        // textos e jogava 50.040 fora — 5 segundos. Enquanto a paginação era só
        // "Anterior" e "Próxima", ninguém chegava lá; com a numerada, o fim da
        // lista fica a um clique. Então a página é escolhida só com `atos`, que
        // é leve, e o texto é buscado para as vinte que sobraram.
        $ids = array_column(Banco::todos(
            'SELECT a.id FROM ' . $conta . $filtro
            . ' ORDER BY ' . self::ordem($f)
            . ' LIMIT ' . self::POR_PAGINA . ' OFFSET ' . $salto,
            $p
        ), 'id');
        if (!$ids) {
            return ['itens' => [], 'total' => $total];
        }
        $marcas = [];
        $pi = [];
        foreach (array_values($ids) as $k => $id) {
            $marcas[] = ':i' . $k;
            $pi['i' . $k] = $id;
        }

        // As relações vêm como texto concatenado, e não numa segunda consulta
        // por linha: vinte atos por página dariam vinte idas ao banco para
        // mostrar uma etiqueta.
        $itens = Banco::todos(
            'SELECT a.id, a.tipo, a.numero, a.data_pub, a.data_ato, a.orgao,'
            . ' a.unidade, a.ementa, a.ementa_inferida, a.cabecalho, a.rotulo, a.processo,'
            . ' a.e_cti, a.confianca, a.entidade_sistema, a.pagina, a.status,'
            . ' LEFT(c.texto, 700) AS inicio,'
            . ' (SELECT GROUP_CONCAT(DISTINCT r.tipo_relacao ORDER BY r.tipo_relacao)'
            . '  FROM ato_relacoes r WHERE r.ato_id = a.id) AS relacoes'
            . ' FROM atos a JOIN ato_corpo c ON c.ato_id = a.id'
            . ' WHERE a.id IN (' . implode(', ', $marcas) . ')'
            . ' ORDER BY ' . self::ordem($f),
            $pi
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
