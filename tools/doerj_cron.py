"""Orquestra a importação automática do DOERJ na hospedagem.

O cron chama somente este arquivo. As etapas especializadas continuam nos
scripts próprios em ``tools/``.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Sequence
from zoneinfo import ZoneInfo

FUSO_RIO = ZoneInfo("America/Sao_Paulo")


def janela_padrao(agora: datetime | None = None) -> tuple[date, date]:
    instante = agora or datetime.now(tz=FUSO_RIO)
    hoje = instante.astimezone(FUSO_RIO).date()
    return hoje - timedelta(days=3), hoje


def pdfs_da_janela(pasta: Path, inicio: date, fim: date) -> list[Path]:
    encontrados: list[Path] = []
    dia = inicio
    while dia <= fim:
        mes = pasta / f"{dia:%Y}" / f"{dia:%m}"
        encontrados.extend(
            mes.glob(f"{dia:%Y-%m-%d}-parte-i-poder-executivo*.pdf")
        )
        dia += timedelta(days=1)
    def ordem(caminho: Path) -> tuple[str, int]:
        extra = re.search(r"-(\d+)$", caminho.stem)
        base = caminho.stem[: extra.start()] if extra else caminho.stem
        return base, int(extra.group(1)) if extra else 1

    return sorted(encontrados, key=ordem)


def jsonls_dos_pdfs(pdfs: Sequence[Path], pasta: Path) -> list[Path]:
    return [pasta / f"{pdf.stem}.jsonl" for pdf in pdfs]


@dataclass(frozen=True)
class Contexto:
    raiz: Path
    trabalho: Path
    inicio: date
    fim: date
    python: str
    ambiente: dict[str, str]

    @property
    def dados(self) -> Path:
        return self.trabalho / "dados"

    @property
    def extraido(self) -> Path:
        return self.trabalho / "extraido"


@dataclass(frozen=True)
class Resultado:
    inicio: str
    fim: str
    pdfs: int
    jsonls: int
    contagens: dict[str, int]


@dataclass(frozen=True)
class Banco:
    host: str
    porta: int
    nome: str
    usuario: str
    senha: str


def _valor_cnf(valor: str) -> str:
    if "\n" in valor or "\r" in valor or "\0" in valor:
        raise ValueError("valor inválido para arquivo MySQL")
    return valor.replace("\\", "\\\\").replace('"', '\\"')


@contextmanager
def arquivo_cnf(banco: Banco):
    descritor, nome = tempfile.mkstemp(prefix="doerj-", suffix=".cnf")
    caminho = Path(nome)
    try:
        os.chmod(caminho, 0o600)
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            arquivo.write(
                "[client]\n"
                f'host="{_valor_cnf(banco.host)}"\n'
                f"port={banco.porta}\n"
                f'user="{_valor_cnf(banco.usuario)}"\n'
                f'password="{_valor_cnf(banco.senha)}"\n'
            )
        yield caminho
    finally:
        caminho.unlink(missing_ok=True)


class ExecucaoEmAndamento(RuntimeError):
    pass


@contextmanager
def trava_exclusiva(caminho: Path):
    import fcntl

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a+", encoding="utf-8") as arquivo:
        try:
            fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as erro:
            raise ExecucaoEmAndamento("outra importação já está rodando") from erro
        yield


def gravar_estado(destino: Path, payload: dict) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_text(texto, encoding="utf-8")
    temporario.replace(destino)


def ler_banco(config_php: Path, php: str = "php") -> Banco:
    codigo = (
        '$c=require $argv[1]; '
        'echo json_encode($c["banco"], JSON_THROW_ON_ERROR);'
    )
    resultado = subprocess.run(
        [php, "-r", codigo, str(config_php)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    bruto = json.loads(resultado.stdout)
    campos = ("host", "porta", "nome", "usuario", "senha")
    if any(bruto.get(campo) in (None, "") for campo in campos):
        raise RuntimeError("config.php não contém todos os campos do banco")
    return Banco(
        str(bruto["host"]),
        int(bruto["porta"]),
        str(bruto["nome"]),
        str(bruto["usuario"]),
        str(bruto["senha"]),
    )


def fazer_backup(contexto: Contexto) -> Path:
    banco = ler_banco(contexto.raiz / "config" / "config.php")
    pasta = contexto.trabalho / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"doerj-{datetime.now(FUSO_RIO):%Y%m%d-%H%M%S}.sql.gz"
    with arquivo_cnf(banco) as cnf, gzip.open(destino, "wb") as saida:
        resultado = subprocess.run(
            [
                "mysqldump",
                f"--defaults-extra-file={cnf}",
                "--no-tablespaces",
                banco.nome,
            ],
            stdout=saida,
            stderr=subprocess.PIPE,
        )
        if resultado.returncode:
            destino.unlink(missing_ok=True)
            raise RuntimeError(
                resultado.stderr.decode("utf-8", errors="replace").strip()
            )
    return destino


def consultar_contagens(contexto: Contexto) -> dict[str, int]:
    banco = ler_banco(contexto.raiz / "config" / "config.php")
    consulta = (
        "SELECT (SELECT COUNT(*) FROM atos),"
        "(SELECT COUNT(*) FROM edicoes),"
        "(SELECT COUNT(*) FROM ato_relacoes),"
        "(SELECT COUNT(*) FROM ato_prazo)"
    )
    with arquivo_cnf(banco) as cnf:
        resultado = subprocess.run(
            [
                "mysql",
                f"--defaults-extra-file={cnf}",
                "-N",
                "-B",
                banco.nome,
                "-e",
                consulta,
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    valores = [int(valor) for valor in resultado.stdout.strip().split("\t")]
    if len(valores) != 4:
        raise RuntimeError("o MySQL não devolveu as quatro contagens esperadas")
    return dict(zip(("atos", "edicoes", "relacoes", "prazos"), valores))


def limpar_antigos(pasta: Path, dias: int, agora: datetime) -> None:
    limite = agora.timestamp() - dias * 86400
    for caminho in pasta.rglob("*"):
        if caminho.is_file() and caminho.stat().st_mtime < limite:
            caminho.unlink()
    diretorios = (caminho for caminho in pasta.rglob("*") if caminho.is_dir())
    for caminho in sorted(diretorios, reverse=True):
        if not any(caminho.iterdir()):
            caminho.rmdir()


def executar(comando, *, cwd: Path, env: dict[str, str]) -> None:
    print("+", " ".join(str(parte) for parte in comando))
    subprocess.run(comando, cwd=cwd, env=env, check=True)


def rodar_pipeline(
    contexto: Contexto,
    *,
    executar=executar,
    backup,
    contagens,
) -> Resultado:
    ferramentas = contexto.raiz / "tools"
    ambiente = {**os.environ, **contexto.ambiente, "TZ": "America/Sao_Paulo"}
    contexto.dados.mkdir(parents=True, exist_ok=True)
    contexto.extraido.mkdir(parents=True, exist_ok=True)

    executar(
        [
            contexto.python,
            ferramentas / "doerj_download.py",
            "--inicio",
            contexto.inicio.isoformat(),
            "--fim",
            contexto.fim.isoformat(),
            "--destino",
            contexto.dados,
        ],
        cwd=contexto.raiz,
        env=ambiente,
    )
    pdfs = pdfs_da_janela(contexto.dados, contexto.inicio, contexto.fim)
    if not pdfs:
        return Resultado(
            contexto.inicio.isoformat(),
            contexto.fim.isoformat(),
            0,
            0,
            {},
        )

    jsonls = jsonls_dos_pdfs(pdfs, contexto.extraido)
    executar(
        [
            contexto.python,
            ferramentas / "doerj_extrair.py",
            *pdfs,
            "--saida",
            contexto.extraido,
        ],
        cwd=contexto.raiz,
        env=ambiente,
    )
    executar(
        [contexto.python, ferramentas / "doerj_temas.py", *jsonls],
        cwd=contexto.raiz,
        env=ambiente,
    )
    backup(contexto)
    executar(
        [
            contexto.python,
            ferramentas / "doerj_carregar.py",
            *jsonls,
            "--pdf",
            contexto.dados,
        ],
        cwd=contexto.raiz,
        env=ambiente,
    )
    for nome in ("doerj_relacoes.py", "doerj_prazos.py"):
        executar(
            [contexto.python, ferramentas / nome],
            cwd=contexto.raiz,
            env=ambiente,
        )
    numeros = contagens(contexto)
    return Resultado(
        contexto.inicio.isoformat(),
        contexto.fim.isoformat(),
        len(pdfs),
        len(jsonls),
        numeros,
    )
