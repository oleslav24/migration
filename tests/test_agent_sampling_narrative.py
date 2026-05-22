import json
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.agents.migration_narrative_agent import run_migration_narrative_agent
from src.agents.sampling_agent import MANUAL_COLUMNS, run_sampling_coding_agent
from src.agents.toponym_agent import run_toponym_urban_space_agent


def _contract(work_dir: Path) -> Path:
    path = work_dir / "contract.yaml"
    path.write_text(
        """
agent_id: test_agent
purpose: "Test local sampling and narrative agents."
task_contract: {inputs: [data], outputs: [report], invariants: [traceable]}
allowed_context:
  read: [data]
  write: [out, tmp_write_check]
  external: []
allowed_actions: []
forbidden_actions: []
quality_gates: {required_tests: []}
stop_conditions: {stop_on_failed_quality_gate: true, stop_on_access_violation: true, stop_on_empty_context: false}
audit_trail: {output_dir: out/audit}
feedback_sensors: {evidence_traceability: true}
access_model: {default_policy: deny}
threat_lens: {zero_trust: true}
metrics: {primary: [traceability]}
""".strip(),
        encoding="utf-8",
    )
    return path


def _write_docs(work_dir: Path) -> None:
    data = work_dir / "data"
    data.mkdir(parents=True)
    (data / "documents.csv").write_text(
        "datetime,source,group,text,sentiment,topic_id,migration_driver,toponyms\n"
        "2025-01-01,telegram,g1,visa documents in Bangkok,neutral,1,visa/legal,\"['Bangkok']\"\n"
        "2025-01-02,youtube,g2,remote work income in Phuket,positive,2,work/income,\"['Phuket']\"\n"
        "2025-01-03,telegram,g1,hard adaptation and language problem,negative,3,adaptation/problems,\"[]\"\n",
        encoding="utf-8",
    )


def test_sampling_reproducible_manual_columns_and_manifest():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    contract = _contract(work_dir)

    first = run_sampling_coding_agent(contract, work_dir, "out1", sample_size=2, random_state=4)
    second = run_sampling_coding_agent(contract, work_dir, "out2", sample_size=2, random_state=4)

    a = pd.read_csv(Path(first["output_dir"]) / "coding_sample.csv")
    b = pd.read_csv(Path(second["output_dir"]) / "coding_sample.csv")
    assert a["sample_id"].tolist() == b["sample_id"].tolist()
    assert not a.duplicated(subset=["source_path", "row_index"]).any()
    assert set(MANUAL_COLUMNS).issubset(a.columns)
    assert (Path(first["output_dir"]) / "coding_manifest.json").exists()


def test_sampling_by_toponym_exports_bridge_artifacts_and_manifest_params():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    contract = _contract(work_dir)

    run_toponym_urban_space_agent(
        contract,
        work_dir,
        "out_toponym",
        top_n_toponyms=2,
        samples_per_toponym=2,
        max_texts_per_toponym=50,
        random_state=42,
    )
    result = run_sampling_coding_agent(
        contract,
        work_dir,
        "out_sampling",
        sample_size=2,
        random_state=7,
        report_language="ru",
        toponym="Bangkok",
        stratify_by="source",
    )

    root = Path(result["output_dir"])
    assert (root / "coding_sample_by_toponym.csv").exists()
    assert (root / "coding_codebook_toponym.md").exists()
    assert (root / "coding_manifest_toponym.json").exists()
    sample = pd.read_csv(root / "coding_sample_by_toponym.csv")
    assert set(MANUAL_COLUMNS).issubset(sample.columns)
    manifest = (root / "coding_manifest_toponym.json").read_text(encoding="utf-8")
    assert '"toponym": "Bangkok"' in manifest
    assert '"stratify_by": "source"' in manifest


def test_sampling_by_toponym_is_reproducible_with_seed():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    contract = _contract(work_dir)

    run_toponym_urban_space_agent(
        contract,
        work_dir,
        "out_toponym",
        top_n_toponyms=3,
        samples_per_toponym=2,
        max_texts_per_toponym=50,
        random_state=42,
    )
    first = run_sampling_coding_agent(
        contract,
        work_dir,
        "out_sampling_1",
        sample_size=3,
        random_state=11,
        toponym="Bangkok",
        stratify_by="source",
    )
    second = run_sampling_coding_agent(
        contract,
        work_dir,
        "out_sampling_2",
        sample_size=3,
        random_state=11,
        toponym="Bangkok",
        stratify_by="source",
    )

    a = pd.read_csv(Path(first["output_dir"]) / "coding_sample_by_toponym.csv")
    b = pd.read_csv(Path(second["output_dir"]) / "coding_sample_by_toponym.csv")
    assert a["sample_id"].tolist() == b["sample_id"].tolist()


def test_sampling_by_toponym_normalizes_empty_source_values():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)
    contract = _contract(work_dir)

    toponym_result = run_toponym_urban_space_agent(
        contract,
        work_dir,
        "out_toponym",
        top_n_toponyms=3,
        samples_per_toponym=2,
        max_texts_per_toponym=50,
        random_state=42,
    )
    toponym_root = Path(toponym_result["output_dir"])
    manifest = json.loads((toponym_root / "texts_by_toponym_manifest.json").read_text(encoding="utf-8"))
    assert manifest["items"]
    item = manifest["items"][0]
    toponym_name = str(item["toponym"])
    table_path = toponym_root / item["path"]
    table = pd.read_csv(table_path)
    assert not table.empty
    table.loc[table.index[0], "source"] = ""
    table.loc[table.index[0], "source_path"] = "DS/telegram_comments_12.25.csv"
    if len(table) > 1:
        table.loc[table.index[1], "source"] = ""
        table.loc[table.index[1], "source_path"] = "unknown/path.csv"
    table.to_csv(table_path, index=False, encoding="utf-8")

    sampling_result = run_sampling_coding_agent(
        contract,
        work_dir,
        "out_sampling",
        sample_size=10,
        random_state=7,
        toponym=toponym_name,
        stratify_by="source",
    )

    sample = pd.read_csv(Path(sampling_result["output_dir"]) / "coding_sample_by_toponym.csv")
    assert not sample.empty
    assert sample["source"].fillna("").astype(str).str.strip().ne("").all()
    assert "telegram" in set(sample["source"].astype(str).str.lower())


def test_migration_narrative_evidence_ids_and_absent_status():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)

    result = run_migration_narrative_agent(_contract(work_dir), work_dir, "out")

    root = Path(result["output_dir"])
    report = (root / "migration_narrative_report.md").read_text(encoding="utf-8")
    matrix = pd.read_csv(root / "migration_narrative_matrix.csv")
    assert "narrative:" in report
    assert "absent evidence" in set(matrix["status"])
    assert "unsupported" not in report.lower()


def test_migration_narrative_report_supports_russian_language():
    work_dir = Path("tmp_write_check") / "agent_sprint_tests" / uuid4().hex
    _write_docs(work_dir)

    result = run_migration_narrative_agent(_contract(work_dir), work_dir, "out", report_language="ru")

    report = Path(result["report_path"]).read_text(encoding="utf-8")
    assert result["report_language"] == "ru"
    assert "# Отчет по миграционным нарративам" in report
    assert "## Количественное распределение" in report
