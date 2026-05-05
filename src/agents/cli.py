from __future__ import annotations

import argparse

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

    args = parser.parse_args()
    result = run_contract(args.contract, args.workspace)
    print(f"status={result.status}")
    print(f"run_id={result.run_id}")
    print(f"audit_path={result.audit_path}")
    if result.report_path:
        print(f"report_path={result.report_path}")
    print(result.message)


if __name__ == "__main__":
    main()
