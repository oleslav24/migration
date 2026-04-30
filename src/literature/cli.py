from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from src.config import PipelineConfig

from .evidence import collect_evidence, filter_evidence
from .export import export_search_results
from .index import build_literature_index, _literature_config
from .report import export_summary_json, export_summary_report
from .search import search_literature
from .summarizer import summarize_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Local literature retrieval for migration research.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-index")
    build.add_argument("--config", required=True)

    search = subparsers.add_parser("search")
    search.add_argument("--config", required=True)
    search.add_argument("--query", required=True)

    run_queries = subparsers.add_parser("run-queries")
    run_queries.add_argument("--config", required=True)
    run_queries.add_argument("--queries", required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("--config", required=True)
    summarize.add_argument("--task", required=True)
    summarize.add_argument("--tasks", default="queries/summarization_tasks.yaml")

    summarize_all = subparsers.add_parser("summarize-all")
    summarize_all.add_argument("--config", required=True)
    summarize_all.add_argument("--tasks", required=True)

    args = parser.parse_args()
    config = PipelineConfig.from_yaml(args.config)
    literature = _literature_config(config)

    if args.command == "build-index":
        build_literature_index(config)
        return
    if args.command == "search":
        results = search_literature(args.query, literature["index_dir"], int(literature["top_k"]))
        export_search_results(results, args.query, config.output_dir)
        print(results.to_string(index=False))
        return
    if args.command == "run-queries":
        _run_queries(config, literature, Path(args.queries))
        return
    if args.command == "summarize":
        task = _load_task(Path(args.tasks), args.task)
        summary = run_summary_task(config, task)
        print(f"Summary written: {Path(config.output_dir) / 'literature_summaries' / (task['id'] + '.md')}")
        return
    if args.command == "summarize-all":
        summarize_all_tasks(config, Path(args.tasks))
        return


def _run_queries(config: PipelineConfig, literature: dict, queries_path: Path) -> None:
    payload = yaml.safe_load(queries_path.read_text(encoding="utf-8")) or {}
    output_dir = Path(config.output_dir) / "literature"
    for item in payload.get("queries", []):
        query_id = item["id"]
        query = f"{item.get('query_ru', '')} {item.get('query_en', '')}".strip()
        results = search_literature(query, literature["index_dir"], int(literature["top_k"]))
        export_search_results(results, query, output_dir, stem=query_id)


def run_summary_task(config: PipelineConfig, task: dict) -> dict:
    literature = _literature_config(config)
    summarization = literature.get("summarization", {})
    top_k = int(literature.get("top_k", 8))
    max_items = int(summarization.get("max_evidence_items", 20))
    evidence = collect_evidence(task, config, top_k=max(top_k, max_items))
    evidence = filter_evidence(evidence, max_items=max_items)
    summary = summarize_task(task, evidence, config)
    output_dir = Path(config.output_dir) / "literature_summaries"
    export_summary_report(summary, str(output_dir / f"{task.get('id', 'manual_task')}.md"))
    export_summary_json(summary, str(output_dir / f"{task.get('id', 'manual_task')}.json"))
    return summary


def summarize_all_tasks(config: PipelineConfig, tasks_path: Path) -> list[dict]:
    payload = yaml.safe_load(tasks_path.read_text(encoding="utf-8")) or {}
    summaries: list[dict] = []
    for task in payload.get("tasks", []):
        summaries.append(run_summary_task(config, task))
    return summaries


def _load_task(tasks_path: Path, task_id: str) -> dict:
    payload = yaml.safe_load(tasks_path.read_text(encoding="utf-8")) or {}
    for task in payload.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise ValueError(f"Task not found: {task_id}")


if __name__ == "__main__":
    main()
