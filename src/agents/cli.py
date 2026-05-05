from __future__ import annotations

import argparse

from .corpus_agent import analyze_corpus_context, prepare_corpus_context
from .runtime import run_contract


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlled agent runtime for migration research tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-contract")
    validate.add_argument("--contract", required=True)
    validate.add_argument("--workspace", default=".")

    run = subparsers.add_parser("run")
    run.add_argument("--contract", required=True)
    run.add_argument("--workspace", default=".")

    prepare_context = subparsers.add_parser("prepare-context")
    prepare_context.add_argument("--contract", required=True)
    prepare_context.add_argument("--workspace", default=".")
    prepare_context.add_argument("--output-root")

    analyze_corpus = subparsers.add_parser("analyze-corpus")
    analyze_corpus.add_argument("--contract", required=True)
    analyze_corpus.add_argument("--workspace", default=".")
    analyze_corpus.add_argument("--output-root")

    args = parser.parse_args()
    if args.command == "prepare-context":
        pack = prepare_corpus_context(args.contract, args.workspace, args.output_root)
        print(f"context_pack_path={pack.get('context_pack_path')}")
        print(f"context_report_path={pack.get('context_report_path')}")
        print(f"datasets={len(pack.get('datasets', []))}")
        return
    if args.command == "analyze-corpus":
        result = analyze_corpus_context(args.contract, args.workspace, args.output_root)
        print(f"context_pack_path={result['context_pack'].get('context_pack_path')}")
        print(f"evidence_pack_path={result['evidence_pack'].get('evidence_pack_path')}")
        print(f"context_report_path={result.get('context_report_path')}")
        print(f"evidence_items={len(result['evidence_pack'].get('evidence_items', []))}")
        return
    result = run_contract(args.contract, args.workspace)
    print(f"status={result.status}")
    print(f"run_id={result.run_id}")
    print(f"audit_path={result.audit_path}")
    if result.report_path:
        print(f"report_path={result.report_path}")
    print(result.message)


if __name__ == "__main__":
    main()
