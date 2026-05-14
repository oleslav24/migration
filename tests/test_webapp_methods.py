from pathlib import Path
import json

import pytest

from src.webapp.app import (
    build_report_bundle,
    compare_run_manifests,
    evidence_payload,
    method_sample_payload,
    read_report,
    summary_payload,
    table_payload,
)


def test_method_sample_payload_runs_local_methods():
    payload = method_sample_payload("Bangkok condo rent is expensive near Sukhumvit")

    labels = {item["method"]: item["label"] for item in payload["results"]}
    assert labels["toponyms"]
    assert "Bangkok" in labels["toponyms"]
    assert labels["place_perception"] in {"affordability", "housing"}
    assert payload["normalized_text"] == "bangkok condo rent is expensive near sukhumvit"


def test_methods_summary_exposes_researcher_metadata():
    payload = summary_payload()
    methods = {item["id"]: item for item in payload["methods"]}

    assert "toponyms" in methods
    assert methods["toponyms"]["stage"] == "place extraction"
    assert methods["toponyms"]["quality_gates"]
    assert methods["toponyms"]["experiments"]
    assert payload["safety"]["execution_model"] == "registry-only experiments"
    assert "arbitrary shell commands from UI" in payload["safety"]["forbidden"]
    assert "experiment_outputs" in payload
    assert any(item["id"] == "migration_narratives" for item in payload["experiment_outputs"])
    for item in payload["experiment_outputs"]:
        assert {"reports", "evidence", "tables", "counts"}.issubset(item.keys())
        assert {"reports", "evidence", "tables"}.issubset(item["counts"].keys())


def test_webapp_language_pack_contains_ru_and_en():
    path = Path("src/webapp/static/i18n.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["ru"]["app.title"] == "Рабочее место исследователя миграции"
    assert data["en"]["app.title"] == "Migration Research Workspace"
    assert set(data["en"]) <= set(data["ru"])


def test_table_payload_filters_csv_preview():
    path = Path("tmp_write_check") / "webapp_table_test.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("id,text\n1,Bangkok visa\n2,Phuket beach\n", encoding="utf-8")

    payload = table_payload(str(path), "Bangkok", 10)

    assert payload["returned_rows"] == 1
    assert payload["rows"][0]["text"] == "Bangkok visa"


def test_table_payload_allows_dataset_preview_from_ds():
    files = list(Path("DS").glob("*.csv"))
    if not files:
        pytest.skip("No DS CSV files available for read-only dataset preview test.")

    payload = table_payload(str(files[0]), "", 10)

    assert "error" not in payload
    assert payload["returned_rows"] >= 0


def test_evidence_payload_filters_json_items():
    path = Path("tmp_write_check") / "webapp_evidence_test.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"evidence_items":[{"source_path":"telegram.csv","toponym":"Bangkok","sentiment":"negative","text":"visa problem"},{"source_path":"youtube.csv","toponym":"Phuket","sentiment":"positive","text":"beach"}]}',
        encoding="utf-8",
    )

    payload = evidence_payload(str(path), {"toponym": "Bangkok", "source": "telegram"}, 10)

    assert payload["total_rows"] == 2
    assert payload["returned_rows"] == 1
    assert payload["rows"][0]["text"] == "visa problem"


def test_compare_run_manifests_reports_parameter_differences():
    root = Path("tmp_write_check") / "webapp_manifest_test"
    a = root / "a" / "run_manifest.json"
    b = root / "b" / "run_manifest.json"
    a.parent.mkdir(parents=True, exist_ok=True)
    b.parent.mkdir(parents=True, exist_ok=True)
    a.write_text('{"experiment":{"id":"x","runner":"sampling"},"params":{"seed":1},"result":{"sample_size":5}}', encoding="utf-8")
    b.write_text('{"experiment":{"id":"x","runner":"sampling"},"params":{"seed":2},"result":{"sample_size":5}}', encoding="utf-8")

    payload = compare_run_manifests(str(a), str(b))

    fields = {item["field"] for item in payload["differences"]}
    assert "params" in fields


def test_build_report_bundle_creates_markdown():
    report = Path("tmp_write_check") / "webapp_report_source.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Source Report\n\nEvidence only.", encoding="utf-8")

    payload = build_report_bundle({"title": "Test bundle", "paths": [str(report)]})

    output = Path(payload["path"])
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "# Test bundle" in text
    assert "Source Report" in text


def test_read_report_allows_docs_markdown():
    path = Path("docs") / "toponym_research_workflow_plan.md"
    text = read_report(str(path))
    assert "Toponym Research Workflow" in text
