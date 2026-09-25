from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from zoneinfo import ZoneInfo

from tools.doerj_cron import (
    Contexto,
    janela_padrao,
    jsonls_dos_pdfs,
    pdfs_da_janela,
    rodar_pipeline,
)


def contexto_de_teste(raiz: Path) -> Contexto:
    return Contexto(
        raiz=raiz,
        trabalho=raiz / "trabalho",
        inicio=date(2026, 9, 24),
        fim=date(2026, 9, 24),
        python="python",
        ambiente={},
    )


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


class PipelineTest(TestCase):
    def test_ordena_etapas_e_faz_backup_antes_da_carga(self):
        chamadas = []

        def executar(comando, **_):
            nome = Path(comando[1]).name
            chamadas.append(nome)
            if nome == "doerj_download.py":
                pdf = (
                    contexto.dados
                    / "2026"
                    / "09"
                    / "2026-09-24-parte-i-poder-executivo.pdf"
                )
                pdf.parent.mkdir(parents=True, exist_ok=True)
                pdf.write_bytes(b"%PDF-1.7" + b"x" * 11000)
            if nome == "doerj_extrair.py":
                contexto.extraido.mkdir(parents=True, exist_ok=True)
                (
                    contexto.extraido
                    / "2026-09-24-parte-i-poder-executivo.jsonl"
                ).write_text('{"id_ioerj":"1"}\n', encoding="utf-8")

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

    def test_sem_edicao_termina_sem_backup_ou_escrita_no_banco(self):
        chamadas = []
        with TemporaryDirectory() as tmp:
            contexto = contexto_de_teste(Path(tmp))
            resultado = rodar_pipeline(
                contexto,
                executar=lambda comando, **_: chamadas.append(Path(comando[1]).name),
                backup=lambda _: self.fail("backup não deve rodar"),
                contagens=lambda _: self.fail("contagem não deve rodar"),
            )

        self.assertEqual(chamadas, ["doerj_download.py"])
        self.assertEqual(resultado.pdfs, 0)
