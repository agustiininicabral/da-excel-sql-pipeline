from __future__ import annotations
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

import pandas as pd

@dataclass
class PipelineConfig:
    excel_path: str
    sheet: Any
    table: str
    key: Optional[str]
    db_path: str
    rules_path: str
    out_dir: str
    cleaned_excel_path: str

def _ensure_dirs(out_dir: str, db_path: str):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

def _read_excel(excel_path: str, sheet: Any) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name=sheet, engine="openpyxl")
    # Normalizar nombres de columnas (limpia espacios)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Quita filas completamente vacías
    df2 = df.dropna(how="all").copy()

    # Trim en strings
    for col in df2.columns:
        if pd.api.types.is_string_dtype(df2[col]):
            df2[col] = df2[col].astype(str).str.strip()

    return df2

def _profile(df: pd.DataFrame, key: Optional[str]) -> pd.DataFrame:
    rows = []
    total = len(df)

    for col in df.columns:
        s = df[col]
        nulls = int(s.isna().sum())
        nunique = int(s.nunique(dropna=True))
        dtype = str(s.dtype)

        rows.append({
            "column": col,
            "dtype": dtype,
            "total_rows": total,
            "null_count": nulls,
            "null_pct": round((nulls / total * 100), 2) if total else 0.0,
            "unique_count": nunique
        })

    prof = pd.DataFrame(rows).sort_values(["null_count", "unique_count"], ascending=[False, True])

    # duplicados por clave
    if key and key in df.columns:
        dup_ids = int(df[key].duplicated(keep=False).sum())
        prof = pd.concat([prof, pd.DataFrame([{
            "column": key,
            "dtype": str(df[key].dtype),
            "total_rows": total,
            "null_count": int(df[key].isna().sum()),
            "null_pct": round((int(df[key].isna().sum()) / total * 100), 2) if total else 0.0,
            "unique_count": int(df[key].nunique(dropna=True)),
            "note": f"duplicated_rows_by_key={dup_ids}"
        }])], ignore_index=True)

    return prof

def _to_sqlite(df: pd.DataFrame, db_path: str, table: str):
    with sqlite3.connect(db_path) as con:
        df.to_sql(table, con, if_exists="replace", index=False)

def _run_rules(db_path: str, rules_sql: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as con:
        # Ejecuta múltiples SELECT en un solo script:
        # En SQLite, ejecutamos statement por statement para capturar resultados.
        cur = con.cursor()
        statements = [s.strip() for s in rules_sql.split(";") if s.strip()]
        results = []
        for stmt in statements:
            cur.execute(stmt)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
            for r in rows:
                results.append(dict(zip(cols, r)))
        return pd.DataFrame(results)

def _write_report(profile_df: pd.DataFrame, rules_df: pd.DataFrame, out_dir: str, meta: dict):
    profile_path = os.path.join(out_dir, "profile_summary.csv")
    rules_path = os.path.join(out_dir, "rules_results.csv")
    md_path = os.path.join(out_dir, "report.md")

    profile_df.to_csv(profile_path, index=False, encoding="utf-8")
    rules_df.to_csv(rules_path, index=False, encoding="utf-8")

    # Markdown report (simple y presentable)
    passed = int((rules_df["status"] == "PASS").sum()) if "status" in rules_df.columns else 0
    failed = int((rules_df["status"] == "FAIL").sum()) if "status" in rules_df.columns else 0

    md = []
    md.append("# Data Quality Report")
    md.append("")
    md.append(f"- Generated at: **{meta['generated_at']}**")
    md.append(f"- Source Excel: **{meta['excel_path']}**")
    md.append(f"- Table: **{meta['table']}**")
    md.append(f"- Rows loaded: **{meta['rows_loaded']}**")
    md.append("")
    md.append("## Rules summary")
    md.append(f"- PASS: **{passed}**")
    md.append(f"- FAIL: **{failed}**")
    md.append("")
    md.append("## Rules details")
    if len(rules_df) == 0:
        md.append("_No rules executed._")
    else:
        md.append(rules_df.to_markdown(index=False))
    md.append("")
    md.append("## Profiling (top 25 by null_count)")
    md.append(profile_df.head(25).to_markdown(index=False))

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

def run_pipeline(
    excel_path: str,
    sheet: Any,
    table: str,
    key: Optional[str],
    db_path: str,
    rules_path: str,
    out_dir: str,
    cleaned_excel_path: str
):
    cfg = PipelineConfig(
        excel_path=excel_path,
        sheet=sheet,
        table=table,
        key=key,
        db_path=db_path,
        rules_path=rules_path,
        out_dir=out_dir,
        cleaned_excel_path=cleaned_excel_path
    )

    _ensure_dirs(cfg.out_dir, cfg.db_path)

    df_raw = _read_excel(cfg.excel_path, cfg.sheet)
    df_clean = _basic_clean(df_raw)

    # Guarda cleaned Excel
    os.makedirs(os.path.dirname(cfg.cleaned_excel_path) or ".", exist_ok=True)
    df_clean.to_excel(cfg.cleaned_excel_path, index=False, engine="openpyxl")

    # Load to SQLite
    _to_sqlite(df_clean, cfg.db_path, cfg.table)

    # Profiling
    profile_df = _profile(df_clean, cfg.key)

    # Run rules
    with open(cfg.rules_path, "r", encoding="utf-8") as f:
        rules_sql = f.read()

    # Nota: rules.sql asume tabla 'ventas' por defecto.
    # Si el usuario eligió otro nombre de tabla, reemplazamos de forma simple:
    rules_sql = rules_sql.replace("\nFROM ventas\n", f"\nFROM {cfg.table}\n")
    rules_sql = rules_sql.replace("\nFROM (\n  SELECT COUNT(*) AS cnt\n  FROM ventas\n", f"\nFROM (\n  SELECT COUNT(*) AS cnt\n  FROM {cfg.table}\n")
    rules_sql = rules_sql.replace("\n  FROM ventas\n", f"\n  FROM {cfg.table}\n")

    rules_df = _run_rules(cfg.db_path, rules_sql)

    meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "excel_path": cfg.excel_path,
        "table": cfg.table,
        "rows_loaded": int(len(df_clean))
    }

    _write_report(profile_df, rules_df, cfg.out_dir, meta)

    print("OK - Pipeline finished")
    print(f"- Cleaned Excel: {cfg.cleaned_excel_path}")
    print(f"- SQLite DB:      {cfg.db_path}")
    print(f"- Outputs:        {cfg.out_dir}")
