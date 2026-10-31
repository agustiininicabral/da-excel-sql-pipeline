# Excel-to-SQL Data Quality Pipeline

Pipeline de portfolio para demostrar un flujo reproducible de **Excel → Python/pandas → SQLite → SQL → reportes**. Lee un archivo Excel, perfila sus datos, aplica reglas de calidad, separa registros válidos y rechazados y genera reportes para revisión.

## Problema que resuelve

En un proceso de análisis, cargar una planilla sin validar claves, nulos, duplicados o reglas de negocio puede propagar errores al análisis. Este proyecto muestra cómo detectar esos problemas antes de utilizar los datos y conservar evidencia de las filas rechazadas.

## Herramientas

- Python 3.12
- pandas y openpyxl
- SQLite
- SQL para reglas de calidad
- pytest y Ruff
- GitHub Actions

## Estructura

La implementación está dentro de `da-excel-sql-pipeline/`:

- `dq_pipeline/`: CLI, carga, profiling, validación y exportación.
- `sql/rules.sql`: reglas de calidad ejecutadas en SQLite.
- `examples/ventas_demo.xlsx`: Excel sintético de demostración.
- `tests/test_pipeline.py`: pruebas automatizadas.
- `.github/workflows/ci.yml`: controles ejecutados por GitHub Actions.

## Cómo ejecutarlo

Desde la raíz del repositorio, en Windows PowerShell:

```powershell
cd da-excel-sql-pipeline
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q
```

Ejecutá la demo:

```powershell
python -m dq_pipeline run --excel examples/ventas_demo.xlsx --sheet Ventas --table ventas --key id_venta
```

El comando genera archivos en `outputs/` y una base SQLite local en `data/`. La demo contiene un duplicado intencional de `sale_id`; por diseño, la regla correspondiente debe reportar FAIL y el proceso puede devolver código de salida `1` aunque haya generado los reportes correctamente.

## Resultados y evidencia

El reporte generado incluye el perfil de los datos, el resultado de cada regla SQL y el archivo Excel con las filas aceptadas.

**Capturas sugeridas para completar esta sección:**
- [COMPLETAR: captura del reporte de calidad PASS/FAIL]
- [COMPLETAR: captura del Excel limpio y de las filas rechazadas]
- [COMPLETAR: captura de una ejecución exitosa de GitHub Actions]

## Limitaciones

- El proyecto trabaja con archivos Excel locales; no se conecta a ERP ni a bases de datos externas.
- Las reglas incluidas son demostrativas y deben adaptarse al dominio de cada dataset.
- Las filas rechazadas requieren revisión humana antes de corregir o descartar datos.
- Los datos de ejemplo son sintéticos. No publiques archivos de empresas, clientes o empleados sin autorización y anonimización.
- La implementación está anidada en `da-excel-sql-pipeline/`; los comandos deben ejecutarse desde esa carpeta.

## Licencia

[COMPLETAR: confirmar la licencia del proyecto y agregar el archivo LICENSE si corresponde.]

Consultá el [README detallado de la implementación](da-excel-sql-pipeline/README.md).
