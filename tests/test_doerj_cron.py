from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tools.doerj_cron import (
    Banco,
    Contexto,
    ExecucaoEmAndamento,
    arquivo_cnf,
    consultar_contagens,
    fazer_backup,
    gravar_estado,
    janela_padrao,
    jsonls_dos_pdfs,
    ler_banco,
    limpar_antigos,
    pdfs_da_janela,
    rodar_pipeline,
    trava_exclusiva,
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


class OperacaoSeguraTest(TestCase):
    def test_arquivo_mysql_cita_hash_barra_e_aspas(self):
        banco = Banco("localhost", 3306, "doerj", "usuario", 'a#b\\c"d')

        with arquivo_cnf(banco) as caminho:
            if os.name != "nt":
                self.assertEqual(caminho.stat().st_mode & 0o777, 0o600)
            texto = caminho.read_text(encoding="utf-8")
            self.assertIn('password="a#b\\\\c\\"d"', texto)
            self.assertNotIn("password=a#", texto)

        self.assertFalse(caminho.exists())

    def test_estado_atomico_preserva_sucesso_se_serializacao_falhar(self):
        with TemporaryDirectory() as tmp:
            destino = Path(tmp) / "ultimo-sucesso.json"
            gravar_estado(destino, {"estado": "sucesso", "atos": 10})
            self.assertEqual(json.loads(destino.read_text())["atos"], 10)

            with self.assertRaises(TypeError):
                gravar_estado(destino, {"invalido": object()})

            self.assertEqual(json.loads(destino.read_text())["atos"], 10)

    @patch("tools.doerj_cron.subprocess.run")
    def test_le_config_php_por_json_sem_senha_na_linha_de_comando(self, rodar):
        rodar.return_value.stdout = (
            '{"host":"localhost","porta":3306,"nome":"doerj",'
            '"usuario":"portal","senha":"segredo#1"}'
        )

        banco = ler_banco(Path("config.php"), php="php")

        self.assertEqual(banco.senha, "segredo#1")
        comando = rodar.call_args.args[0]
        self.assertNotIn("segredo#1", comando)
        self.assertEqual(comando[-1], "config.php")

    @patch("tools.doerj_cron.ler_banco")
    @patch("tools.doerj_cron.subprocess.run")
    def test_backup_usa_cnf_temporario_sem_senha_no_comando(self, rodar, ler):
        ler.return_value = Banco("localhost", 3306, "doerj", "portal", "segredo#1")
        rodar.return_value.returncode = 0
        rodar.return_value.stderr = b""
        with TemporaryDirectory() as tmp:
            contexto = contexto_de_teste(Path(tmp))

            destino = fazer_backup(contexto)

            self.assertTrue(destino.exists())
            comando = rodar.call_args.args[0]
            self.assertNotIn("segredo#1", comando)
            self.assertTrue(
                any(str(parte).startswith("--defaults-extra-file=") for parte in comando)
            )

    @patch("tools.doerj_cron.ler_banco")
    @patch("tools.doerj_cron.subprocess.run")
    def test_converte_contagens_mysql_em_campos_nomeados(self, rodar, ler):
        ler.return_value = Banco("localhost", 3306, "doerj", "portal", "segredo#1")
        rodar.return_value.stdout = "12\t3\t4\t5\n"
        with TemporaryDirectory() as tmp:
            contexto = contexto_de_teste(Path(tmp))

            contagens = consultar_contagens(contexto)

        self.assertEqual(
            contagens,
            {"atos": 12, "edicoes": 3, "relacoes": 4, "prazos": 5},
        )

    def test_remove_so_arquivos_antigos_em_subpastas(self):
        agora = datetime(2026, 9, 24, 12, tzinfo=ZoneInfo("UTC"))
        with TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            antiga = pasta / "2026" / "08" / "antiga.pdf"
            nova = pasta / "2026" / "09" / "nova.pdf"
            antiga.parent.mkdir(parents=True)
            nova.parent.mkdir(parents=True)
            antiga.write_bytes(b"antiga")
            nova.write_bytes(b"nova")
            instante_antigo = (agora - timedelta(days=20)).timestamp()
            os.utime(antiga, (instante_antigo, instante_antigo))

            limpar_antigos(pasta, 14, agora)

            self.assertFalse(antiga.exists())
            self.assertTrue(nova.exists())

    @skipIf(os.name == "nt", "fcntl é validado no runner Linux")
    def test_trava_recusa_segunda_execucao(self):
        with TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "cron.lock"
            with trava_exclusiva(caminho):
                with self.assertRaises(ExecucaoEmAndamento):
                    with trava_exclusiva(caminho):
                        pass
