<?php

declare(strict_types=1);

/**
 * A ligação com o MySQL.
 *
 * Tudo que chega do visitante vai por parâmetro, nunca concatenado na consulta.
 * Este portal publica texto vindo de PDF e recebe busca livre de quem quiser —
 * são as duas pontas por onde injeção entra, e nenhuma delas admite atalho.
 */
final class Banco
{
    private static ?PDO $pdo = null;

    public static function pdo(): PDO
    {
        if (self::$pdo instanceof PDO) {
            return self::$pdo;
        }

        $c = config_valor('banco', []);
        $dsn = sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
            $c['host'] ?? '127.0.0.1',
            (int) ($c['porta'] ?? 3306),
            $c['nome'] ?? 'doerj'
        );

        self::$pdo = new PDO($dsn, $c['usuario'] ?? '', $c['senha'] ?? '', [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            // Preparo de verdade no servidor, e não emulado no cliente: com a
            // emulação ligada, o PDO monta a consulta como texto antes de
            // enviar, e o parâmetro volta a ser concatenação com outro nome.
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);

        return self::$pdo;
    }

    /** @return array<int,array<string,mixed>> */
    public static function todos(string $sql, array $parametros = []): array
    {
        $consulta = self::pdo()->prepare($sql);
        $consulta->execute($parametros);
        return $consulta->fetchAll();
    }

    /** @return array<string,mixed>|null */
    public static function um(string $sql, array $parametros = []): ?array
    {
        $linha = self::todos($sql, $parametros)[0] ?? null;
        return $linha ?: null;
    }

    public static function valor(string $sql, array $parametros = []): mixed
    {
        $consulta = self::pdo()->prepare($sql);
        $consulta->execute($parametros);
        return $consulta->fetchColumn();
    }
}
