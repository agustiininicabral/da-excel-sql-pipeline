import argparse
from .pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(prog="dq_pipeline", description="Excel → SQLite → SQL rules → Report")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run the data quality pipeline")
    run.add_argument("--excel", required=True, help="Path to Excel (.xlsx)")
    run.add_argument("--sheet", default=0, help="Sheet name or index (default 0)")
    run.add_argument("--table", required=True, help="SQLite table name to load into")
    run.add_argument("--key", default=None, help="Primary key column (used for duplicate check in profiling)")
    run.add_argument("--db", default="data/pipeline.db", help="SQLite DB path (default data/pipeline.db)")
    run.add_argument("--rules", default="sql/rules.sql", help="SQL rules file path (default sql/rules.sql)")
    run.add_argument("--out", default="outputs", help="Output folder (default outputs)")
    run.add_argument("--cleaned-excel", default="outputs/cleaned.xlsx", help="Cleaned Excel output path")

    args = parser.parse_args()

    if args.cmd == "run":
        run_pipeline(
            excel_path=args.excel,
            sheet=args.sheet,
            table=args.table,
            key=args.key,
            db_path=args.db,
            rules_path=args.rules,
            out_dir=args.out,
            cleaned_excel_path=args.cleaned_excel
        )
