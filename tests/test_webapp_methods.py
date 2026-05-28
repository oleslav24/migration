import os
from pathlib import Path
import json
import time

import pytest

import src.webapp.app as webapp_module
from src.webapp.app import (
    _load_manifest_summary,
    _experiment_outputs_payload,
    build_report_bundle,
    build_run_packet,
    build_run_comparison,
    compare_run_manifests,
    evidence_payload,
    method_sample_payload,
    read_report,
    run_comparison_candidates,
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
        assert {"reports", "evidence", "tables", "counts", "key_table", "key_evidence"}.issubset(item.keys())
        assert {"reports", "evidence", "tables"}.issubset(item["counts"].keys())


def test_research_story_outputs_include_linked_step_artifacts(monkeypatch):
    unique_id = f"webapp_e2e_linked_{int(time.time() * 1_000_000)}"
    root = Path("tmp_write_check") / unique_id
    story_dir = root / "research_story_e2e"
    toponym_dir = root / "toponym"
    narrative_dir = root / "narrative"
    sampling_dir = root / "sampling"
    story_dir.mkdir(parents=True, exist_ok=True)
    toponym_dir.mkdir(parents=True, exist_ok=True)
    narrative_dir.mkdir(parents=True, exist_ok=True)
    sampling_dir.mkdir(parents=True, exist_ok=True)

    (story_dir / "research_story_e2e_report.md").write_text("# story\n", encoding="utf-8")
    (story_dir / "research_story_e2e_steps.csv").write_text("step,report_path,output_dir,evidence_items\n", encoding="utf-8")
    (story_dir / "research_story_e2e_summary.json").write_text(
        json.dumps(
            {
                "steps": [
                    {"step": "toponym", "report_path": str(toponym_dir / "toponym_research_report.md"), "output_dir": str(toponym_dir)},
                    {"step": "migration_narrative", "report_path": str(narrative_dir / "migration_narrative_report.md"), "output_dir": str(narrative_dir)},
                    {"step": "sampling", "report_path": "", "output_dir": str(sampling_dir)},
                ],
                "outputs": {
                    "steps_csv": str(story_dir / "research_story_e2e_steps.csv"),
                    "coding_sample": str(sampling_dir / "coding_sample_by_toponym.csv"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (toponym_dir / "toponym_research_report.md").write_text("# toponym\n", encoding="utf-8")
    (toponym_dir / "toponym_frequency.csv").write_text("toponym,count\nBangkok,4\n", encoding="utf-8")
    (narrative_dir / "migration_narrative_report.md").write_text("# narrative\n", encoding="utf-8")
    (narrative_dir / "migration_narrative_matrix.csv").write_text("driver,count\nvisa/legal,2\n", encoding="utf-8")
    (sampling_dir / "coding_sample_by_toponym.csv").write_text("text,toponym\nx,Bangkok\n", encoding="utf-8")

    manifest = {
        "experiment_id": "research_story_e2e",
        "path": str(story_dir / "run_manifest.json"),
        "output_dir": str(story_dir),
        "report_path": str(story_dir / "research_story_e2e_report.md"),
        "params": {},
        "manifest_mtime": time.time(),
    }

    monkeypatch.setattr(webapp_module, "_run_manifests_payload", lambda: [manifest])
    outputs = _experiment_outputs_payload([{"id": "research_story_e2e", "title": "Story", "runner": "research-story-e2e"}])

    assert len(outputs) == 1
    output = outputs[0]
    table_names = {item["name"] for item in output["tables"]}
    report_names = {item["name"] for item in output["reports"]}
    assert "research_story_e2e_steps.csv" in table_names
    assert "migration_narrative_matrix.csv" in table_names
    assert "coding_sample_by_toponym.csv" in table_names
    assert "toponym_research_report.md" in report_names
    assert output["key_table"] is not None
    assert output["key_table"]["name"] == "research_story_e2e_steps.csv"


def test_webapp_language_pack_contains_ru_and_en():
    path = Path("src/webapp/static/i18n.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["ru"]["app.title"] == "Рабочее место исследователя миграции"
    assert data["en"]["app.title"] == "Migration Research Workspace"
    assert set(data["en"]) <= set(data["ru"])
    assert data["en"]["label.run"] == "Run"
    assert data["en"]["section.run_focused_result"] == "Run-focused result"
    assert data["en"]["section.next_research_action"] == "Next research action"
    assert data["en"]["section.research_readiness"] == "Research readiness checklist"
    assert data["en"]["section.run_comparison_board"] == "Run comparison board"
    assert data["en"]["section.run_timeline"] == "Run timeline"
    assert data["en"]["section.evidence_digest"] == "Evidence digest"
    assert data["en"]["section.research_story_e2e"] == "One-click research story (E2E)"
    assert data["en"]["button.current_run"] == "Current run"
    assert data["en"]["button.open_manual_coding"] == "Open manual coding step"
    assert data["en"]["button.open_e2e_summary"] == "Open E2E summary"
    assert data["en"]["button.open_result_pack"] == "Open result pack"
    assert data["en"]["button.open_run_log"] == "Open run log"
    assert data["en"]["text.started_at"] == "Started"
    assert data["en"]["text.finished_at"] == "Finished"
    assert data["en"]["text.ready"] == "ready"
    assert data["en"]["text.missing"] == "missing"
    assert data["en"]["text.readiness_score"] == "Readiness score"
    assert data["en"]["text.next_action_missing"] == "The next required artifact is missing."
    assert data["en"]["text.next_action_ready"] == "Checklist is complete. Continue with synthesis and manual coding review."
    assert data["en"]["text.next_action_running"] == "Run is still in progress. Wait for completion and inspect the run log if needed."
    assert data["en"]["text.next_action_failed"] == "Run failed. Inspect the run log and relaunch the failed step."
    assert data["en"]["text.compare_current"] == "Current"
    assert data["en"]["text.compare_previous"] == "Previous"
    assert data["en"]["text.baseline_run"] == "Baseline run"
    assert data["en"]["text.changed_tables"] == "Changed tables"
    assert data["en"]["text.difference_count"] == "Differences"
    assert data["en"]["text.comparison_loading"] == "Loading comparison board..."
    assert data["en"]["text.comparison_updating"] == "Updating comparison..."
    assert data["en"]["text.comparison_no_baseline"] == "No previous run baseline is available yet."
    assert data["en"]["text.comparison_failed"] == "Failed to build comparison board."
    assert data["en"]["text.no_evidence_digest"]
    assert data["en"]["checklist.primary_report"] == "Primary report is available"
    assert data["en"]["checklist.toponym_frequency"] == "Toponym frequency table is available"
    assert data["en"]["checklist.narrative_matrix"] == "Migration narrative matrix is available"
    assert data["en"]["checklist.coding_sample"] == "Coding sample is available"
    assert data["en"]["message.result_pack_opened"] == "Result pack opened"
    assert data["en"]["message.result_pack_not_ready"] == "Result pack is not ready yet."
    assert data["en"]["metric.toponym_frequency"] == "Toponym frequency"
    assert data["en"]["metric.migration_driver_distribution"] == "Migration drivers"
    assert data["en"]["metric.sentiment_per_toponym"] == "Sentiment per toponym"
    assert data["en"]["metric.topics_per_toponym"] == "Topics per toponym"
    assert data["en"]["delta.up"] == "up"
    assert data["en"]["delta.down"] == "down"
    assert data["en"]["delta.same"] == "no change"
    assert data["en"]["delta.missing"] == "n/a"
    assert "label.run" in data["ru"]
    assert "section.run_focused_result" in data["ru"]
    assert "section.next_research_action" in data["ru"]
    assert "section.research_readiness" in data["ru"]
    assert "section.run_comparison_board" in data["ru"]
    assert "section.run_timeline" in data["ru"]
    assert "section.evidence_digest" in data["ru"]
    assert "section.research_story_e2e" in data["ru"]
    assert "button.current_run" in data["ru"]
    assert "button.open_manual_coding" in data["ru"]
    assert "button.open_e2e_summary" in data["ru"]
    assert "button.open_result_pack" in data["ru"]
    assert "button.open_run_log" in data["ru"]
    assert "message.result_pack_opened" in data["ru"]
    assert "message.result_pack_not_ready" in data["ru"]
    assert "text.ready" in data["ru"]
    assert "text.missing" in data["ru"]
    assert "text.readiness_score" in data["ru"]
    assert "text.next_action_missing" in data["ru"]
    assert "text.next_action_ready" in data["ru"]
    assert "text.next_action_running" in data["ru"]
    assert "text.next_action_failed" in data["ru"]
    assert "text.compare_current" in data["ru"]
    assert "text.compare_previous" in data["ru"]
    assert "text.baseline_run" in data["ru"]
    assert "text.changed_tables" in data["ru"]
    assert "text.difference_count" in data["ru"]
    assert "text.comparison_loading" in data["ru"]
    assert "text.comparison_updating" in data["ru"]
    assert "text.comparison_no_baseline" in data["ru"]
    assert "text.comparison_failed" in data["ru"]
    assert "checklist.primary_report" in data["ru"]
    assert "checklist.toponym_frequency" in data["ru"]
    assert "checklist.narrative_matrix" in data["ru"]
    assert "checklist.coding_sample" in data["ru"]
    assert "metric.toponym_frequency" in data["ru"]
    assert "metric.migration_driver_distribution" in data["ru"]
    assert "metric.sentiment_per_toponym" in data["ru"]
    assert "metric.topics_per_toponym" in data["ru"]
    assert "delta.up" in data["ru"]
    assert "delta.down" in data["ru"]
    assert "delta.same" in data["ru"]
    assert "delta.missing" in data["ru"]


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
    assert "params.seed" in fields


def test_run_comparison_candidates_returns_current_and_baselines(monkeypatch):
    manifests = [
        {"experiment_id": "exp_a", "path": "tmp_write_check/a.json", "run_id": "run_a", "manifest_mtime": 30.0, "params": {"hypothesis": "A"}},
        {"experiment_id": "exp_a", "path": "tmp_write_check/b.json", "run_id": "run_b", "manifest_mtime": 20.0, "params": {"hypothesis": "B"}},
        {"experiment_id": "exp_a", "path": "tmp_write_check/c.json", "run_id": "run_c", "manifest_mtime": 10.0, "params": {"hypothesis": "C"}},
        {"experiment_id": "exp_other", "path": "tmp_write_check/d.json", "run_id": "run_d", "manifest_mtime": 40.0, "params": {"hypothesis": "D"}},
    ]
    monkeypatch.setattr(webapp_module, "_run_manifests_payload", lambda: manifests)

    payload = run_comparison_candidates("exp_a", run_id="run_b", limit=2)

    assert payload["experiment_id"] == "exp_a"
    assert payload["current"]["run_id"] == "run_b"
    assert payload["current"]["path"] == "tmp_write_check/b.json"
    assert len(payload["baselines"]) == 2
    assert payload["baselines"][0]["run_id"] == "run_a"
    assert payload["baselines"][1]["run_id"] == "run_c"


def test_load_manifest_summary_accepts_utf8_bom():
    path = Path("tmp_write_check") / "webapp_manifest_bom" / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"experiment":{"id":"bom_case","title":"BOM","runner":"sampling"},"params":{"seed":1},"result":{"sample_size":5}}',
        encoding="utf-8-sig",
    )

    payload = _load_manifest_summary(str(path))

    assert "error" not in payload
    assert payload["experiment_id"] == "bom_case"
    assert payload["sample_size"] == 5


def test_load_manifest_summary_reads_web_run_metadata():
    path = Path("tmp_write_check") / "web_runs" / "manifests" / "12345_exp" / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "_web_run": {"run_id": "12345_exp"},
                "experiment": {"id": "meta_case", "title": "Meta", "runner": "sampling"},
                "params": {"seed": 1},
                "result": {"sample_size": 10},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = _load_manifest_summary(str(path))

    assert "error" not in payload
    assert payload["run_id"] == "12345_exp"
    assert payload["experiment_id"] == "meta_case"


def test_build_run_comparison_exports_markdown_json_and_csv():
    unique_id = f"webapp_comparison_{int(time.time() * 1_000_000)}"
    root = Path("tmp_write_check") / unique_id
    output_a = root / "run_a_output"
    output_b = root / "run_b_output"
    export_dir = root / "comparison"
    manifest_a = root / "run_a" / "run_manifest.json"
    manifest_b = root / "run_b" / "run_manifest.json"
    output_a.mkdir(parents=True, exist_ok=True)
    output_b.mkdir(parents=True, exist_ok=True)
    manifest_a.parent.mkdir(parents=True, exist_ok=True)
    manifest_b.parent.mkdir(parents=True, exist_ok=True)
    (output_a / "toponym_research_report.md").write_text("# Run A\n", encoding="utf-8")
    (output_b / "toponym_research_report.md").write_text("# Run B\n", encoding="utf-8")
    (output_a / "toponym_frequency.csv").write_text("toponym,count\nBangkok,10\nPhuket,3\n", encoding="utf-8")
    (output_b / "toponym_frequency.csv").write_text("toponym,count\nBangkok,6\nChiang Mai,4\n", encoding="utf-8")
    manifest_a.write_text(
        json.dumps(
            {
                "experiment": {"id": unique_id, "title": "Run A", "runner": "toponym-agent"},
                "params": {"hypothesis": "A", "top_n_toponyms": 10},
                "result": {
                    "output_dir": str(output_a).replace("/", "\\"),
                    "report_path": str((output_a / "toponym_research_report.md")).replace("/", "\\"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest_b.write_text(
        json.dumps(
            {
                "experiment": {"id": unique_id, "title": "Run B", "runner": "toponym-agent"},
                "params": {"hypothesis": "B", "top_n_toponyms": 20},
                "result": {
                    "output_dir": str(output_b).replace("/", "\\"),
                    "report_path": str((output_b / "toponym_research_report.md")).replace("/", "\\"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = build_run_comparison({"a": str(manifest_a), "b": str(manifest_b), "output_dir": str(export_dir)})

    assert "error" not in payload
    assert payload["difference_count"] >= 3
    markdown = Path(payload["paths"]["markdown"])
    json_path = Path(payload["paths"]["json"])
    csv_path = Path(payload["paths"]["csv"])
    assert markdown.exists()
    assert json_path.exists()
    assert csv_path.exists()
    text = markdown.read_text(encoding="utf-8")
    assert "# Run Comparison:" in text
    assert "toponym_frequency.csv" in text
    assert "Bangkok=10" in text
    assert "Bangkok=6" in text
    top_row = next((item for item in payload["comparison"]["table_comparisons"] if item.get("table") == "toponym_frequency.csv"), {})
    assert top_row.get("a", {}).get("top_value") == 10.0
    assert top_row.get("b", {}).get("top_value") == 6.0


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


def test_build_run_packet_creates_markdown_with_manifest_params_and_artifacts():
    unique_id = f"webapp_packet_{int(time.time() * 1_000_000)}"
    root = Path("tmp_write_check") / unique_id
    output_dir = root / "agent_output"
    packet_dir = root / "packets"
    manifest = root / "manifest" / "run_manifest.json"
    report = output_dir / "toponym_research_report.md"
    table = output_dir / "toponym_frequency.csv"
    evidence = output_dir / "toponym_evidence_pack.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Toponym Report\n\nEvidence.", encoding="utf-8")
    table.write_text("toponym,count\nBangkok,2\n", encoding="utf-8")
    evidence.write_text('{"evidence_items":[{"text":"Bangkok visa"}]}', encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "experiment": {"id": unique_id, "title": "Packet test", "runner": "toponym-agent"},
                "params": {"hypothesis": "Bangkok is central", "top_n_toponyms": 10},
                "result": {
                    "output_dir": str(output_dir).replace("/", "\\"),
                    "report_path": str(report).replace("/", "\\"),
                    "evidence_items": 1,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = build_run_packet({"manifest_path": str(manifest), "output_dir": str(packet_dir)})

    assert "error" not in payload
    packet = Path(payload["path"])
    assert packet.exists()
    text = packet.read_text(encoding="utf-8")
    assert "# Run Packet: Packet test" in text
    assert "Bangkok is central" in text
    assert "toponym_research_report.md" in text
    assert "toponym_frequency.csv" in text
    assert payload["manifest_path"].endswith("run_manifest.json")


def test_read_report_allows_docs_markdown():
    path = Path("docs") / "toponym_research_workflow_plan.md"
    text = read_report(str(path))
    assert "Toponym Research Workflow" in text


def test_experiment_outputs_uses_latest_manifest():
    unique_id = f"webapp_latest_{int(time.time() * 1_000_000)}"
    base = Path("tmp_write_check") / unique_id
    older_output = base / "older_output"
    newer_output = base / "newer_output"
    older_manifest = base / "older_manifest" / "run_manifest.json"
    newer_manifest = base / "newer_manifest" / "run_manifest.json"
    older_output.mkdir(parents=True, exist_ok=True)
    newer_output.mkdir(parents=True, exist_ok=True)
    older_manifest.parent.mkdir(parents=True, exist_ok=True)
    newer_manifest.parent.mkdir(parents=True, exist_ok=True)
    (older_output / "old_report.md").write_text("# Old\n", encoding="utf-8")
    (newer_output / "new_report.md").write_text("# New\n", encoding="utf-8")
    older_manifest.write_text(
        json.dumps(
            {
                "experiment": {"id": unique_id, "title": "old", "runner": "test"},
                "params": {"hypothesis": "old"},
                "result": {
                    "output_dir": str(older_output).replace("/", "\\"),
                    "report_path": str((older_output / "old_report.md")).replace("/", "\\"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    newer_manifest.write_text(
        json.dumps(
            {
                "experiment": {"id": unique_id, "title": "new", "runner": "test"},
                "params": {"hypothesis": "new", "report_language": "ru", "sample_size": 120},
                "result": {
                    "output_dir": str(newer_output).replace("/", "\\"),
                    "report_path": str((newer_output / "new_report.md")).replace("/", "\\"),
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    now = time.time()
    old_time = now - 120
    new_time = now - 60
    os.utime(older_manifest, (old_time, old_time))
    os.utime(newer_manifest, (new_time, new_time))

    outputs = _experiment_outputs_payload([{"id": unique_id, "title": "Latest", "runner": "test"}])
    assert len(outputs) == 1
    output = outputs[0]
    assert output["hypothesis"] == "new"
    assert output["report_language"] == "ru"
    assert output["last_params"]["sample_size"] == 120
    assert output["primary_report"]["name"] == "new_report.md"
    assert output["manifest_path"].endswith("newer_manifest\\run_manifest.json")
    assert output["last_run_at"] is not None
