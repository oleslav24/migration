from pathlib import Path
from uuid import uuid4

from src.discovery.deduplicate import deduplicate_candidates
from src.discovery.export import export_discovery_results
from src.discovery.models import ArticleCandidate
from src.discovery.providers.manual_seed import ManualSeedProvider
from src.discovery.scoring import score_candidate


def test_deduplicate_by_doi_and_title():
    candidates = [
        ArticleCandidate("a", "crossref", "q", "Digital Traces Migration", doi="10.1/test"),
        ArticleCandidate("b", "openalex", "q", "Other title", doi="10.1/TEST", pdf_url="https://example.org/a.pdf"),
        ArticleCandidate("c", "crossref", "q", "Urban Space Representation"),
        ArticleCandidate("d", "openalex", "q", "urban space: representation"),
    ]

    result = deduplicate_candidates(candidates)

    assert len(result) == 2
    doi_item = next(item for item in result if item.doi)
    assert doi_item.pdf_url == "https://example.org/a.pdf"
    assert set(doi_item.metadata["sources"]) == {"crossref", "openalex"}


def test_score_candidate_has_reason():
    query = {
        "required_terms": ["migration", "social media"],
        "optional_terms": ["digital traces"],
    }
    candidate = ArticleCandidate(
        "a",
        "openalex",
        "q",
        "Digital traces and migration decisions in social media",
        abstract="The article studies migration and social media communities.",
        year=2024,
        citation_count=25,
        open_access=True,
    )

    scored = score_candidate(candidate, query, {"discovery": {"year_from": 2015, "year_to": 2026}})

    assert scored.relevance_score and scored.relevance_score > 0.45
    assert "matched required terms" in scored.reason


def test_manual_seed_provider_reads_sources():
    work_dir = Path("tmp_write_check") / uuid4().hex
    seed_path = work_dir / "seed.yaml"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(
        "sources:\n"
        "  - id: s1\n"
        "    title: Manual migration article\n"
        "    doi: 10.1/manual\n"
        "    pdf_url: https://example.org/manual.pdf\n"
        "    note: Found manually in Google Scholar\n",
        encoding="utf-8",
    )

    candidates = ManualSeedProvider(str(seed_path)).search({"id": "seed"}, {})

    assert len(candidates) == 1
    assert candidates[0].open_access is True
    assert candidates[0].metadata["note"] == "Found manually in Google Scholar"


def test_export_discovery_results_creates_report():
    work_dir = Path("tmp_write_check") / uuid4().hex
    config = {
        "discovery": {
            "output_dir": str(work_dir / "data"),
            "articles_dir": str(work_dir / "pdf"),
            "metadata_dir": str(work_dir / "metadata"),
        }
    }
    candidate = ArticleCandidate("a", "manual_seed", "q", "Selected article", relevance_score=0.8, open_access=True)

    export_discovery_results([candidate], [candidate], [], config)

    assert (work_dir / "data" / "candidates.csv").exists()
    assert (work_dir / "data" / "selected_articles.csv").exists()
    assert "# Article Discovery Report" in (work_dir / "data" / "discovery_report.md").read_text(encoding="utf-8")
