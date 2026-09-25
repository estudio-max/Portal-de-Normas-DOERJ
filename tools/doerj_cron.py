"""Orquestra a importação automática do DOERJ na hospedagem.

O cron chama somente este arquivo. As etapas especializadas continuam nos
scripts próprios em ``tools/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import re
import subprocess
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
