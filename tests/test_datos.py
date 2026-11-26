"""Integration tests of the data layer against a MySQL server loaded with BDERP.sql.

Skipped unless BDERP_TEST_DB=1; CI runs them against a mysql:8 service
container. They build the real MainWindow (offscreen), so they also cover the
login and the start-up queries. Rows they insert use ID >= 100 and are deleted
afterwards.
"""
import os
import unittest

from PyQt5.QtCore import QDate

from _app import load_presentacion

ACTIVO = os.environ.get("BDERP_TEST_DB") == "1"


@unittest.skipUnless(ACTIVO, "set BDERP_TEST_DB=1 and BDERP_DB_* to run against MySQL")
class DatosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.pop("BDERP_TWITTER_ENABLED", None)
        cls.presentacion = load_presentacion()
        cls.ventana = cls.presentacion.MainWindow()

    @classmethod
    def tearDownClass(cls):
        cls.ventana.conn.close()

    def tearDown(self):
        cur = self.ventana.cur
        for tabla in ("ventas", "cliente", "distribuidor", "empleados"):
            cur.execute("delete from `%s` where ID >= 100" % tabla)
        self.ventana.conn.commit()

    def uno(self, sql, args=()):
        self.ventana.cur.execute(sql, args)
        return self.ventana.cur.fetchone()

    # --- login -------------------------------------------------------------
    def test_valid_administrator(self):
        self.assertEqual(self.ventana.verificarAdministrador("Admi", "hello"), 1)

    def test_wrong_password(self):
        self.assertIsNone(self.ventana.verificarAdministrador("Admi", "nope"))

    def test_login_is_not_injectable(self):
        self.assertIsNone(self.ventana.verificarAdministrador(
            "Admi", "' or '1'='1"))
        self.assertIsNone(self.ventana.verificarAdministrador(
            "' or 1=1 -- ", "x"))

    def test_login_form_starts_the_service(self):
        login = self.ventana.login
        login.usuario.setEditText("Yo")
        login.contrasenia.setText("1234")
        self.ventana.verificarCuenta()
        self.assertEqual(self.ventana.administradorActive, 2)
        self.assertEqual(self.ventana.ventas.IDultimaVenta, 14)
        self.assertEqual(self.ventana.RRHH.listEmpleados.rowCount(), 2)
        self.assertEqual(self.ventana.RRHH.listEmpleados.item(0, 1).text(), "empleado1")
        opciones = [a.text() for a in self.ventana.menuBar().actions()[1].menu().actions()]
        self.assertEqual(opciones, ["Compras", "Ventas", "RRHH"])

    def test_login_form_rejects_a_bad_password(self):
        login = self.ventana.login
        login.usuario.setEditText("Yo")
        login.contrasenia.setText("' or '1'='1")
        self.ventana.administradorActive = 0
        self.ventana.verificarCuenta()
        self.assertEqual(self.ventana.administradorActive, 0)
        self.assertEqual(login.Notificacion.text(), "Usuario o contraseña incorrecta")

    # --- clients, suppliers, employees ------------------------------------
    def test_save_client_with_a_quote_in_the_name(self):
        self.ventana.guardarClienteBD(100, "O'Brien", "10123456789")
        self.assertEqual(self.uno("select nombre, RUC from cliente where ID=100"),
                         ("O'Brien", 10123456789))

    def test_client_form_saves_with_the_next_id(self):
        self.ventana.nuevoCliente.IDultimoCliente = 99
        self.ventana.nuevoCliente.nombre.setText("Nuevo")
        self.ventana.nuevoCliente.RUC.setText("20123456789")
        self.ventana.guardarCliente()
        self.assertEqual(self.ventana.nuevoCliente.IDultimoCliente, 100)
        self.assertEqual(self.uno("select nombre from cliente where ID=100"), ("Nuevo",))

    def test_save_supplier(self):
        nombre = "'); drop table productos#"  # fits varchar(25)
        self.ventana.guardarProveedorBD(100, nombre, "1")
        self.assertEqual(self.uno("select nombre from distribuidor where ID=100"), (nombre,))
        self.assertEqual(self.uno("select count(*) from productos"), (1,))

    def test_employee_form_saves_the_row(self):
        formulario = self.ventana.nuevoEmpleado
        formulario.puesto.addItem("analista")
        formulario.puesto.setCurrentText("analista")
        formulario.nombre.setText("Ana")
        formulario.dni.setText("12345678")
        formulario.salario.setValue(55.5)  # the form caps it at 99.99
        self.ventana.RRHH.IDultimoEmpleado = 99
        filas = self.ventana.RRHH.listEmpleados.rowCount()
        self.ventana.guardarEmpleado()
        fila = self.uno("select nombre, DNI, puesto, sueldo from empleados where ID=100")
        self.assertIsNotNone(fila)
        self.assertEqual(fila[:3], ("Ana", 12345678, "analista"))
        self.assertEqual(float(fila[3]), 55.5)
        self.assertEqual(self.ventana.RRHH.listEmpleados.rowCount(), filas + 1)

    # --- sales -------------------------------------------------------------
    def test_client_lookup(self):
        self.assertEqual(self.ventana.idCliente("cliente1"), 1)
        self.assertIsNone(self.ventana.idCliente("nadie"))
        self.assertIsNone(self.ventana.idCliente("x' or '1'='1"))

    def test_record_a_sale(self):
        detalle = self.ventana.ventaDetalle
        detalle.clientes.setEditText("cliente1")
        detalle.fecha.setDate(QDate(2016, 7, 5))
        self.ventana.ventas.IDultimaVenta = 99
        self.ventana.aniadirVenta()
        fila = self.uno("select ID_cliente, date(fecha) from ventas where ID=100")
        self.assertEqual(fila[0], 1)
        self.assertEqual(str(fila[1]), "2016-07-05")

    def test_sale_for_an_unknown_client_is_not_recorded(self):
        self.ventana.ventaDetalle.clientes.setEditText("nadie")
        self.ventana.ventas.IDultimaVenta = 99
        self.ventana.aniadirVenta()
        self.assertEqual(self.ventana.ventas.IDultimaVenta, 99)
        self.assertIsNone(self.uno("select ID from ventas where ID=100"))

    def test_add_a_product_line_to_a_sale(self):
        self.ventana.iniciarDetalleVenta()
        detalle = self.ventana.ventaDetalle
        detalle.productosVenta.setColumnCount(4)
        detalle.productos.setCurrentText("producto1")
        detalle.cantidadProducto.setValue(3)
        filas = detalle.productosVenta.rowCount()
        self.ventana.aniadirProductoVenta()
        self.assertEqual([detalle.productosVenta.item(filas, i).text() for i in range(4)],
                         ["1", "producto1", "12.34", "3"])

    def test_last_ids(self):
        self.assertEqual(self.ventana.ultimoID("ventas"), 14)
        self.assertEqual(self.ventana.ultimoID("compras"), 0)
        self.assertEqual(self.ventana.ultimoID("empleados"), 2)


if __name__ == "__main__":
    unittest.main()
