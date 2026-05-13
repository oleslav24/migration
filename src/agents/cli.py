from __future__ import annotations

import argparse
import json

from .corpus_agent import analyze_corpus_context, prepare_corpus_context
from .experiment_registry import inspect_experiment, load_registry, run_experiment
from .literature_bridge_agent import run_literature_bridge_agent
from .migration_narrative_agent import run_migration_narrative_agent
from .place_perception_agent import run_place_perception_agent
from .runtime import run_contract
from .sampling_agent import run_sampling_coding_agent
from .toponym_agent import run_toponym_urban_space_agent


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
    analyze_corpus.add_argument("--report-language", default="en", choices=["en", "ru"])

    toponyms = subparsers.add_parser("analyze-toponyms")
    toponyms.add_argument("--contract", required=True)
    toponyms.add_argument("--workspace", default=".")
    toponyms.add_argument("--output-root")
    toponyms.add_argument("--report-language", default="en", choices=["en", "ru"])

    place = subparsers.add_parser("analyze-place-perception")
    place.add_argument("--contract", required=True)
    place.add_argument("--workspace", default=".")
    place.add_argument("--output-root")
    place.add_argument("--report-language", default="en", choices=["en", "ru"])

    sampling = subparsers.add_parser("prepare-coding-sample")
    sampling.add_argument("--contract", required=True)
    sampling.add_argument("--workspace", default=".")
    sampling.add_argument("--output-root")
    sampling.add_argument("--sample-size", type=int, default=100)
    sampling.add_argument("--random-state", type=int, default=42)
    sampling.add_argument("--report-language", default="en", choices=["en", "ru"])

    narrative = subparsers.add_parser("analyze-migration-narratives")
    narrative.add_argument("--contract", required=True)
    narrative.add_argument("--workspace", default=".")
    narrative.add_argument("--output-root")
    narrative.add_argument("--report-language", default="en", choices=["en", "ru"])

    bridge = subparsers.add_parser("bridge-literature-corpus")
    bridge.add_argument("--contract", required=True)
    bridge.add_argument("--workspace", default=".")
    bridge.add_argument("--output-root")
    bridge.add_argument("--report-language", default="en", choices=["en", "ru"])

    list_experiments = subparsers.add_parser("list-experiments")
    list_experiments.add_argument("--registry", default="experiments/registry.yaml")

    inspect = subparsers.add_parser("inspect-experiment")
    inspect.add_argument("--id", required=True)
    inspect.add_argument("--registry", default="experiments/registry.yaml")

    run_exp = subparsers.add_parser("run-experiment")
    run_exp.add_argument("--id", required=True)
    run_exp.add_argument("--registry", default="experiments/registry.yaml")
    run_exp.add_argument("--workspace", default=".")
    run_exp.add_argument("--params", default="{}")

    args = parser.parse_args()
    if args.command == "prepare-context":
        pack = prepare_corpus_context(args.contract, args.workspace, args.output_root)
        print(f"context_pack_path={pack.get('context_pack_path')}")
        print(f"context_report_path={pack.get('context_report_path')}")
        print(f"datasets={len(pack.get('datasets', []))}")
        return
    if args.command == "analyze-corpus":
        result = analyze_corpus_context(args.contract, args.workspace, args.output_root, args.report_language)
        print(f"context_pack_path={result['context_pack'].get('context_pack_path')}")
        print(f"evidence_pack_path={result['evidence_pack'].get('evidence_pack_path')}")
        print(f"context_report_path={result.get('context_report_path')}")
        print(f"evidence_items={len(result['evidence_pack'].get('evidence_items', []))}")
        return
    if args.command == "analyze-toponyms":
        _print_result(run_toponym_urban_space_agent(args.contract, args.workspace, args.output_root, report_language=args.report_language))
        return
    if args.command == "analyze-place-perception":
        _print_result(run_place_perception_agent(args.contract, args.workspace, args.output_root, args.report_language))
        return
    if args.command == "prepare-coding-sample":
        _print_result(run_sampling_coding_agent(args.contract, args.workspace, args.output_root, args.sample_size, args.random_state, args.report_language))
        return
    if args.command == "analyze-migration-narratives":
        _print_result(run_migration_narrative_agent(args.contract, args.workspace, args.output_root, args.report_language))
        return
    if args.command == "bridge-literature-corpus":
        _print_result(run_literature_bridge_agent(args.contract, args.workspace, args.output_root, report_language=args.report_language))
        return
    if args.command == "list-experiments":
        print(json.dumps(load_registry(args.registry), ensure_ascii=False, indent=2))
        return
    if args.command == "inspect-experiment":
        print(json.dumps(inspect_experiment(args.id, args.registry), ensure_ascii=False, indent=2))
        return
    if args.command == "run-experiment":
        _print_result(run_experiment(args.id, args.registry, args.workspace, json.loads(args.params)))
        return
    result = run_contract(args.contract, args.workspace)
    print(f"status={result.status}")
    print(f"run_id={result.run_id}")
    print(f"audit_path={result.audit_path}")
    if result.report_path:
        print(f"report_path={result.report_path}")
    print(result.message)


def _print_result(result: dict) -> None:
    for key, value in result.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
