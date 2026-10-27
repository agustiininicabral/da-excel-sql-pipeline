# da-excel-sql-pipeline

Pipeline profesional de **Data Analytics / Data Quality** para portfolio: toma un **Excel**, lo carga a una **base de datos SQLite**, ejecuta **validaciones SQL**, genera un **reporte** (CSV + Markdown) y exporta un **Excel limpio**.

Está pensado para mostrar:
- Excel → Python (pandas) → Base de datos → SQL → Reporte
- Data Quality Checks (nulos, duplicados, rangos, reglas de negocio)
- Output reproducible ideal para GitHub + CI (puedes agregarlo luego)

## Qué incluye
- CLI: `python -m dq_pipeline ...`
- Carga de Excel a SQLite (`data/pipeline.db`)
- Profiling básico (tipos, nulos, duplicados por clave)
- Reglas SQL (carpeta `sql/`) con estado PASS/FAIL
- Export del dataset “limpio” a `outputs/cleaned.xlsx`

## Requisitos
- Python 3.10+
- (Recomendado) Entorno virtual

## Instalación
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements-dev.txt
```

## Ejecución (demo incluida)
```bash
python -m dq_pipeline run --excel examples/ventas_demo.xlsx --sheet Ventas --table ventas --key id_venta
```

Outputs:
- `outputs/profile_summary.csv`
- `outputs/rules_results.csv`
- `outputs/report.md`
- `outputs/cleaned.xlsx`
- `data/pipeline.db`

## Cómo usar con tu Excel real
1. Exporta tu dataset a `.xlsx`
2. Ejecuta:
```bash
python -m dq_pipeline run --excel TU_ARCHIVO.xlsx --sheet Hoja1 --table mi_tabla --key tu_id
```
3. Ajusta reglas en `sql/rules.sql` o agrega nuevas en `sql/rules/`

## Ideas para mejorar (si querés escalarlo a nivel “enterprise”)
- Conectar a PostgreSQL (SQLAlchemy)
- Generar reportes HTML (Jinja2)
- Tests automáticos con pytest + GitHub Actions
- Checks de formato/lint con Ruff y validación de consistencia de dependencias
- Great Expectations / pandera para validaciones avanzadas

## Pruebas y calidad

Desde esta carpeta:

```powershell
python -m pip check
python -m ruff format --check dq_pipeline tests
python -m ruff check dq_pipeline tests
python -m pytest -q
```

GitHub Actions ejecuta las mismas comprobaciones desde la raíz del repositorio y prueba la demo incluida.

Los nombres de tabla y de clave se validan como identificadores SQL antes de construir consultas. Si no se indica `--key`, la regla de duplicados por clave se omite. Los valores de texto vacíos se conservan como nulos para que el profiling los detecte, en lugar de convertirlos en el texto literal `nan`.


## Exit codes and validation behavior

- `0`: every SQL rule returns `PASS`.
- `1`: the pipeline completed and at least one SQL rule returned `FAIL`; reports and cleaned outputs are still generated.
- `2`: an input, configuration, SQL, or output error prevented a valid evaluation. The CLI prints a concise error to stderr.

The included demo intentionally contains a duplicate `sale_id`, so it should return `1` and produce a `FAIL` report. Numeric `--sheet` arguments are parsed as zero-based Excel sheet indexes. Duplicate headers after trimming and configured key columns that do not exist are rejected before loading data into SQLite.
