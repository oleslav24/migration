from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.agents.place_perception_agent import classify_place_perception, run_place_perception_agent
from src.agents.toponym_agent import run_toponym_urban_space_agent


def _contract(work_dir: Path) -> Path:
    path = work_dir / "contract.yaml"
    path.write_text(
        """
agent_id: test_agent
purpose: "Test local research agent."
task_contract:
  inputs: [data]
  outputs: [report]
  invariants: [source paths preserved]
allowed_context:
  read: [data]
  write: [out, tmp_write_check]
  external: []
allowed_actions: []
forbidden_actions: [web search]
quality_gates:
  required_tests: []
stop_conditions:
  stop_on_failed_quality_gate: true
  stop_on_access_violation: true
  stop_on_empty_context: false
audit_trail: {output_dir: out/audit}
feedback_sensors: {evidence_traceability: true}
access_model: {default_policy: deny}
threat_lens: {zero_trust: true}
metrics:
  primary: [source_traceability]
""".strip(),
        encoding="utf-8",
    )
    return path


def _write_docs(work_dir: Path) -> None:
    data = work_dir / "data"
    data.mkdir(parents=True)
    (data / "documents_enriched.csv").write_text(
        "datetime,source,group,text,sentiment,topic_id,migration_driver,toponyms\n"
        "2025-01-01,telegram,g1,Bangkok visa and condo is expensive,negative,1,visa/legal,\"['Bangkok','Sukhumvit']\"\n"
        "2025-01-02,youtube,g2,Phuket has safe beach community,positive,2,climate/lifestyle,\"['Phuket','Patong']\"\n"
        "2025-01-03,telegram,g1,Bangkok traffic near Sukhumvit is difficult,negative,1,adaptation/problems,\"['Sukhumvit']\"\n",
        encoding="utf-8",
    )


def test_toponym_evidence_contains_source_paths_and_city_stats():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    result = run_toponym_urban_space_agent(_contract(work_dir), work_dir, "out", random_state=7)

    root = Path(result["output_dir"])
    evidence = (root / "toponym_evidence_pack.json").read_text(encoding="utf-8")
    assert "source_path" in evidence
    city_stats = pd.read_csv(root / "city_level_stats.csv")
    assert "Bangkok" in set(city_stats["parent_city"])
    assert (root / "texts_by_toponym_manifest.json").exists()


def test_toponym_sampling_is_deterministic():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    contract = _contract(work_dir)
    first = run_toponym_urban_space_agent(contract, work_dir, "out1", random_state=11)
    second = run_toponym_urban_space_agent(contract, work_dir, "out2", random_state=11)

    a = (Path(first["output_dir"]) / "toponym_samples.csv").read_text(encoding="utf-8")
    b = (Path(second["output_dir"]) / "toponym_samples.csv").read_text(encoding="utf-8")
    assert a == b


def test_toponym_research_workflow_exports_texts_and_hypothesis_report():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)

    result = run_toponym_urban_space_agent(
        _contract(work_dir),
        work_dir,
        "out",
        random_state=5,
        report_language="ru",
        hypothesis="Какие районы Бангкока связаны с визами и жильем?",
        dataset_scope="telegram",
        top_n_toponyms=2,
        samples_per_toponym=1,
        max_texts_per_toponym=10,
    )

    root = Path(result["output_dir"])
    report = Path(result["report_path"]).read_text(encoding="utf-8")
    manifest = (root / "toponym_research_manifest.json").read_text(encoding="utf-8")
    assert "Исследовательская гипотеза" in report
    assert "Какие районы Бангкока" in report
    assert "texts_by_toponym" in manifest
    assert list((root / "texts_by_toponym").glob("*.csv"))


def test_no_toponym_corpus_returns_limitation():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    data = work_dir / "data"
    data.mkdir(parents=True)
    (data / "documents.csv").write_text("text\nno place here\n", encoding="utf-8")

    result = run_toponym_urban_space_agent(_contract(work_dir), work_dir, "out")

    assert result["evidence_items"] == 0
    assert "No toponyms" in result["limitations"][0]


def test_place_perception_classifier_and_report_examples():
    assert classify_place_perception("Bangkok condo rent is expensive") == "affordability"
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)

    result = run_place_perception_agent(_contract(work_dir), work_dir, "out")

    root = Path(result["output_dir"])
    assert (root / "place_perception_distribution.csv").exists()
    report = (root / "place_perception_report.md").read_text(encoding="utf-8")
    assert "Evidence snippets" in report
    assert "Source:" in report
