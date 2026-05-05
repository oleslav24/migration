from pathlib import Path
from uuid import uuid4

from src.agents.corpus_agent import analyze_corpus_context, prepare_corpus_context
from src.agents.context_pack import prepare_context_pack
from src.agents.evidence_pack import build_evidence_pack


def _write_contract(work_dir: Path, read_paths: list[str], write_paths: list[str] | None = None) -> Path:
    path = work_dir / "contract.yaml"
    read_yaml = "\n".join(f"    - {item}" for item in read_paths)
    write_yaml = "\n".join(f"    - {item}" for item in (write_paths or ["agent_output", "tmp_write_check"]))
    path.write_text(
        f"""
agent_id: test_corpus_agent
purpose: "Prepare context pack for tests."
task_contract:
  inputs:
    - local corpus
  outputs:
    - context_pack.json
    - evidence_pack.json
    - context_report.md
  invariants:
    - evidence keeps source paths
allowed_context:
  read:
{read_yaml}
  write:
{write_yaml}
  external: []
allowed_actions:
  - "python -m pytest tests/test_agent_context_pack.py"
forbidden_actions:
  - web search
quality_gates:
  required_tests: []
stop_conditions:
  stop_on_failed_quality_gate: true
  stop_on_access_violation: true
  stop_on_empty_context: false
audit_trail:
  output_dir: agent_output/audit
feedback_sensors:
  context_coverage: true
access_model:
  default_policy: deny
threat_lens:
  zero_trust: true
metrics:
  primary:
    - source_traceability
""".strip(),
        encoding="utf-8",
    )
    return path


def test_prepare_context_pack_discovers_dataset_and_schema():
    work_dir = Path("tmp_write_check") / "agent_context_tests" / uuid4().hex
    data_dir = work_dir / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "comments.csv").write_text(
        "datetime,source,group,comment\n"
        "2025-01-01T00:00:00Z,telegram,g1,hello bangkok\n"
        "2025-01-02T00:00:00Z,youtube,g2,phuket work visa\n",
        encoding="utf-8",
    )
    contract_path = _write_contract(work_dir, ["data"], ["agent_output", "tmp_write_check"])

    pack = prepare_context_pack(contract_path, work_dir, "agent_output")

    assert pack["datasets"]
    assert pack["datasets"][0]["row_count"] == 2
    assert "comment" in pack["datasets"][0]["columns"]
    assert Path(pack["context_pack_path"]).exists()


def test_evidence_pack_contains_source_paths_and_text_samples():
    work_dir = Path("tmp_write_check") / "agent_context_tests" / uuid4().hex
    data_dir = work_dir / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "documents_enriched.csv").write_text(
        "datetime,source,group,text,language,sentiment,topic_id,toponyms\n"
        "2025-01-01T00:00:00Z,telegram,g1,visa questions in Bangkok,en,neutral,0,\"['bangkok']\"\n"
        "2025-01-02T00:00:00Z,youtube,g2,Phuket housing and work,en,positive,1,\"['phuket']\"\n",
        encoding="utf-8",
    )
    contract_path = _write_contract(work_dir, ["data"], ["agent_output", "tmp_write_check"])
    context_pack = prepare_context_pack(contract_path, work_dir, "agent_output")

    evidence_pack = build_evidence_pack(contract_path, context_pack, work_dir, "agent_output")

    assert evidence_pack["evidence_items"]
    assert evidence_pack["evidence_items"][0]["source_path"]
    assert evidence_pack["aggregate_items"]
    assert Path(evidence_pack["evidence_pack_path"]).exists()


def test_analyze_corpus_writes_markdown_report():
    work_dir = Path("tmp_write_check") / "agent_context_tests" / uuid4().hex
    data_dir = work_dir / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "comments.csv").write_text(
        "datetime,source,group,comment\n"
        "2025-01-01T00:00:00Z,telegram,g1,chiang mai adaptation problems\n",
        encoding="utf-8",
    )
    contract_path = _write_contract(work_dir, ["data"], ["agent_output", "tmp_write_check"])

    result = analyze_corpus_context(contract_path, work_dir, "agent_output")

    report_path = Path(result["context_report_path"])
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "## Datasets" in report
    assert "Source:" in report


def test_empty_context_returns_explicit_limitation():
    work_dir = Path("tmp_write_check") / "agent_context_tests" / uuid4().hex
    empty_dir = work_dir / "empty"
    empty_dir.mkdir(parents=True)
    contract_path = _write_contract(work_dir, ["empty"], ["agent_output", "tmp_write_check"])

    pack = prepare_corpus_context(contract_path, work_dir, "agent_output")

    assert pack["datasets"] == []
    assert "No readable local context files were discovered." in pack["limitations"]

