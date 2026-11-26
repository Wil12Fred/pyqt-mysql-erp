"""Smoke tests that need neither a MySQL server nor Twitter credentials.

They check that every Qt Designer form still loads with the pinned PyQt5 and
that the application modules import. Run with QT_QPA_PLATFORM=offscreen on a
headless machine.
"""
import glob
import importlib.machinery
import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt5 import uic  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])


class SmokeTest(unittest.TestCase):
    def test_every_ui_file_loads(self):
        files = sorted(glob.glob(os.path.join(ROOT, "*.ui")))
        self.assertGreater(len(files), 0)
        for path in files:
            with self.subTest(ui=os.path.basename(path)):
                form_class, base_class = uic.loadUiType(path)
                widget = base_class()
                form_class().setupUi(widget)

    def test_twitter_client_builds_without_credentials(self):
        import infoBolsa
        self.assertIsNotNone(infoBolsa.infBolsa().api)

    def test_main_module_imports(self):
        loader = importlib.machinery.SourceFileLoader(
            "presentacion", os.path.join(ROOT, "presentacion.pyw"))
        spec = importlib.util.spec_from_loader("presentacion", loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        self.assertTrue(hasattr(module, "MainWindow"))


if __name__ == "__main__":
    unittest.main()
