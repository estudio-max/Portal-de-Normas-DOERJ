from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zoneinfo import ZoneInfo

from tools.doerj_cron import janela_padrao, jsonls_dos_pdfs, pdfs_da_janela


class JanelaTest(TestCase):
    def test_usa_data_do_rio_e_inclui_tres_dias_anteriores(self):
        agora = datetime(2026, 9, 24, 2, 0, tzinfo=ZoneInfo("UTC"))

        self.assertEqual(
            janela_padrao(agora),
            (date(2026, 9, 20), date(2026, 9, 23)),
        )

    def test_seleciona_so_pdfs_do_executivo_dentro_da_janela(self):
        with TemporaryDirectory() as tmp:
            dados = Path(tmp)
            mes = dados / "2026" / "09"
            mes.mkdir(parents=True)
            esperados = [
                "2026-09-21-parte-i-poder-executivo.pdf",
                "2026-09-22-parte-i-poder-executivo.pdf",
                "2026-09-22-parte-i-poder-executivo-2.pdf",
            ]
            ignorados = [
                "2026-09-22-parte-ii-poder-legislativo.pdf",
                "2026-09-18-parte-i-poder-executivo.pdf",
            ]
            for nome in esperados + ignorados:
                (mes / nome).write_bytes(b"%PDF-1.7")

            encontrados = pdfs_da_janela(
                dados, date(2026, 9, 20), date(2026, 9, 23)
            )

            self.assertEqual([p.name for p in encontrados], esperados)
            self.assertEqual(
                [p.name for p in jsonls_dos_pdfs(encontrados, dados / "extraido")],
                [Path(nome).stem + ".jsonl" for nome in esperados],
            )
