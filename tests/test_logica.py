"""Logic that runs without a database: SUNAT parsing and the Twitter switch."""
import os
import subprocess
import sys
import types
import unittest
from unittest import mock

from PyQt5.QtWidgets import QTableWidget

from _app import ROOT, load_presentacion

presentacion = load_presentacion()


class TipoDeCambioTest(unittest.TestCase):
    """iniciarVenta on the saved SUNAT page (sunat.txt) instead of the live site."""

    def iniciar_venta(self):
        ventana = types.SimpleNamespace(ventas=types.SimpleNamespace(
            tipoDeCambio=QTableWidget()))
        with open(os.path.join(ROOT, "sunat.txt"), "rb") as pagina, \
                mock.patch.object(presentacion.urllib.request, "urlopen",
                                  return_value=pagina) as urlopen:
            presentacion.MainWindow.iniciarVenta(ventana)
        urlopen.assert_called_once()
        return ventana.ventas.tipoDeCambio

    def columna(self, tabla, j):
        return [tabla.item(k, j).text() for k in range(3)]

    def test_shows_the_last_three_days_newest_first(self):
        tabla = self.iniciar_venta()
        self.assertEqual(tabla.rowCount(), 3)
        self.assertEqual(tabla.columnCount(), 3)
        self.assertEqual(self.columna(tabla, 0), ["23", "3.320", "3.324"])
        self.assertEqual(self.columna(tabla, 1), ["22", "3.319", "3.323"])
        self.assertEqual(self.columna(tabla, 2), ["21", "3.307", "3.311"])
        self.assertEqual(tabla.verticalHeaderItem(1).text(), "Compra")

    def test_refreshing_again_keeps_three_columns(self):
        ventana = types.SimpleNamespace(ventas=types.SimpleNamespace(
            tipoDeCambio=QTableWidget()))
        for _ in range(2):
            with open(os.path.join(ROOT, "sunat.txt"), "rb") as pagina, \
                    mock.patch.object(presentacion.urllib.request, "urlopen",
                                      return_value=pagina):
                presentacion.MainWindow.iniciarVenta(ventana)
        self.assertEqual(ventana.ventas.tipoDeCambio.columnCount(), 3)

    def test_urllib_request_is_imported_by_the_module(self):
        # In a fresh interpreter: `import urllib` alone does not load urllib.request.
        codigo = ("import sys; sys.path.insert(0, 'tests'); "
                  "from _app import load_presentacion; "
                  "print(load_presentacion().urllib.request.urlopen.__name__)")
        salida = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(salida.returncode, 0, salida.stderr)
        self.assertEqual(salida.stdout.strip(), "urlopen")


class TwitterSwitchTest(unittest.TestCase):
    def test_off_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BDERP_TWITTER_ENABLED", None)
            self.assertFalse(presentacion.twitterActivado())

    def test_on_only_with_1(self):
        for valor, esperado in (("1", True), ("0", False), ("yes", False)):
            with self.subTest(valor=valor), \
                    mock.patch.dict(os.environ, {"BDERP_TWITTER_ENABLED": valor}):
                self.assertEqual(presentacion.twitterActivado(), esperado)

    def test_refresh_does_nothing_when_off(self):
        ventana = types.SimpleNamespace(iBolsa=None)
        self.assertIsNone(presentacion.MainWindow.iniciarBV(ventana))


class UltimoIdTest(unittest.TestCase):
    def test_rejects_an_unknown_table_before_touching_the_database(self):
        cur = mock.Mock()
        ventana = types.SimpleNamespace(cur=cur)
        with self.assertRaises(ValueError):
            presentacion.MainWindow.ultimoID(ventana, "ventas; drop table ventas")
        cur.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
