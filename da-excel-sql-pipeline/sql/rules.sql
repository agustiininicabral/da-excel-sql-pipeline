-- Reglas SQL de Data Quality (SQLite)
-- Convención: cada SELECT devuelve:
-- rule_id, rule_name, status, details

-- 1) No nulos en campos críticos
SELECT
  'R001' AS rule_id,
  'Campos críticos sin nulos' AS rule_name,
  CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  'Filas con nulos en (fecha, producto, cantidad, precio_unitario): ' || cnt AS details
FROM (
  SELECT COUNT(*) AS cnt
  FROM ventas
  WHERE fecha IS NULL
     OR producto IS NULL
     OR cantidad IS NULL
     OR precio_unitario IS NULL
);

-- 2) Cantidad positiva
SELECT
  'R002' AS rule_id,
  'Cantidad debe ser > 0' AS rule_name,
  CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  'Filas con cantidad <= 0: ' || cnt AS details
FROM (
  SELECT COUNT(*) AS cnt
  FROM ventas
  WHERE cantidad <= 0
);

-- 3) Precio unitario no negativo
SELECT
  'R003' AS rule_id,
  'Precio unitario debe ser >= 0' AS rule_name,
  CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  'Filas con precio_unitario < 0: ' || cnt AS details
FROM (
  SELECT COUNT(*) AS cnt
  FROM ventas
  WHERE precio_unitario < 0
);

-- 4) Duplicados por clave (si existe id_venta)
SELECT
  'R004' AS rule_id,
  'Duplicados por id_venta' AS rule_name,
  CASE WHEN cnt = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
  'Cantidad de ids duplicados: ' || cnt AS details
FROM (
  SELECT COUNT(*) AS cnt
  FROM (
    SELECT id_venta
    FROM ventas
    GROUP BY id_venta
    HAVING COUNT(*) > 1
  )
);
