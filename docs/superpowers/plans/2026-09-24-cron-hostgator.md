# HostGator Automatic Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the complete DOERJ import on HostGator every weekday and publish new records directly to the production MySQL database without human review.

**Architecture:** A testable Python 3.9+ orchestrator runs the existing downloader, extractor, classifier, loader, relation detector, and deadline extractor in order. It owns the exclusive lock, pre-write database backup, structured state files, retention, and process exit status; cPanel Cron only invokes this single entry point with absolute paths.

**Tech Stack:** Python 3.9+, standard library, PyMuPDF, PyMySQL, PHP CLI for reading the existing production configuration, MySQL/MariaDB CLI tools, cPanel Cron, GitHub Actions.

## Global Constraints

- Publish new editions without prior human review; keep inferred fields visibly marked as automatic.
- Process only DOERJ Poder Executivo and use a three-day recovery window in `America/Sao_Paulo`.
- Never put the database password in Git, command-line arguments, crontab, logs, or documentation.
- Keep code and operational data outside the public document root.
- Do not run `git pull` from cron or update application code automatically.
- Acquire a non-blocking exclusive lock before network or database work.
- Back up production before the first database write.
- Preserve the existing uncommitted edits in `tools/doerj_extrair.py` and `tools/vocabulario.py`.
- Use only Python features accepted by HostGator's documented Python 3.9 runtime.
- Do not activate the schedule until a manual production run and an idempotence rerun both pass.

---

### Task 1: Date window and file-selection core

**Files:**
- Create: `tests/test_doerj_cron.py`
- Create: `tools/doerj_cron.py`

**Interfaces:**
- Produces: `janela_padrao(agora: datetime | None = None) -> tuple[date, date]`
- Produces: `pdfs_da_janela(pasta: Path, inicio: date, fim: date) -> list[Path]`
- Produces: `jsonls_dos_pdfs(pdfs: Sequence[Path], pasta: Path) -> list[Path]`

- [ ] **Step 1: Write failing tests for the Brasília date window and deterministic file selection**

```python
from datetime import date, datetime
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf
from zoneinfo import ZoneInfo

from tools.doerj_cron import janela_padrao, jsonls_dos_pdfs, pdfs_da_janela


class JanelaTest(TestCase):
    def test_uses_brasilia_date_and_includes_three_days_back(self):
        agora = datetime(2026, 9, 24, 2, 0, tzinfo=ZoneInfo("UTC"))
        self.assertEqual(
            janela_padrao(agora),
            (date(2026, 9, 20), date(2026, 9, 23)),
        )

    def test_selects_only_executive_pdfs_inside_the_window(self):
        with TemporaryDirectory() as tmp:
            dados = Path(tmp)
            mes = dados / "2026" / "09"
            mes.mkdir(parents=True)
            nomes = [
                "2026-09-21-parte-i-poder-executivo.pdf",
                "2026-09-22-parte-i-poder-executivo.pdf",
                "2026-09-22-parte-i-poder-executivo-2.pdf",
                "2026-09-22-parte-ii-poder-legislativo.pdf",
                "2026-09-18-parte-i-poder-executivo.pdf",
            ]
            for nome in nomes:
                (mes / nome).write_bytes(b"%PDF-1.7")

            encontrados = pdfs_da_janela(
                dados, date(2026, 9, 20), date(2026, 9, 23)
            )
            self.assertEqual(
                [p.name for p in encontrados],
                nomes[:3],
            )
            self.assertEqual(
                [p.name for p in jsonls_dos_pdfs(encontrados, dados / "extraido")],
                [p.stem + ".jsonl" for p in encontrados],
            )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_doerj_cron.JanelaTest -v`

Expected: `ModuleNotFoundError: No module named 'tools.doerj_cron'`.

- [ ] **Step 3: Implement the date and path functions**

```python
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

FUSO_RIO = ZoneInfo("America/Sao_Paulo")


def janela_padrao(agora: datetime | None = None) -> tuple[date, date]:
    instante = agora or datetime.now(tz=FUSO_RIO)
    hoje = instante.astimezone(FUSO_RIO).date()
    return hoje - timedelta(days=3), hoje


def pdfs_da_janela(pasta: Path, inicio: date, fim: date) -> list[Path]:
    encontrados = []
    dia = inicio
    while dia <= fim:
        mes = pasta / f"{dia:%Y}" / f"{dia:%m}"
        encontrados.extend(
            mes.glob(f"{dia:%Y-%m-%d}-parte-i-poder-executivo*.pdf")
        )
        dia += timedelta(days=1)
    return sorted(encontrados)


def jsonls_dos_pdfs(pdfs: Sequence[Path], pasta: Path) -> list[Path]:
    return [pasta / f"{pdf.stem}.jsonl" for pdf in pdfs]
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `python -m unittest tests.test_doerj_cron.JanelaTest -v`

Expected: two tests pass.

- [ ] **Step 5: Commit the core**

```bash
git add tests/test_doerj_cron.py tools/doerj_cron.py
git commit -m "feat: add cron date window core"
```

---

### Task 2: Ordered, incremental import pipeline

**Files:**
- Modify: `tests/test_doerj_cron.py`
- Modify: `tools/doerj_cron.py`

**Interfaces:**
- Consumes: Task 1 date and path functions.
- Produces: `Contexto`, `Resultado`, and `rodar_pipeline(contexto, executar, backup, contagens) -> Resultado`.
- Guarantees: no database mutation when the window contains no PDF; backup occurs immediately before `doerj_carregar.py`.

- [ ] **Step 1: Add failing pipeline-order and no-edition tests**

```python
from tools.doerj_cron import Contexto, rodar_pipeline


def contexto_de_teste(raiz: Path) -> Contexto:
    return Contexto(
        raiz=raiz,
        trabalho=raiz / "trabalho",
        inicio=date(2026, 9, 24),
        fim=date(2026, 9, 24),
        python="python",
        ambiente={},
    )


class PipelineTest(TestCase):
    def test_orders_every_stage_and_backs_up_before_loading(self):
        chamadas = []

        def executar(comando, **kwargs):
            chamadas.append(Path(comando[1]).name)
            if Path(comando[1]).name == "doerj_download.py":
                pdf = contexto.dados / "2026" / "09" / "2026-09-24-parte-i-poder-executivo.pdf"
                pdf.parent.mkdir(parents=True, exist_ok=True)
                pdf.write_bytes(b"%PDF-1.7" + b"x" * 11000)
            if Path(comando[1]).name == "doerj_extrair.py":
                contexto.extraido.mkdir(parents=True, exist_ok=True)
                (contexto.extraido / "2026-09-24-parte-i-poder-executivo.jsonl").write_text(
                    '{"id_ioerj":"1"}\n', encoding="utf-8"
                )

        def backup(_):
            chamadas.append("backup")

        with TemporaryDirectory() as tmp:
            contexto = contexto_de_teste(Path(tmp))
            resultado = rodar_pipeline(
                contexto,
                executar=executar,
                backup=backup,
                contagens=lambda _: {"atos": 1, "edicoes": 1},
            )

        self.assertEqual(
            chamadas,
            [
                "doerj_download.py",
                "doerj_extrair.py",
                "doerj_temas.py",
                "backup",
                "doerj_carregar.py",
                "doerj_relacoes.py",
                "doerj_prazos.py",
            ],
        )
        self.assertEqual(resultado.contagens["atos"], 1)

    def test_no_edition_finishes_without_backup_or_database_write(self):
        chamadas = []
        with TemporaryDirectory() as tmp:
            contexto = contexto_de_teste(Path(tmp))
            resultado = rodar_pipeline(
                contexto,
                executar=lambda comando, **kwargs: chamadas.append(Path(comando[1]).name),
                backup=lambda _: self.fail("backup must not run"),
                contagens=lambda _: self.fail("counts must not run"),
            )
        self.assertEqual(chamadas, ["doerj_download.py"])
        self.assertEqual(resultado.pdfs, 0)
```

- [ ] **Step 2: Run the pipeline tests and verify RED**

Run: `python -m unittest tests.test_doerj_cron.PipelineTest -v`

Expected: import failures for `Contexto`, `Resultado`, and `rodar_pipeline`.

- [ ] **Step 3: Implement the pipeline with explicit command construction**

```python
from dataclasses import dataclass
import os
import subprocess


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


def executar(comando, *, cwd, env):
    print("+", " ".join(str(parte) for parte in comando))
    subprocess.run(comando, cwd=cwd, env=env, check=True)


def rodar_pipeline(contexto, *, executar=executar, backup, contagens):
    ferramentas = contexto.raiz / "tools"
    ambiente = {**os.environ, **contexto.ambiente, "TZ": "America/Sao_Paulo"}
    contexto.dados.mkdir(parents=True, exist_ok=True)
    contexto.extraido.mkdir(parents=True, exist_ok=True)

    executar(
        [
            contexto.python,
            ferramentas / "doerj_download.py",
            "--inicio", contexto.inicio.isoformat(),
            "--fim", contexto.fim.isoformat(),
            "--destino", contexto.dados,
        ],
        cwd=contexto.raiz,
        env=ambiente,
    )
    pdfs = pdfs_da_janela(contexto.dados, contexto.inicio, contexto.fim)
    if not pdfs:
        return Resultado(
            contexto.inicio.isoformat(), contexto.fim.isoformat(), 0, 0, {}
        )

    jsonls = jsonls_dos_pdfs(pdfs, contexto.extraido)
    executar(
        [contexto.python, ferramentas / "doerj_extrair.py", *pdfs,
         "--saida", contexto.extraido],
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
        [contexto.python, ferramentas / "doerj_carregar.py", *jsonls,
         "--pdf", contexto.dados],
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
        contexto.inicio.isoformat(), contexto.fim.isoformat(),
        len(pdfs), len(jsonls), numeros
    )
```

- [ ] **Step 4: Run the pipeline tests and the existing tool self-tests**

Run:

```bash
python -m unittest tests.test_doerj_cron.PipelineTest -v
python tools/doerj_download.py --autoteste
python tools/doerj_extrair.py --autoteste
python tools/doerj_temas.py --autoteste
python tools/doerj_carregar.py --autoteste
python tools/doerj_relacoes.py --autoteste
python tools/doerj_prazos.py --autoteste
```

Expected: all tests exit zero and each existing tool prints `autoteste: tudo certo`.

- [ ] **Step 5: Commit the ordered pipeline**

```bash
git add tests/test_doerj_cron.py tools/doerj_cron.py
git commit -m "feat: orchestrate automatic DOERJ import"
```

---

### Task 3: Secure credentials, backup, state, retention, and locking

**Files:**
- Modify: `tests/test_doerj_cron.py`
- Modify: `tools/doerj_cron.py`

**Interfaces:**
- Produces: `Banco`, `ler_banco(config_php, php) -> Banco`, `arquivo_cnf(banco)`, `fazer_backup(contexto)`, `consultar_contagens(contexto)`, `gravar_estado(path, payload)`, `limpar_antigos(path, dias, agora)` and `trava_exclusiva(path)`.
- Security guarantee: the password appears only in a mode-`0600` temporary option file and child-process environment.

- [ ] **Step 1: Add failing security and recovery tests**

```python
from tools.doerj_cron import (
    Banco,
    ExecucaoEmAndamento,
    arquivo_cnf,
    gravar_estado,
    trava_exclusiva,
)


class OperacaoSeguraTest(TestCase):
    def test_mysql_option_file_quotes_hash_backslash_and_double_quote(self):
        banco = Banco("localhost", 3306, "doerj", "usuario", 'a#b\\c"d')
        with arquivo_cnf(banco) as caminho:
            self.assertEqual(caminho.stat().st_mode & 0o777, 0o600)
            texto = caminho.read_text(encoding="utf-8")
            self.assertIn('password="a#b\\\\c\\"d"', texto)
            self.assertNotIn("password=a#", texto)
        self.assertFalse(caminho.exists())

    def test_state_write_is_atomic_and_failure_does_not_replace_success(self):
        with TemporaryDirectory() as tmp:
            destino = Path(tmp) / "ultimo-sucesso.json"
            gravar_estado(destino, {"estado": "sucesso", "atos": 10})
            self.assertEqual(json.loads(destino.read_text())["atos"], 10)
            with self.assertRaises(TypeError):
                gravar_estado(destino, {"invalido": object()})
            self.assertEqual(json.loads(destino.read_text())["atos"], 10)

    @skipIf(os.name == "nt", "fcntl é validado no runner Linux")
    def test_lock_refuses_a_second_execution(self):
        with TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "cron.lock"
            with trava_exclusiva(caminho):
                with self.assertRaises(ExecucaoEmAndamento):
                    with trava_exclusiva(caminho):
                        pass
```

- [ ] **Step 2: Run the security tests and verify RED**

Run: `python -m unittest tests.test_doerj_cron.OperacaoSeguraTest -v`

Expected: imports fail for the new interfaces.

- [ ] **Step 3: Implement secure configuration and MySQL option files**

```python
from contextlib import contextmanager
import json
import tempfile


@dataclass(frozen=True)
class Banco:
    host: str
    porta: int
    nome: str
    usuario: str
    senha: str


def ler_banco(config_php: Path, php: str = "php") -> Banco:
    codigo = (
        '$c=require $argv[1]; '
        'echo json_encode($c["banco"], JSON_THROW_ON_ERROR);'
    )
    r = subprocess.run(
        [php, "-r", codigo, str(config_php)],
        check=True, capture_output=True, text=True, encoding="utf-8"
    )
    bruto = json.loads(r.stdout)
    campos = ("host", "porta", "nome", "usuario", "senha")
    if any(bruto.get(campo) in (None, "") for campo in campos):
        raise RuntimeError("config.php não contém todos os campos do banco")
    return Banco(
        str(bruto["host"]), int(bruto["porta"]), str(bruto["nome"]),
        str(bruto["usuario"]), str(bruto["senha"])
    )


def _cnf(valor: str) -> str:
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
                f'host="{_cnf(banco.host)}"\n'
                f"port={banco.porta}\n"
                f'user="{_cnf(banco.usuario)}"\n'
                f'password="{_cnf(banco.senha)}"\n'
            )
        yield caminho
    finally:
        caminho.unlink(missing_ok=True)
```

- [ ] **Step 4: Implement backup, counts, state, retention, and a Linux lock**

```python
import gzip
from contextlib import contextmanager


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


def fazer_backup(contexto: Contexto) -> Path:
    banco = ler_banco(contexto.raiz / "config" / "config.php")
    pasta = contexto.trabalho / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"doerj-{datetime.now(FUSO_RIO):%Y%m%d-%H%M%S}.sql.gz"
    with arquivo_cnf(banco) as cnf, gzip.open(destino, "wb") as saida:
        r = subprocess.run(
            ["mysqldump", f"--defaults-extra-file={cnf}", "--no-tablespaces", banco.nome],
            stdout=saida, stderr=subprocess.PIPE
        )
        if r.returncode:
            destino.unlink(missing_ok=True)
            raise RuntimeError(r.stderr.decode("utf-8", errors="replace"))
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
        r = subprocess.run(
            ["mysql", f"--defaults-extra-file={cnf}", "-N", "-B", banco.nome,
             "-e", consulta],
            check=True, capture_output=True, text=True, encoding="utf-8"
        )
    valores = [int(v) for v in r.stdout.strip().split("\t")]
    return dict(zip(("atos", "edicoes", "relacoes", "prazos"), valores))


def gravar_estado(destino: Path, payload: dict) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_text(texto, encoding="utf-8")
    temporario.replace(destino)


def limpar_antigos(pasta: Path, dias: int, agora: datetime) -> None:
    limite = agora.timestamp() - dias * 86400
    for caminho in pasta.rglob("*"):
        if caminho.is_file() and caminho.stat().st_mtime < limite:
            caminho.unlink()
    for caminho in sorted(
        (p for p in pasta.rglob("*") if p.is_dir()), reverse=True
    ):
        if not any(caminho.iterdir()):
            caminho.rmdir()
```

- [ ] **Step 5: Run the security tests on Linux and verify GREEN**

Run: `python -m unittest tests.test_doerj_cron.OperacaoSeguraTest -v`

Expected: all tests pass. On Windows, run this test in GitHub Actions because `fcntl` is Linux-only.

- [ ] **Step 6: Commit the operational safeguards**

```bash
git add tests/test_doerj_cron.py tools/doerj_cron.py
git commit -m "feat: secure automatic import operations"
```

---

### Task 4: CLI, environment proof, logs, and exit semantics

**Files:**
- Modify: `tests/test_doerj_cron.py`
- Modify: `tools/doerj_cron.py`

**Interfaces:**
- Produces CLI flags `--raiz`, `--trabalho`, `--inicio`, `--fim`, `--checar-ambiente`, and `--contar`.
- Produces files `estado/ultimo-sucesso.json`, `estado/ultima-falha.json`, and `logs/YYYY-MM-DD-HHMMSS.log`.
- Returns exit `0` for success or no edition, `75` for an existing lock, and `1` for a failed stage.

- [ ] **Step 1: Add failing CLI tests**

```python
import io
from contextlib import redirect_stdout
from unittest.mock import patch

from tools.doerj_cron import argumentos, checar_ambiente, main


class CliTest(TestCase):
    def test_rejects_end_before_start(self):
        with self.assertRaises(SystemExit) as erro:
            argumentos(["--inicio", "2026-09-24", "--fim", "2026-09-23"])
        self.assertEqual(erro.exception.code, 2)

    def test_environment_check_lists_every_required_program(self):
        resultado = checar_ambiente(
            localizar=lambda nome: "/bin/" + nome,
            importar=lambda nome: None,
        )
        self.assertEqual(resultado, {
            "php": "/bin/php",
            "mysql": "/bin/mysql",
            "mysqldump": "/bin/mysqldump",
            "fitz": "ok",
            "pymysql": "ok",
        })

    @patch("tools.doerj_cron.checar_ambiente")
    def test_main_environment_check_is_read_only(self, checar):
        checar.return_value = {"php": "/bin/php", "mysql": "/bin/mysql"}
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["--checar-ambiente"])
        self.assertEqual(codigo, 0)
        self.assertIn('"php": "/bin/php"', saida.getvalue())
```

- [ ] **Step 2: Run the CLI tests and verify RED**

Run: `python -m unittest tests.test_doerj_cron.CliTest -v`

Expected: imports fail for `argumentos` and `checar_ambiente`.

- [ ] **Step 3: Implement argument parsing and environment checks**

```python
import argparse
import importlib
import shutil
import sys


def checar_ambiente(localizar=shutil.which, importar=importlib.import_module):
    resultado = {}
    for programa in ("php", "mysql", "mysqldump"):
        caminho = localizar(programa)
        if not caminho:
            raise RuntimeError(f"programa obrigatório ausente: {programa}")
        resultado[programa] = caminho
    for modulo in ("fitz", "pymysql"):
        importar(modulo)
        resultado[modulo] = "ok"
    return resultado


def argumentos(argv=None):
    raiz_padrao = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raiz", type=Path, default=raiz_padrao)
    p.add_argument("--trabalho", type=Path, default=Path.home() / "doerj-var")
    p.add_argument("--inicio", type=date.fromisoformat)
    p.add_argument("--fim", type=date.fromisoformat)
    p.add_argument("--checar-ambiente", action="store_true")
    p.add_argument("--contar", action="store_true")
    args = p.parse_args(argv)
    if args.fim and not args.inicio:
        p.error("--fim exige --inicio")
    if args.inicio and args.fim and args.fim < args.inicio:
        p.error("a data final é anterior à inicial")
    return args
```

- [ ] **Step 4: Implement `main()` with lock, state, retention, and sanitized failure output**

```python
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict
import traceback


def _contexto(args, inicio, fim, banco):
    return Contexto(
        raiz=args.raiz.resolve(),
        trabalho=args.trabalho.resolve(),
        inicio=inicio,
        fim=fim,
        python=sys.executable,
        ambiente={
            "DOERJ_HOST": banco.host,
            "DOERJ_PORT": str(banco.porta),
            "DOERJ_USER": banco.usuario,
            "DOERJ_SENHA": banco.senha,
            "DOERJ_BANCO": banco.nome,
        },
    )


def main(argv=None):
    args = argumentos(argv)
    try:
        programas = checar_ambiente()
    except Exception as erro:
        print(f"ambiente inválido: {erro}", file=sys.stderr)
        return 1
    if args.checar_ambiente:
        print(json.dumps(programas, ensure_ascii=False, indent=2))
        return 0

    inicio, fim = (
        (args.inicio, args.fim or args.inicio)
        if args.inicio else janela_padrao()
    )
    try:
        banco = ler_banco(args.raiz / "config" / "config.php", programas["php"])
    except Exception as erro:
        print(f"configuração inválida: {erro}", file=sys.stderr)
        return 1
    contexto = _contexto(args, inicio, fim, banco)
    if args.contar:
        print(json.dumps(consultar_contagens(contexto), indent=2))
        return 0

    agora = datetime.now(FUSO_RIO)
    logs = contexto.trabalho / "logs"
    estado = contexto.trabalho / "estado"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{agora:%Y-%m-%d-%H%M%S}.log"
    try:
        with log.open("w", encoding="utf-8") as registro:
            with redirect_stdout(registro), redirect_stderr(registro):
                with trava_exclusiva(contexto.trabalho / "cron.lock"):
                    resultado = rodar_pipeline(
                        contexto,
                        backup=fazer_backup,
                        contagens=consultar_contagens,
                    )
                    payload = {
                        "estado": "sucesso",
                        "executado_em": datetime.now(FUSO_RIO).isoformat(),
                        **asdict(resultado),
                    }
                    gravar_estado(estado / "ultimo-sucesso.json", payload)
                    limpar_antigos(contexto.trabalho / "backups", 14, agora)
                    limpar_antigos(logs, 30, agora)
                    limpar_antigos(contexto.dados, 14, agora)
                    limpar_antigos(contexto.extraido, 14, agora)
    except ExecucaoEmAndamento as erro:
        print(str(erro), file=sys.stderr)
        return 75
    except Exception as erro:
        with log.open("a", encoding="utf-8") as registro:
            traceback.print_exc(file=registro)
        gravar_estado(estado / "ultima-falha.json", {
            "estado": "falha",
            "executado_em": datetime.now(FUSO_RIO).isoformat(),
            "tipo": type(erro).__name__,
            "mensagem": str(erro),
            "log": str(log),
        })
        print(f"importação falhou; consulte {log}", file=sys.stderr)
        return 1
    print(
        f"importação concluída: {resultado.pdfs} PDF(s), "
        f"{resultado.contagens.get('atos', 0)} ato(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the complete orchestrator test module**

Run: `python -m unittest tests.test_doerj_cron -v`

Expected: all Task 1–4 tests pass on Linux.

- [ ] **Step 6: Commit the production CLI**

```bash
git add tests/test_doerj_cron.py tools/doerj_cron.py
git commit -m "feat: expose production cron command"
```

---

### Task 5: Add a repeatable quality gate

**Files:**
- Create: `.github/workflows/quality.yml`
- Modify: `README.md`

**Interfaces:**
- Runs all Python self-tests, the new unit suite, PHP text tests, contrast checks, generated SQL consistency, and the real MySQL schema proof.

- [ ] **Step 1: Create the failing GitHub Actions quality workflow**

```yaml
name: Qualidade

on:
  push:
  pull_request:
  workflow_dispatch:

jobs:
  testar:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.4
        env:
          MYSQL_ALLOW_EMPTY_PASSWORD: "yes"
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.9"
          cache: pip
      - run: pip install -r requirements.txt
      - name: Testes unitários do cron
        run: python -m unittest discover -s tests -v
      - name: Autotestes Python
        run: |
          python tools/doerj_download.py --autoteste
          python tools/doerj_extrair.py --autoteste
          python tools/doerj_temas.py --autoteste
          python tools/doerj_carregar.py --autoteste
          python tools/doerj_relacoes.py --autoteste
          python tools/doerj_prazos.py --autoteste
          python tools/lgpd.py
          python tools/vocabulario.py
          python tools/contraste.py
      - name: Texto PHP
        run: php app/provar_texto.php
      - name: Esquema MySQL real
        env:
          DOERJ_HOST: 127.0.0.1
          DOERJ_PORT: 3306
          DOERJ_USER: root
          DOERJ_SENHA: ""
          DOERJ_BANCO: doerj_teste
        run: python backend/db/provar_esquema.py
      - name: Instalador SQL reproduzível
        run: |
          cp backend/db/instalar.sql /tmp/instalar.sql
          python tools/gerar_instalador.py
          cmp /tmp/instalar.sql backend/db/instalar.sql
```

- [ ] **Step 2: Run the same quality gate locally and capture any genuine failure**

Run the Python and PHP commands from the workflow. Run `python backend/db/provar_esquema.py` only against the documented disposable `doerj_teste` database.

Expected: any current failure is recorded before it is fixed; tests are never disabled or weakened.

- [ ] **Step 3: Document the single local quality command group in README**

Add the exact commands from the workflow under `## Qualidade`, including the warning that `provar_esquema.py` destroys and recreates only the database named by `DOERJ_BANCO`.

- [ ] **Step 4: Run the full quality gate again and verify GREEN**

Expected: every command exits zero and the generated installer matches the committed file byte-for-byte.

- [ ] **Step 5: Commit the quality gate**

```bash
git add .github/workflows/quality.yml README.md
git commit -m "ci: prove automatic import pipeline"
```

---

### Task 6: Prove HostGator capacity and deploy without enabling cron

**Files:**
- Server create: `/home1/fanara87/doerj/tools/doerj_cron.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_download.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_extrair.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_temas.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_carregar.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_relacoes.py`
- Server create: `/home1/fanara87/doerj/tools/doerj_prazos.py`
- Server create: `/home1/fanara87/doerj/tools/lgpd.py`
- Server create: `/home1/fanara87/doerj/tools/vocabulario.py`
- Server create: `/home1/fanara87/doerj-var/venv/`

**Interfaces:**
- Consumes the committed tools and existing `/home1/fanara87/doerj/config/config.php`.
- Produces a private runtime directory and a successful read-only environment report.

- [ ] **Step 1: Inspect the server without mutation**

Run in cPanel Terminal or SSH:

```bash
date '+%Y-%m-%d %H:%M:%S %z'
python3 --version
command -v python3 php mysql mysqldump
crontab -l
df -h /home1/fanara87
du -sh /home1/fanara87/doerj /home1/fanara87/doerj-var 2>/dev/null || true
```

Gate: stop this plan before deployment if Python is older than 3.9, any required executable is absent, or available storage is below 1 GB. In that case, write a separate GitHub Actions + SSH plan from the approved fallback design.

- [ ] **Step 2: Create the private runtime and virtual environment**

```bash
mkdir -p /home1/fanara87/doerj/tools
mkdir -p /home1/fanara87/doerj-var/{dados,extraido,backups,logs,estado}
chmod 700 /home1/fanara87/doerj-var
python3 -m venv /home1/fanara87/doerj-var/venv
/home1/fanara87/doerj-var/venv/bin/python -m pip install --upgrade pip
/home1/fanara87/doerj-var/venv/bin/python -m pip install 'pymupdf>=1.24' 'pymysql>=1.1'
```

- [ ] **Step 3: Upload only the required committed tools**

Run from the clean implementation worktree:

```bash
scp tools/doerj_cron.py tools/doerj_download.py tools/doerj_extrair.py \
  tools/doerj_temas.py tools/doerj_carregar.py tools/doerj_relacoes.py \
  tools/doerj_prazos.py tools/lgpd.py tools/vocabulario.py \
  hostgator-fanara:/home1/fanara87/doerj/tools/
```

Do not upload `config/config.php`, `dados/`, `extraido/`, local `.env`, or either locally modified uncommitted script version unless those changes have separately passed review and tests.

- [ ] **Step 4: Verify permissions and environment**

```bash
chmod 700 /home1/fanara87/doerj/tools/doerj_cron.py
chmod 600 /home1/fanara87/doerj/config/config.php
/home1/fanara87/doerj-var/venv/bin/python \
  /home1/fanara87/doerj/tools/doerj_cron.py \
  --raiz /home1/fanara87/doerj \
  --trabalho /home1/fanara87/doerj-var \
  --checar-ambiente
```

Expected: the command reports Python, `fitz`, `pymysql`, PHP, MySQL, and mysqldump, and exits zero without touching the database.

---

### Task 7: Manual production run, idempotence proof, and rollback proof

**Files:**
- Server output: `/home1/fanara87/doerj-var/backups/*.sql.gz`
- Server output: `/home1/fanara87/doerj-var/logs/*.log`
- Server output: `/home1/fanara87/doerj-var/estado/ultimo-sucesso.json`

**Interfaces:**
- Produces a verified production import and a confirmed recovery artifact.

- [ ] **Step 1: Record pre-run production counts**

```bash
/home1/fanara87/doerj-var/venv/bin/python \
  /home1/fanara87/doerj/tools/doerj_cron.py \
  --raiz /home1/fanara87/doerj \
  --trabalho /home1/fanara87/doerj-var \
  --contar
```

Expected: JSON with `atos`, `edicoes`, `relacoes`, and `prazos`, without a password or connection string.

- [ ] **Step 2: Run one explicit one-day import manually**

```bash
/home1/fanara87/doerj-var/venv/bin/python \
  /home1/fanara87/doerj/tools/doerj_cron.py \
  --raiz /home1/fanara87/doerj \
  --trabalho /home1/fanara87/doerj-var \
  --inicio 2026-09-24 \
  --fim 2026-09-24
```

Expected: a backup is created before loading; each stage exits zero; `ultimo-sucesso.json` records the date range and final counts.

- [ ] **Step 3: Verify the public result**

Open `https://doerj.fanara.com.br`, search for an `id_ioerj` from the imported JSONL, and confirm that the public page points to the correct edition and retains the automatic/inferred markers.

- [ ] **Step 4: Run the same command a second time**

Expected: final table counts are identical to the first run, no duplicate `id_ioerj` exists, and a second valid backup is present.

- [ ] **Step 5: Prove the backup is readable without restoring over production**

```bash
gzip -t "$(ls -1t /home1/fanara87/doerj-var/backups/*.sql.gz | head -1)"
gunzip -c "$(ls -1t /home1/fanara87/doerj-var/backups/*.sql.gz | head -1)" | head -20
```

Expected: `gzip -t` exits zero and the first lines are a MySQL dump header. Do not perform a destructive restore during this proof.

---

### Task 8: Activate and observe the cPanel cron

**Files:**
- External configuration: cPanel `Cron Jobs`
- Modify: `docs/publicacao.md`
- Modify: `REQUIREMENTS.md`
- Modify: `ARCHITECTURE.md`
- Modify: `STEPS.md`

**Interfaces:**
- Produces one enabled weekday schedule and operational documentation.

- [ ] **Step 1: Determine the cPanel cron timezone**

Compare the cPanel current time with `date '+%Y-%m-%d %H:%M:%S %z'`. Use 09:15 if it is `-0300`; use 12:15 if it is `+0000`. For any other offset, add three hours to 09:15 for every hour the server is east of Brasília.

- [ ] **Step 2: Add exactly one cron job in cPanel**

Schedule fields for a Brasília-time server:

```text
minute: 15
hour: 9
day: *
month: *
weekday: 1-5
```

Command:

```bash
TZ=America/Sao_Paulo /home1/fanara87/doerj-var/venv/bin/python /home1/fanara87/doerj/tools/doerj_cron.py --raiz /home1/fanara87/doerj --trabalho /home1/fanara87/doerj-var >> /home1/fanara87/doerj-var/logs/cron.log 2>&1
```

For a UTC server, change only the hour field from `9` to `12`.

- [ ] **Step 3: Confirm cPanel shows the saved job and no duplicate exists**

Expected: one row contains the exact command and weekday schedule. If a duplicate exists, stop and ask before deleting because cron deletion is destructive external state.

- [ ] **Step 4: Observe the first scheduler-triggered run**

After the scheduled time, verify that `ultimo-sucesso.json` has a newer timestamp than the manual run, `cron.log` contains the same execution window, and the portal exposes an act from the new edition.

- [ ] **Step 5: Update living documentation to implemented state**

Document the final timezone, exact schedule, runtime paths, backup retention, log retention, manual command, disable procedure, and non-destructive backup verification. Mark RF-34, RNF-13, and Phase 9 implemented only after Step 4 passes.

- [ ] **Step 6: Run the final quality gate and inspect the diff**

Run all Task 5 commands, then:

```bash
git diff --check
git status --short
git diff -- REQUIREMENTS.md ARCHITECTURE.md STEPS.md docs/publicacao.md
```

Expected: tests pass, `git diff --check` reports no errors, and unrelated user changes remain unstaged.

- [ ] **Step 7: Commit the verified operational state**

```bash
git add REQUIREMENTS.md ARCHITECTURE.md STEPS.md docs/publicacao.md
git commit -m "docs: record automatic production import"
```
