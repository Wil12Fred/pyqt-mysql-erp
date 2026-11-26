"""Shared helpers: load presentacion.pyw as a module and one QApplication."""
import importlib.machinery
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])


def load_presentacion():
    loader = importlib.machinery.SourceFileLoader(
        "presentacion", os.path.join(ROOT, "presentacion.pyw"))
    spec = importlib.util.spec_from_loader("presentacion", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
