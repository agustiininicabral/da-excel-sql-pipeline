import argparse
import sqlite3
import sys

from .pipeline import run_pipeline


def _parse_sheet(value: str) -> str | int:
    try:
        return int(value)
    except ValueError:
        return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dq_pipeline",
        description="Excel → SQLite → SQL rules → Report",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    run_parser = subparsers.add_parser("run", help="Run the data quality pipeline")
    run_parser.add_argument("--excel", required=True, help="Path to Excel (.xlsx)")
    run_parser.add_argument(
        "--sheet",
        type=_parse_sheet,
        default=0,
        help="Sheet name or index (default: 0)",
    )
    run_parser.add_argument(
        "--table",
        required=True,
        help="SQLite table name to load into",
    )
    run_parser.add_argument(
        "--key",
        default=None,
        help="Primary key column (used for duplicate check in profiling)",
    )
    run_parser.add_argument(
        "--db",
        default="data/pipeline.db",
        help="SQLite DB path (default data/pipeline.db)",
    )
    run_parser.add_argument(
        "--rules",
        default="sql/rules.sql",
        help="SQL rules file path (default sql/rules.sql)",
    )
    run_parser.add_argument(
        "--out",
        default="outputs",
        help="Output folder (default outputs)",
    )
    run_parser.add_argument(
        "--cleaned-excel",
        default="outputs/cleaned.xlsx",
        help="Cleaned Excel output path",
    )

    args = parser.parse_args(argv)
    if args.cmd == "run":
        try:
            passed = run_pipeline(
                excel_path=args.excel,
                sheet=args.sheet,
                table=args.table,
                key=args.key,
                db_path=args.db,
                rules_path=args.rules,
                out_dir=args.out,
                cleaned_excel_path=args.cleaned_excel,
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        return 0 if passed else 1
    return 2


if __name__ == "__main__":
    main()
