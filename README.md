# pyqt-mysql-erp

[![CI](https://github.com/Wil12Fred/pyqt-mysql-erp/actions/workflows/ci.yml/badge.svg)](https://github.com/Wil12Fred/pyqt-mysql-erp/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small desktop ERP prototype in Python with PyQt5 — an MDI window with Qt
Designer forms for purchases, sales, clients, suppliers and HR — on top of a
MySQL database accessed with PyMySQL. UI and code are in Spanish.

`diagramaBPM.pdf` is the business-process diagram.

## Features

- **Login** against the `administrador` table.
- **Compras / Ventas** — purchases and sales with line items; add suppliers
  and clients. *Ventas* reads the official USD/PEN exchange rate from SUNAT's
  web page and shows the last three published days (`sunat.txt` is a saved
  copy of that page, used by the tests).
- **RRHH** — list and add employees.
- **Bolsa de Valores** (optional, off by default) — top stock-market tweets
  through the Twitter API v1.1 (`infoBolsa.py`, `python-twitter`).
- Every query uses PyMySQL placeholders; table names are checked against a
  fixed list.
- `BDERP.sql` — a MySQL 5.7 dump with the schema and sample rows; it loads
  into MySQL 8.

## Requirements

- Python 3.9+ and [uv](https://docs.astral.sh/uv/).
  - Debian/Ubuntu: `sudo apt install python3`, then
    `curl -LsSf https://astral.sh/uv/install.sh | sh` (uv is not packaged).
  - Arch: `sudo pacman -S python uv`
- Qt runtime libraries for the PyQt5 wheel.
  - Debian/Ubuntu: `sudo apt install libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0`
  - Arch: `sudo pacman -S libglvnd libxkbcommon-x11 xcb-util-cursor`
- A MySQL 8 (or MariaDB) server and client.
  - Debian/Ubuntu: `sudo apt install mysql-server mysql-client`
    (or `mariadb-server mariadb-client`)
  - Arch: `sudo pacman -S mariadb mariadb-clients`

Configuration comes from the environment, see `.env.example`:
`BDERP_DB_HOST`, `BDERP_DB_USER`, `BDERP_DB_PASSWORD`, `BDERP_DB_NAME`, and,
for the optional window, `BDERP_TWITTER_ENABLED=1` plus the four
`TWITTER_*` credentials.

## Build

Nothing is compiled; `uv` creates the environment:

```bash
uv sync --locked                       # add --extra twitter for Bolsa de Valores
```

## Run

```bash
mysql -u root -p -e "CREATE DATABASE BDERP"
mysql -u root -p BDERP < BDERP.sql
cp .env.example .env                   # fill in the DB credentials
set -a; . ./.env; set +a
uv run python presentacion.pyw
```

Log in with a `usuario` / `contrasenia` pair from the `administrador` table
(for example `Yo` / `1234` from the sample data). CI starts the application
under `xvfb-run` against a MySQL 8 container loaded with `BDERP.sql`; captured
from that run:

```
$ xvfb-run -a timeout 10 uv run python presentacion.pyw; echo "exit status: $?"
exit status: 124
```

124 is `timeout` stopping a window that was still open, which is the pass
condition.

## Tests

```bash
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
```

Without a database the MySQL tests are skipped; to run them, load
`BDERP.sql` and set `BDERP_TEST_DB=1` and the `BDERP_DB_*` variables. CI does
this against a `mysql:8` service container.

- `tests/test_datos.py` (MySQL, 14 tests, building the real `MainWindow`
  offscreen) — administrator login, wrong password, and login inputs such as
  `' or '1'='1` refused; the login form starts the service (employees listed,
  last sale id read, no Twitter menu entry); clients, suppliers and employees
  saved through the forms, including names with quotes and SQL in them;
  client lookup; recording a sale and refusing one for an unknown client;
  adding a product line; last ids per table.
- `tests/test_logica.py` — the exchange-rate table built from the saved SUNAT
  page (last three days, three fixed columns), `urllib.request` available in
  a fresh interpreter, the Twitter switch, and `ultimoID` refusing an unknown
  table without touching the database.
- `tests/test_smoke.py` — every `.ui` form loads, the main module imports,
  and the Twitter client builds without credentials (skipped without the
  `twitter` extra).

## Project layout

```
presentacion.pyw   main window and all business logic
infoBolsa.py       Twitter search and ranking of tweets (optional)
mdirc_.py          compiled Qt resource module (pyrcc5 output)
*.ui               Qt Designer forms
BDERP.sql          database schema and sample data
sunat.txt          saved SUNAT exchange-rate page
tests/             smoke, logic and MySQL integration tests
```

## Known limitations

- The Twitter API v1.1 search used by *Bolsa de Valores* is no longer free,
  so the window is disabled unless `BDERP_TWITTER_ENABLED=1`; even then it
  needs paid API access.
- The exchange rate is scraped from SUNAT's page layout of 2016; if the live
  page changes, *Actualizar* in *Ventas* fails.
- *Confirmar compra* does nothing (`aniadirCompra` is empty), and the line
  items of a sale are not stored in `ventas_detalle`.
- Passwords are stored and compared in plain text; ids are computed as
  `MAX(ID)+1` in the client, so two users at once can collide.
- Database errors on inserts are rolled back silently.

## Background

Written in 2016 for a databases / software course at a university.

## License

MIT — see [LICENSE](LICENSE).
