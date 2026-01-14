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

pip install -r requirements.txt
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
- Great Expectations / pandera para validaciones avanzadas
