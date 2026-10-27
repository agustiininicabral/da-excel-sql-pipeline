from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from dq_pipeline.cli import _parse_sheet, main
from dq_pipeline.pipeline import _basic_clean, run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def _write_sales(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "sale_id": "S-001",
                "fecha": "2025-01-01",
                "cliente": " Ana ",
                "producto": " Crema ",
                "cantidad": 2,
                "precio_unitario": 100,
                "costo_unitario": 60,
            },
            {
                "sale_id": "S-001",
                "fecha": "2025-01-02",
                "cliente": "Beto",
                "producto": "Jabón",
                "cantidad": 1,
                "precio_unitario": 50,
                "costo_unitario": 20,
            },
            {
                "sale_id": "S-003",
                "fecha": "2025-01-03",
                "cliente": None,
                "producto": "Perfume",
                "cantidad": 1,
                "precio_unitario": 300,
                "costo_unitario": 100,
            },
        ]
    ).to_excel(path, sheet_name="Ventas", index=False)


def test_basic_clean_preserves_missing_text_as_null() -> None:
    dataframe = pd.DataFrame({"cliente": [" Ana ", None, "  "], "cantidad": [1, 2, 3]})

    cleaned = _basic_clean(dataframe)

    assert cleaned["cliente"].iloc[0] == "Ana"
    assert pd.isna(cleaned["cliente"].iloc[1])
    assert pd.isna(cleaned["cliente"].iloc[2])


def test_pipeline_supports_custom_table_and_key_and_writes_reports(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sales.xlsx"
    _write_sales(source)
    database = tmp_path / "data" / "pipeline.db"
    output = tmp_path / "outputs"
    cleaned = output / "cleaned.xlsx"

    passed = run_pipeline(
        excel_path=str(source),
        sheet="Ventas",
        table="sales_data",
        key="sale_id",
        db_path=str(database),
        rules_path=str(ROOT / "sql" / "rules.sql"),
        out_dir=str(output),
        cleaned_excel_path=str(cleaned),
    )

    assert passed is False
    assert "## Result: FAIL" in (output / "report.md").read_text(encoding="utf-8")
    assert cleaned.is_file()
    assert (output / "profile_summary.csv").is_file()
    assert (output / "rules_results.csv").is_file()
    assert (output / "report.md").is_file()

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM sales_data").fetchone()[0] == 3

    rules = pd.read_csv(output / "rules_results.csv")
    assert rules["rule_id"].tolist() == ["R001", "R002", "R003", "R004"]
    duplicate_rule = rules.loc[rules["rule_id"] == "R004"].iloc[0]
    assert duplicate_rule["status"] == "FAIL"
    assert "sale_id" in duplicate_rule["rule_name"]


def test_pipeline_skips_duplicate_key_rule_when_no_key_is_configured(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sales.xlsx"
    _write_sales(source)
    output = tmp_path / "outputs"

    passed = run_pipeline(
        excel_path=str(source),
        sheet="Ventas",
        table="sales",
        key=None,
        db_path=str(tmp_path / "data" / "pipeline.db"),
        rules_path=str(ROOT / "sql" / "rules.sql"),
        out_dir=str(output),
        cleaned_excel_path=str(output / "cleaned.xlsx"),
    )

    assert passed is True
    assert "## Result: PASS" in (output / "report.md").read_text(encoding="utf-8")
    rules = pd.read_csv(output / "rules_results.csv")
    assert rules["rule_id"].tolist() == ["R001", "R002", "R003"]


@pytest.mark.parametrize("table", ["sales; DROP TABLE users", "bad-name", "1sales"])
def test_pipeline_rejects_unsafe_table_identifiers(tmp_path: Path, table: str) -> None:
    with pytest.raises(ValueError, match="Invalid table name"):
        run_pipeline(
            excel_path="does-not-need-to-exist.xlsx",
            sheet=0,
            table=table,
            key=None,
            db_path=str(tmp_path / "data" / "pipeline.db"),
            rules_path=str(ROOT / "sql" / "rules.sql"),
            out_dir=str(tmp_path / "outputs"),
            cleaned_excel_path=str(tmp_path / "outputs" / "cleaned.xlsx"),
        )


def test_pipeline_rejects_duplicate_headers_after_trimming(tmp_path: Path) -> None:
    source = tmp_path / "duplicate_headers.xlsx"
    pd.DataFrame([["A", "B"]], columns=["producto", " producto "]).to_excel(
        source, index=False
    )
    with pytest.raises(
        ValueError, match="Duplicate column names after trimming: producto"
    ):
        run_pipeline(
            excel_path=str(source),
            sheet=0,
            table="ventas",
            key=None,
            db_path=str(tmp_path / "data" / "pipeline.db"),
            rules_path=str(ROOT / "sql" / "rules.sql"),
            out_dir=str(tmp_path / "outputs"),
            cleaned_excel_path=str(tmp_path / "outputs" / "cleaned.xlsx"),
        )


def test_pipeline_rejects_missing_key_column(tmp_path: Path) -> None:
    source = tmp_path / "sales.xlsx"
    _write_sales(source)
    with pytest.raises(ValueError, match="Key column 'missing_id' not found"):
        run_pipeline(
            excel_path=str(source),
            sheet="Ventas",
            table="sales",
            key="missing_id",
            db_path=str(tmp_path / "data" / "pipeline.db"),
            rules_path=str(ROOT / "sql" / "rules.sql"),
            out_dir=str(tmp_path / "outputs"),
            cleaned_excel_path=str(tmp_path / "outputs" / "cleaned.xlsx"),
        )


def test_cli_parses_numeric_sheet_index_as_integer() -> None:
    assert _parse_sheet("0") == 0
    assert isinstance(_parse_sheet("0"), int)
    assert _parse_sheet("Ventas") == "Ventas"


def test_cli_returns_nonzero_when_sql_rules_fail(tmp_path: Path) -> None:
    source = tmp_path / "sales.xlsx"
    _write_sales(source)
    result = main(
        [
            "run",
            "--excel",
            str(source),
            "--sheet",
            "Ventas",
            "--table",
            "ventas",
            "--key",
            "sale_id",
            "--db",
            str(tmp_path / "data" / "pipeline.db"),
            "--rules",
            str(ROOT / "sql" / "rules.sql"),
            "--out",
            str(tmp_path / "outputs"),
            "--cleaned-excel",
            str(tmp_path / "outputs" / "cleaned.xlsx"),
        ]
    )
    assert result == 1


def test_cli_returns_two_for_missing_workbook(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(
        [
            "run",
            "--excel",
            str(tmp_path / "missing.xlsx"),
            "--table",
            "ventas",
            "--db",
            str(tmp_path / "data" / "pipeline.db"),
            "--rules",
            str(ROOT / "sql" / "rules.sql"),
            "--out",
            str(tmp_path / "outputs"),
        ]
    )
    assert result == 2
    assert "ERROR:" in capsys.readouterr().err
