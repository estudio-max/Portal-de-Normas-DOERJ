"""Orquestra a importação automática do DOERJ na hospedagem.

O cron chama somente este arquivo. As etapas especializadas continuam nos
scripts próprios em ``tools/``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import re
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
