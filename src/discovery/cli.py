from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import PipelineConfig
from src.literature.index import build_literature_index

from .deduplicate import deduplicate_candidates
from .downloader import download_pdf
from .export import candidates_from_csv, export_discovery_results
from .fulltext import find_pdf_url
from .models import ArticleCandidate, discovery_config, ensure_discovery_dirs
from .providers import ArxivProvider, CrossrefProvider, ManualSeedProvider, OpenAlexProvider, SemanticScholarProvider
from .queries import load_discovery_queries
from .scoring import score_candidate


LOGGER = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = argparse.ArgumentParser(description="Scholarly article discovery agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search")
    search.add_argument("--config", required=True)
    search.add_argument("--queries", required=True)

    download = subparsers.add_parser("download")
    download.add_argument("--config", required=True)
    download.add_argument("--candidates", required=True)

    run = subparsers.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--queries", required=True)
    run.add_argument("--reindex", action="store_true")

    seed = subparsers.add_parser("add-seed")
    seed.add_argument("--config", required=True)
    seed.add_argument("--seed", required=True)

    args = parser.parse_args()
    config = PipelineConfig.from_yaml(args.config)

    if args.command == "search":
        run_search(config, Path(args.queries))
    elif args.command == "download":
        run_download(config, Path(args.candidates))
    elif args.command == "run":
        selected = run_search(config, Path(args.queries))
        run_download(config, Path(discovery_config(config)["output_dir"]) / "selected_articles.csv")
        if args.reindex:
            build_literature_index(config)
        return
    elif args.command == "add-seed":
        add_seed(config, Path(args.seed))


def run_search(config: PipelineConfig, queries_path: Path) -> list[ArticleCandidate]:
    ensure_discovery_dirs(config)
    queries = load_discovery_queries(queries_path)
    providers = _providers(config)
    candidates: list[ArticleCandidate] = []
    for query in queries:
        for provider in providers:
            try:
                candidates.extend(provider.search(query, config))
            except Exception as exc:
                LOGGER.warning("Provider %s failed for query %s: %s", provider.name, query.get("id"), exc)

    deduped = deduplicate_candidates(candidates)
    query_by_id = {query["id"]: query for query in queries}
    scored: list[ArticleCandidate] = []
    for candidate in deduped:
        find_pdf_url(candidate, config)
        query = query_by_id.get(candidate.query_id, queries[0] if queries else {})
        scored.append(score_candidate(candidate, query, config))

    min_score = float(discovery_config(config)["relevance"].get("min_score", 0.45))
    selected = sorted([item for item in scored if (item.relevance_score or 0.0) >= min_score], key=_score, reverse=True)
    rejected = sorted([item for item in scored if (item.relevance_score or 0.0) < min_score], key=_score, reverse=True)
    export_discovery_results(scored, selected, rejected, config)
    LOGGER.info("Discovery search complete: %s candidates, %s selected", len(scored), len(selected))
    return selected


def run_download(config: PipelineConfig, candidates_path: Path):
    candidates = candidates_from_csv(candidates_path)
    limit = int(discovery_config(config)["max_pdf_downloads"])
    downloads = []
    for candidate in candidates[:limit]:
        find_pdf_url(candidate, config)
        downloads.append(download_pdf(candidate, config))
    selected = candidates
    rejected: list[ArticleCandidate] = []
    export_discovery_results(candidates, selected, rejected, config, downloads=downloads)
    LOGGER.info("Download complete: %s/%s PDFs", sum(item.downloaded for item in downloads), len(downloads))
    return downloads


def add_seed(config: PipelineConfig, seed_path: Path) -> list[ArticleCandidate]:
    provider = ManualSeedProvider(str(seed_path))
    query = {"id": "manual_seed", "required_terms": [], "optional_terms": []}
    candidates = [score_candidate(find_pdf_url(candidate, config), query, config) for candidate in provider.search(query, config)]
    selected = [candidate for candidate in candidates if candidate.title]
    export_discovery_results(candidates, selected, [], config)
    return selected


def _providers(config: PipelineConfig):
    enabled = discovery_config(config)["providers"]
    providers = []
    if enabled.get("crossref", True):
        providers.append(CrossrefProvider())
    if enabled.get("openalex", True):
        providers.append(OpenAlexProvider())
    if enabled.get("semantic_scholar", True):
        providers.append(SemanticScholarProvider())
    if enabled.get("arxiv", True):
        providers.append(ArxivProvider())
    if enabled.get("manual_seed", True):
        providers.append(ManualSeedProvider())
    return providers


def _score(candidate: ArticleCandidate) -> float:
    return float(candidate.relevance_score or 0.0)


if __name__ == "__main__":
    main()
