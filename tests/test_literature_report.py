from pathlib import Path
from uuid import uuid4

from src.config import PipelineConfig
from src.literature.cli import summarize_all_tasks
from src.literature.report import export_summary_report


def test_export_summary_report_has_evidence_used():
    output = Path("tmp_write_check") / uuid4().hex / "summary.md"
    summary = {
        "title": "Test",
        "question_ru": "Вопрос",
        "question_en": "Question",
        "summary_ru": "Only evidence-based text.",
        "key_findings": ["Finding"],
        "concepts": ["concept"],
        "methods": [],
        "limitations": [],
        "relevance_for_project": "Relevant.",
        "evidence_used": [
            {
                "evidence_id": "E1",
                "filename": "a.md",
                "page_number": None,
                "chunk_index": 0,
                "score": 0.9,
                "text": "Excerpt text.",
            }
        ],
    }

    export_summary_report(summary, str(output))

    content = output.read_text(encoding="utf-8")
    assert "## Evidence used" in content
    assert "### E1" in content


def test_summarize_all_does_not_fail_with_empty_search_results():
    work_dir = Path("tmp_write_check") / uuid4().hex
    tasks_path = work_dir / "tasks.yaml"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(
        "tasks:\n"
        "  - id: empty\n"
        "    title: Empty\n"
        "    question_en: Missing index question\n",
        encoding="utf-8",
    )
    config = PipelineConfig.from_yaml("config.yaml")
    config.output_dir = str(work_dir / "output")
    config.literature["index_dir"] = str(work_dir / "missing_index")

    summaries = summarize_all_tasks(config, tasks_path)

    assert len(summaries) == 1
    assert (work_dir / "output" / "literature_summaries" / "empty.md").exists()
