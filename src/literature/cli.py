from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from src.config import PipelineConfig

from .export import export_search_results
from .index import build_literature_index, _literature_config
from .search import search_literature


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


def _run_queries(config: PipelineConfig, literature: dict, queries_path: Path) -> None:
    payload = yaml.safe_load(queries_path.read_text(encoding="utf-8")) or {}
    output_dir = Path(config.output_dir) / "literature"
    for item in payload.get("queries", []):
        query_id = item["id"]
        query = f"{item.get('query_ru', '')} {item.get('query_en', '')}".strip()
        results = search_literature(query, literature["index_dir"], int(literature["top_k"]))
        export_search_results(results, query, output_dir, stem=query_id)


if __name__ == "__main__":
    main()
