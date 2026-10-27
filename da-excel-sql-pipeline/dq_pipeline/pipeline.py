from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class PipelineConfig:
    excel_path: str
    sheet: str | int
    table: str
    key: str | None
    db_path: str
    rules_path: str
    out_dir: str
    cleaned_excel_path: str


def _validate_identifier(value: str, label: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid {label} {value!r}. Use letters, digits, and underscores; "
            "the first character must be a letter or underscore."
        )


def _ensure_dirs(out_dir: str, db_path: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)


def _read_excel(excel_path: str, sheet: str | int) -> pd.DataFrame:
    dataframe = pd.read_excel(excel_path, sheet_name=sheet, engine="openpyxl")
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    return dataframe


def _basic_clean(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = dataframe.dropna(how="all").copy()
    for column in cleaned.columns:
        if pd.api.types.is_object_dtype(
            cleaned[column]
        ) or pd.api.types.is_string_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].astype("string").str.strip()
            cleaned[column] = cleaned[column].replace("", pd.NA)
    return cleaned


def _profile(dataframe: pd.DataFrame, key: str | None) -> pd.DataFrame:
    rows = []
    total = len(dataframe)

    for column in dataframe.columns:
        series = dataframe[column]
        null_count = int(series.isna().sum())
        rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "total_rows": total,
                "null_count": null_count,
                "null_pct": round(null_count / total * 100, 2) if total else 0.0,
                "unique_count": int(series.nunique(dropna=True)),
            }
        )

    profile = pd.DataFrame(rows).sort_values(
        ["null_count", "unique_count"],
        ascending=[False, True],
    )
    if key and key in dataframe.columns:
        key_nulls = int(dataframe[key].isna().sum())
        duplicate_rows = int(dataframe[key].duplicated(keep=False).sum())
        key_profile = pd.DataFrame(
            [
                {
                    "column": key,
                    "dtype": str(dataframe[key].dtype),
                    "total_rows": total,
                    "null_count": key_nulls,
                    "null_pct": round(key_nulls / total * 100, 2) if total else 0.0,
                    "unique_count": int(dataframe[key].nunique(dropna=True)),
                    "note": f"duplicated_rows_by_key={duplicate_rows}",
                }
            ]
        )
        profile = pd.concat([profile, key_profile], ignore_index=True)

    return profile


def _to_sqlite(dataframe: pd.DataFrame, db_path: str, table: str) -> None:
    with sqlite3.connect(db_path) as connection:
        dataframe.to_sql(table, connection, if_exists="replace", index=False)


def _prepare_rules_sql(rules_sql: str, table: str, key: str | None) -> list[str]:
    statements = [
        statement.strip() for statement in rules_sql.split(";") if statement.strip()
    ]
    prepared = []
    for statement in statements:
        if "'R004' AS rule_id" in statement:
            if key is None:
                continue
            statement = re.sub(
                r"\bSELECT\s+id_venta\b", f'SELECT "{key}"', statement
            )
            statement = re.sub(
                r"\bGROUP BY\s+id_venta\b", f'GROUP BY "{key}"', statement
            )
            statement = statement.replace(
                "Duplicados por id_venta", f"Duplicados por {key}"
            )

        statement = re.sub(
            r"\bFROM\s+ventas\b",
            f'FROM "{table}"',
            statement,
            flags=re.IGNORECASE,
        )
        prepared.append(statement)

    return prepared


def _run_rules(db_path: str, statements: list[str]) -> pd.DataFrame:
    results = []
    with sqlite3.connect(db_path) as connection:
        for statement in statements:
            cursor = connection.execute(statement)
            columns = [description[0] for description in cursor.description or []]
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
    return pd.DataFrame(results)


def _write_report(
    profile_df: pd.DataFrame,
    rules_df: pd.DataFrame,
    out_dir: str,
    metadata: dict[str, Any],
) -> None:
    profile_path = os.path.join(out_dir, "profile_summary.csv")
    rules_path = os.path.join(out_dir, "rules_results.csv")
    markdown_path = os.path.join(out_dir, "report.md")

    profile_df.to_csv(profile_path, index=False, encoding="utf-8")
    rules_df.to_csv(rules_path, index=False, encoding="utf-8")

    passed = int((rules_df["status"] == "PASS").sum()) if "status" in rules_df else 0
    failed = int((rules_df["status"] == "FAIL").sum()) if "status" in rules_df else 0
    lines = [
        "# Data Quality Report",
        "",
        f"- Generated at: **{metadata['generated_at']}**",
        f"- Source Excel: **{metadata['excel_path']}**",
        f"- Table: **{metadata['table']}**",
        f"- Rows loaded: **{metadata['rows_loaded']}**",
        "",
        "## Rules summary",
        f"- PASS: **{passed}**",
        f"- FAIL: **{failed}**",
        "",
        "## Rules details",
        rules_df.to_markdown(index=False)
        if not rules_df.empty
        else "_No rules executed._",
        "",
        "## Profiling (top 25 by null_count)",
        profile_df.head(25).to_markdown(index=False),
    ]
    with open(markdown_path, "w", encoding="utf-8") as report:
        report.write("\n".join(lines))


def run_pipeline(
    excel_path: str,
    sheet: str | int,
    table: str,
    key: str | None,
    db_path: str,
    rules_path: str,
    out_dir: str,
    cleaned_excel_path: str,
) -> None:
    _validate_identifier(table, "table name")
    if key is not None:
        _validate_identifier(key, "key column")

    config = PipelineConfig(
        excel_path=excel_path,
        sheet=sheet,
        table=table,
        key=key,
        db_path=db_path,
        rules_path=rules_path,
        out_dir=out_dir,
        cleaned_excel_path=cleaned_excel_path,
    )
    _ensure_dirs(config.out_dir, config.db_path)

    raw_dataframe = _read_excel(config.excel_path, config.sheet)
    cleaned_dataframe = _basic_clean(raw_dataframe)
    if cleaned_dataframe.empty:
        raise ValueError("No non-empty rows remain after cleaning the input workbook.")

    os.makedirs(os.path.dirname(config.cleaned_excel_path) or ".", exist_ok=True)
    cleaned_dataframe.to_excel(
        config.cleaned_excel_path,
        index=False,
        engine="openpyxl",
    )
    _to_sqlite(cleaned_dataframe, config.db_path, config.table)

    profile_df = _profile(cleaned_dataframe, config.key)
    with open(config.rules_path, encoding="utf-8") as rules_file:
        statements = _prepare_rules_sql(rules_file.read(), config.table, config.key)
    rules_df = _run_rules(config.db_path, statements)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "excel_path": config.excel_path,
        "table": config.table,
        "rows_loaded": int(len(cleaned_dataframe)),
    }
    _write_report(profile_df, rules_df, config.out_dir, metadata)

    print("OK - Pipeline finished")
    print(f"- Cleaned Excel: {config.cleaned_excel_path}")
    print(f"- SQLite DB: {config.db_path}")
    print(f"- Outputs: {config.out_dir}")
