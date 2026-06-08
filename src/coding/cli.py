from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .agreement import compute_pairwise_agreement
from .annotation import create_annotation_template
from .codebook import flatten_codes, load_codebook, validate_codebook
from .coded_segments import get_coded_segments
from .export import export_manual_coding_report
from .import_annotations import import_annotation_file
from .mixed_methods import code_matrix
from .sampling import build_annotation_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual coding toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate-codebook")
    p_validate.add_argument("--codebook", required=True)
    p_validate.add_argument("--export-csv")

    p_sample = sub.add_parser("sample")
    p_sample.add_argument("--input", required=True)
    p_sample.add_argument("--output", required=True)
    p_sample.add_argument("--strategy", required=True)
    p_sample.add_argument("--n", required=True, type=int)
    p_sample.add_argument("--random-state", type=int, default=42)
    p_sample.add_argument("--toponym")
    p_sample.add_argument("--group")
    p_sample.add_argument("--period")
    p_sample.add_argument("--topic-id")

    p_template = sub.add_parser("template")
    p_template.add_argument("--sample", required=True)
    p_template.add_argument("--schema", required=True)
    p_template.add_argument("--codebook", required=True)
    p_template.add_argument("--output", required=True)
    p_template.add_argument("--coder-id")

    p_import = sub.add_parser("import")
    p_import.add_argument("--input", required=True)
    p_import.add_argument("--schema", required=True)
    p_import.add_argument("--codebook", required=True)
    p_import.add_argument("--output", required=True)

    p_agree = sub.add_parser("agreement")
    p_agree.add_argument("--a", required=True)
    p_agree.add_argument("--b", required=True)
    p_agree.add_argument("--fields", nargs="+", required=True)
    p_agree.add_argument("--output-prefix", default="data/annotation/reports/intercoder_agreement")

    p_segments = sub.add_parser("segments")
    p_segments.add_argument("--annotations", required=True)
    p_segments.add_argument("--code", required=True)
    p_segments.add_argument("--field")
    p_segments.add_argument("--output", required=True)

    p_matrix = sub.add_parser("matrix")
    p_matrix.add_argument("--annotations", required=True)
    p_matrix.add_argument("--rows", required=True)
    p_matrix.add_argument("--columns", required=True)
    p_matrix.add_argument("--normalize")
    p_matrix.add_argument("--output", required=True)

    p_report = sub.add_parser("report")
    p_report.add_argument("--annotations", required=True)
    p_report.add_argument("--output", required=True)

    args = parser.parse_args()
    _dispatch(args)


def _dispatch(args: argparse.Namespace) -> None:
    if args.command == "validate-codebook":
        book = load_codebook(args.codebook)
        errors = validate_codebook(book)
        if args.export_csv:
            frame = flatten_codes(book)
            Path(args.export_csv).parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(args.export_csv, index=False, encoding="utf-8")
        if errors:
            raise SystemExit("\n".join(errors))
        print("Codebook valid.")
        return

    if args.command == "sample":
        filters = {"toponym": args.toponym, "group": args.group, "period": args.period, "topic_id": args.topic_id}
        build_annotation_sample(args.input, args.output, args.n, args.strategy, args.random_state, filters)
        print(f"Sample written: {args.output}")
        return

    if args.command == "template":
        sample = _read_any_table(args.sample)
        create_annotation_template(sample, args.schema, args.codebook, args.output, args.coder_id)
        print(f"Template written: {args.output}")
        return

    if args.command == "import":
        frame = import_annotation_file(args.input, args.schema, args.codebook)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(out, index=False, encoding="utf-8")
        print(f"Validated annotations written: {out}")
        return

    if args.command == "agreement":
        a = _read_any_table(args.a)
        b = _read_any_table(args.b)
        report = compute_pairwise_agreement(a, b, args.fields)
        prefix = Path(args.output_prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        (prefix.with_suffix(".json")).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md = ["# Inter-coder Agreement", ""]
        for field, payload in report.items():
            md.append(f"## {field}")
            for key, value in payload.items():
                if key == "confusion_matrix":
                    continue
                md.append(f"- {key}: {value}")
            md.append("")
            confusion = payload.get("confusion_matrix")
            if isinstance(confusion, dict):
                matrix = pd.DataFrame(confusion).fillna(0)
                matrix.to_csv(prefix.parent / f"confusion_{field}.csv", encoding="utf-8")
        (prefix.with_suffix(".md")).write_text("\n".join(md), encoding="utf-8")
        print(f"Agreement report written: {prefix.with_suffix('.json')}")
        return

    if args.command == "segments":
        frame = _read_any_table(args.annotations)
        result = get_coded_segments(frame, args.code, args.field)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out, index=False, encoding="utf-8")
        print(f"Coded segments written: {out}")
        return

    if args.command == "matrix":
        frame = _read_any_table(args.annotations)
        result = code_matrix(frame, args.rows, args.columns, args.normalize)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out, index=False, encoding="utf-8")
        print(f"Matrix written: {out}")
        return

    if args.command == "report":
        frame = _read_any_table(args.annotations)
        export_manual_coding_report(frame, args.output)
        print(f"Report written: {args.output}")


def _read_any_table(path: str) -> pd.DataFrame:
    file = Path(path)
    if file.suffix.lower() == ".xlsx":
        return pd.read_excel(file)
    if file.suffix.lower() == ".parquet":
        return pd.read_parquet(file)
    return pd.read_csv(file)


if __name__ == "__main__":
    main()

