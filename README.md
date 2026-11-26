# BDERP — PyQt5 + MySQL ERP prototype

A small desktop ERP written in Python 3 with PyQt5 (MDI window, Qt Designer
`.ui` forms) on top of a MySQL database accessed with PyMySQL. University
databases/software project, 2016. UI and code are in Spanish.

Windows (menu *Opcion*):

- **Login** — checks the `administrador` table.
- **Compras / Ventas** — record purchases and sales with line items, add
  suppliers and clients. *Ventas* also scrapes the official USD/PEN exchange
  rate from SUNAT with BeautifulSoup (`sunat.txt` is a saved copy of that page).
- **RRHH** — list and add employees.
- **Bolsa de Valores** — top stock-market tweets via the Twitter API
  (`infoBolsa.py`, `python-twitter`).

`BDERP.sql` is a MySQL 5.7 dump with the schema and sample rows;
`diagramaBPM.pdf` is the business-process diagram.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a MySQL/MariaDB server.

```bash
uv sync                                   # creates .venv with the pinned deps
mysql -u root -p -e "CREATE DATABASE BDERP"
mysql -u root -p BDERP < BDERP.sql
cp .env.example .env                      # fill in DB and Twitter credentials
set -a; . ./.env; set +a
uv run python presentacion.pyw
```

Log in with a user/password row from the `administrador` table. Without
Twitter credentials the app still starts; only the *Bolsa de Valores* refresh
fails (the Twitter v1.1 search API it uses is no longer freely available).

## Tests

```bash
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
```

Smoke tests only: every `.ui` form loads, the modules import, and the Twitter
client builds without credentials. They do not need a database.

## Layout

```
presentacion.pyw   main window and all business logic (SQL is built inline)
infoBolsa.py       Twitter search + ranking of tweets
mdirc_.py          compiled Qt resource module (pyrcc5 output, imported by the app)
*.ui               Qt Designer forms
BDERP.sql          database schema + sample data
tests/             smoke tests
```

Known issue kept as-is: SQL statements are built by string concatenation, so
the forms are open to SQL injection. Fine for a classroom demo, not for real use.
