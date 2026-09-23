<?php
/**
 * Prova as duas funções que arrumam texto para a tela.
 *
 *     php app/provar_texto.php
 *
 * São as únicas duas do portal que decidem alguma coisa sobre o conteúdo, e as
 * duas erram do mesmo jeito se erradas: em silêncio, deixando a página feia sem
 * nada estourar. Por isso a prova é aqui e não no olho.
 *
 * Nenhuma das duas toca o banco nem a rede, então este arquivo roda sozinho.
 */
declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

$falhas = 0;

function checa(string $oque, mixed $obtido, mixed $esperado): void
{
    global $falhas;
    if ($obtido === $esperado) {
        echo "  ok    $oque\n";
        return;
    }
    $falhas++;
    echo "  FALHA $oque\n";
    echo "        esperado: " . var_export($esperado, true) . "\n";
    echo "        obtido:   " . var_export($obtido, true) . "\n";
}

echo "resumo()\n";

// O caso que motivou a função: o preâmbulo em caixa alta já está nas colunas de
// órgão e de espécie, e não pode gastar as duas linhas de resumo.
checa(
    'corta o preâmbulo em caixa alta',
    resumo("SECRETARIA DE ESTADO DE POLÍCIA MILITAR\nDIRETORIA GERAL DE SAÚDE\nDESPACHO DO ORDENADOR DE DESPESAS\nAUTORIZO a despesa referente à aquisição de material."),
    'AUTORIZO a despesa referente à aquisição de material.'
);

checa(
    'acento em caixa alta não conta como minúscula',
    resumo("EXTRATO DE TERMO ADITIVO\nINSTRUMENTO: Termo nº 1/2026."),
    'INSTRUMENTO: Termo nº 1/2026.'
);

// Matéria que é só tabela ou só nomes: sem esta saída, a linha ficaria vazia.
checa(
    'sem nenhuma minúscula, devolve o texto mesmo assim',
    resumo("UO SIGLA FR ORÇAMENTO\n06010 GSI 1.500.100"),
    'UO SIGLA FR ORÇAMENTO 06010 GSI 1.500.100'
);

checa('texto nulo vira string vazia', resumo(null), '');
checa('texto só de espaço vira string vazia', resumo("   \n  "), '');
checa(
    'corta na largura pedida',
    resumo("Uma frase bem mais comprida do que a largura pedida aqui.", 20),
    'Uma frase bem mais…'
);
checa(
    'espaço repetido vira um só',
    resumo("PORTARIA\nfoi   deferido   o   pedido"),
    'foi deferido o pedido'
);

echo "\nparagrafos()\n";

// A quebra de coluna do Diário cai no meio da frase. Só isso se junta.
checa(
    'junta a linha que começa em minúscula',
    paragrafos("AUTORIZO a despesa referente à\naquisição de material de consumo."),
    ['AUTORIZO a despesa referente à aquisição de material de consumo.']
);

checa(
    'não junta o que começa em maiúscula',
    paragrafos("Art. 1º - Fica instituído o programa.\nArt. 2º - Esta Resolução entra em vigor."),
    ['Art. 1º - Fica instituído o programa.', 'Art. 2º - Esta Resolução entra em vigor.']
);

checa(
    'não junta item de lista numerado',
    paragrafos("São beneficiários:\n1 - o servidor efetivo;\n2 - o pensionista."),
    ['São beneficiários:', '1 - o servidor efetivo;', '2 - o pensionista.']
);

checa('texto nulo não dá parágrafo nenhum', paragrafos(null), []);
checa('linha em branco não vira parágrafo', paragrafos("Primeira.\n\n\nSegunda."), ['Primeira.', 'Segunda.']);

echo "\norgao_curto()\n";

// O papel da sigla da UFF: o que distingue uma pasta da outra.
checa('tira "Secretaria de Estado de"', orgao_curto('Secretaria de Estado de Polícia Militar'), 'Polícia Militar');
checa('tira "Secretaria de Estado da"', orgao_curto('Secretaria de Estado da Casa Civil'), 'Casa Civil');
checa('tira "Secretaria de Estado do"', orgao_curto('Secretaria de Estado do Ambiente e Sustentabilidade'), 'Ambiente e Sustentabilidade');
checa('não mexe no que não é secretaria', orgao_curto('Controladoria Geral do Estado'), 'Controladoria Geral do Estado');
checa('caixa alta vira caixa normal', orgao_curto('ATOS DO PODER EXECUTIVO'), 'Atos do poder executivo');
checa('vazio vira travessão', orgao_curto(''), '—');

echo "\nrotulo_legivel()\n";

checa('fórmula vira caixa normal', rotulo_legivel('ATO DO SECRETÁRIO'), 'Ato do secretário');
checa('hífen não atrapalha', rotulo_legivel('DESPACHOS DO DIRETOR-GERAL'), 'Despachos do diretor-geral');
// Uma palavra fora da fórmula e o rótulo fica como o Diário publicou. Caixa
// baixa às cegas transformaria a sigla em "ccerj".
checa('sigla desconhecida preserva tudo', rotulo_legivel('DESPACHO DO PRESIDENTE DA CCERJ'), 'DESPACHO DO PRESIDENTE DA CCERJ');
checa('o que já tem minúscula fica', rotulo_legivel('Decisão proferida na Sessão'), 'Decisão proferida na Sessão');

echo "\njanela_paginas()\n";

checa('poucas páginas: todas', janela_paginas(2, 4), [1, 2, 3, 4]);
checa('no meio: pontas, vizinhas e reticências', janela_paginas(50, 2504), [1, null, 49, 50, 51, null, 2504]);
checa('na primeira', janela_paginas(1, 2504), [1, 2, null, 2504]);
checa('na última', janela_paginas(2504, 2504), [1, null, 2503, 2504]);
checa('uma página só', janela_paginas(1, 1), [1]);

echo "\n";
if ($falhas > 0) {
    echo "$falhas prova(s) reprovada(s).\n";
    exit(1);
}
echo "tudo passou\n";
