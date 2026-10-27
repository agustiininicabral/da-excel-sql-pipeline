# Excel-to-SQL Data Quality Pipeline

Pipeline de portfolio para perfilar un Excel, cargarlo a SQLite, ejecutar reglas de calidad SQL y generar reportes reproducibles.

La implementación está en la carpeta [da-excel-sql-pipeline](da-excel-sql-pipeline/). Consultá el [README del proyecto](da-excel-sql-pipeline/README.md) para instalación, ejecución, reglas y salidas.

## CI

GitHub Actions ejecuta pruebas automatizadas, Ruff, consistencia de dependencias y la demo incluida. Los artefactos generados se publican temporalmente en la ejecución de Actions.

## Alcance

El proyecto trabaja con datasets locales y sintéticos/de demostración. No envía datos a servicios externos ni modifica el Excel de entrada. Los resultados deben revisarse antes de utilizarlos en procesos de negocio.
