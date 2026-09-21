import contextlib
import io
import unittest
from unittest import mock

import _paths

from sensor_monitor.cli import main

EXAMPLE = str(_paths.ROOT / "examples" / "exemplo_briefing.csv")


def run_cli(*argv, stdin=None):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        if stdin is None:
            code = main(list(argv))
        else:
            with mock.patch("sys.stdin", io.StringIO(stdin)):
                code = main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


class CliTests(unittest.TestCase):
    def test_simulator_is_used_without_input(self):
        code, out, _ = run_cli("--threshold", "10")

        self.assertEqual(code, 0)
        self.assertIn("Medições válidas: 19", out)
        self.assertIn("Medições inválidas: 1", out)
        self.assertIn("Valor mínimo: 68.00", out)
        self.assertIn("Valor máximo: 101.50", out)
        self.assertIn("Valor médio: 72.77", out)
        self.assertIn("Mudanças bruscas: 2", out)
        self.assertIn("10:50 -> 10:55: diferença absoluta 30.30", out)

    def test_reads_csv_file(self):
        code, out, _ = run_cli("--threshold", "5", "--input", EXAMPLE)

        self.assertEqual(code, 0)
        self.assertIn("Medições válidas: 4", out)
        self.assertIn("Valor médio: 14.25", out)
        self.assertIn("10:05 -> 10:15: diferença absoluta 6.50", out)

    def test_reads_standard_input(self):
        code, out, _ = run_cli("--threshold", "1", "--input", "-", stdin="10:00,1\n10:05,\n10:10,5\n")

        self.assertEqual(code, 0)
        self.assertIn("Medições inválidas: 1", out)
        self.assertIn("Mudanças bruscas: 1", out)

    def test_no_valid_measurements_reports_no_data(self):
        code, out, _ = run_cli("--threshold", "1", "--input", "-", stdin="10:00,\n")

        self.assertEqual(code, 0)
        self.assertIn("Valor médio: sem dados", out)

    def test_errors_return_status_2_with_message(self):
        cases = {
            "negative threshold": (("--threshold", "-1"), None),
            "nan threshold": (("--threshold", "nan"), None),
            "missing file": (("--threshold", "1", "--input", "nao_existe.csv"), None),
            "malformed csv": (("--threshold", "1", "--input", "-"), "10:00,1,2\n"),
        }
        for name, (argv, stdin) in cases.items():
            with self.subTest(name):
                code, out, err = run_cli(*argv, stdin=stdin)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("Erro:"))


if __name__ == "__main__":
    unittest.main()
