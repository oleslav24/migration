const state = {
  summary: null,
  runs: [],
  runStatusById: {},
  notifiedRunFinal: {},
  selectedRun: null,
  polling: false,
  selectedTablePath: null,
  selectedEvidencePath: null,
  compareA: null,
  compareB: null,
  selectedReports: [],
  reportExperimentFilter: "all",
  evidenceExperimentFilter: "all",
  reportArtifactFilter: "",
  evidenceArtifactFilter: "",
  reportFilterPreset: "all",
  evidenceFilterPreset: "all",
  reportExpandAll: false,
  evidenceExpandAll: false,
  reportWorkflowOnly: false,
  evidenceWorkflowOnly: false,
  reportIncludeInactive: false,
  evidenceIncludeInactive: false,
  autoOpenExperiment: null,
  autoOpenTarget: "reportPreview",
  lang: localStorage.getItem("webapp.language") || "ru",
  i18n: {},
};

const RESEARCH_WORKFLOW_STEPS = [
  {
    order: 1,
    experimentId: "toponym_research_workflow",
    titleKey: "workflow.toponym.title",
    titleFallback: "Toponym extraction and grouping",
    textKey: "workflow.toponym.text",
    textFallback: "Find city/district mentions, rank by frequency, and export texts by toponym.",
    keyTable: "toponym_frequency.csv",
  },
  {
    order: 2,
    experimentId: "place_perception",
    titleKey: "workflow.perception.title",
    titleFallback: "Place perception categories",
    textKey: "workflow.perception.text",
    textFallback: "Classify messages into transparent place-perception categories.",
    keyTable: "place_perception_distribution.csv",
  },
  {
    order: 3,
    experimentId: "migration_narratives",
    titleKey: "workflow.narratives.title",
    titleFallback: "Migration narrative matrix",
    textKey: "workflow.narratives.text",
    textFallback: "Aggregate migration drivers and evidence by discourse category.",
    keyTable: "migration_narrative_matrix.csv",
  },
  {
    order: 4,
    experimentId: "sampling_coding",
    titleKey: "workflow.sampling.title",
    titleFallback: "Manual coding sample",
    textKey: "workflow.sampling.text",
    textFallback: "Generate reproducible sample for quantitative and qualitative coding.",
    keyTable: "coding_sample.csv",
  },
];

document.getElementById("languageSelect")?.addEventListener("change", (event) => {
  state.lang = event.target.value;
  localStorage.setItem("webapp.language", state.lang);
  applyTranslations();
  if (state.summary) renderSummary();
});

document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled) return;
  pulseButton(button);
});

document.getElementById("methodSampleButton")?.addEventListener("click", (event) => analyzeMethodSample(event.currentTarget));
document.getElementById("tableRefreshButton")?.addEventListener("click", (event) => {
  if (state.selectedTablePath) previewTable(state.selectedTablePath, "tablePreview", event.currentTarget);
});
document.getElementById("tableFilterInput")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && state.selectedTablePath) previewTable(state.selectedTablePath, "tablePreview");
});
document.getElementById("evidenceRefreshButton")?.addEventListener("click", (event) => {
  if (state.selectedEvidencePath) previewEvidence(state.selectedEvidencePath, event.currentTarget);
});
document.getElementById("reportBundleButton")?.addEventListener("click", (event) => buildReportBundle(event.currentTarget));
document.getElementById("reportExperimentFilter")?.addEventListener("change", (event) => {
  state.reportExperimentFilter = event.target.value || "all";
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceExperimentFilter")?.addEventListener("change", (event) => {
  state.evidenceExperimentFilter = event.target.value || "all";
  markEvidencePresetCustom();
  renderExperimentEvidence();
});
document.getElementById("reportIncludeInactive")?.addEventListener("change", (event) => {
  state.reportIncludeInactive = Boolean(event.target.checked);
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceIncludeInactive")?.addEventListener("change", (event) => {
  state.evidenceIncludeInactive = Boolean(event.target.checked);
  markEvidencePresetCustom();
  renderExperimentEvidence();
});
document.getElementById("reportArtifactFilter")?.addEventListener("input", (event) => {
  state.reportArtifactFilter = event.target.value || "";
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceArtifactFilter")?.addEventListener("input", (event) => {
  state.evidenceArtifactFilter = event.target.value || "";
  markEvidencePresetCustom();
  renderExperimentEvidence();
});
document.getElementById("reportExpandAll")?.addEventListener("change", (event) => {
  state.reportExpandAll = Boolean(event.target.checked);
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceExpandAll")?.addEventListener("change", (event) => {
  state.evidenceExpandAll = Boolean(event.target.checked);
  markEvidencePresetCustom();
  renderExperimentEvidence();
});
document.getElementById("reportWorkflowOnly")?.addEventListener("change", (event) => {
  state.reportWorkflowOnly = Boolean(event.target.checked);
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceWorkflowOnly")?.addEventListener("change", (event) => {
  state.evidenceWorkflowOnly = Boolean(event.target.checked);
  markEvidencePresetCustom();
  renderExperimentEvidence();
});
document.getElementById("reportPresetWorkflow")?.addEventListener("click", () => applyReportFilterPreset("workflow"));
document.getElementById("reportPresetAll")?.addEventListener("click", () => applyReportFilterPreset("all"));
document.getElementById("evidencePresetWorkflow")?.addEventListener("click", () => applyEvidenceFilterPreset("workflow"));
document.getElementById("evidencePresetAll")?.addEventListener("click", () => applyEvidenceFilterPreset("all"));
document.getElementById("reportResetFilters")?.addEventListener("click", () => {
  applyReportFilterPreset("all");
});
document.getElementById("evidenceResetFilters")?.addEventListener("click", () => {
  applyEvidenceFilterPreset("all");
});

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.tab);
  });
});

function setActiveTab(tabId) {
  if (!tabId) return;
  document.querySelectorAll("nav button").forEach((item) => {
    item.classList.toggle("active", item.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab").forEach((item) => {
    item.classList.toggle("active", item.id === tabId);
  });
}

function pulseButton(button) {
  if (!button) return;
  button.classList.remove("is-pressed");
  void button.offsetWidth;
  button.classList.add("is-pressed");
  setTimeout(() => button.classList.remove("is-pressed"), 160);
}

function setButtonBusy(button, busy) {
  if (!button) return;
  button.disabled = Boolean(busy);
  if (!busy) button.classList.remove("is-loading");
  button.setAttribute("aria-busy", busy ? "true" : "false");
}

async function withButtonBusy(button, task) {
  if (!button) return task();
  setButtonBusy(button, true);
  const spinnerTimer = setTimeout(() => {
    if (!button.disabled) return;
    button.classList.add("is-loading");
  }, 140);
  try {
    return await task();
  } finally {
    clearTimeout(spinnerTimer);
    setButtonBusy(button, false);
  }
}

function showToast(message, level = "info", durationMs = 3200) {
  if (!message) return;
  const stack = document.getElementById("toastStack");
  if (!stack) return;
  const toast = document.createElement("div");
  toast.className = `toast ${level}`;
  toast.setAttribute("role", level === "error" ? "alert" : "status");
  toast.textContent = message;
  stack.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.add("visible");
  });
  const dismiss = () => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 220);
  };
  setTimeout(dismiss, durationMs);
}

function latestRunsByPreset() {
  const map = {};
  for (const run of state.runs || []) {
    if (!run?.preset) continue;
    if (!map[run.preset]) map[run.preset] = run;
  }
  return map;
}

function outputByExperimentId(experimentId) {
  return (state.summary?.experiment_outputs || []).find((item) => item.id === experimentId);
}

function experimentTitle(experimentId) {
  const fromSummary = (state.summary?.experiments || []).find((item) => item.id === experimentId);
  return t(`experiment.${experimentId}.title`, fromSummary?.title || experimentId);
}

function workflowStepStatus(experimentId) {
  const latest = latestRunsByPreset()[experimentId];
  if (latest?.status === "running") return "running";
  if (typeof latest?.status === "string" && latest.status.startsWith("failed")) return "failed";
  return outputByExperimentId(experimentId)?.primary_report ? "completed" : "missing";
}

function workflowStepStatusLabel(status) {
  if (status === "running") return t("status.running", "running");
  if (status === "completed") return t("status.completed", "completed");
  if (status === "failed") return t("status.failed", "failed");
  return t("text.not_run_yet", "Not run yet.");
}

function researchNextAction() {
  for (const step of RESEARCH_WORKFLOW_STEPS) {
    const status = workflowStepStatus(step.experimentId);
    if (status === "failed") return { kind: "rerun", step };
    if (status === "missing") return { kind: "run", step };
  }
  return { kind: "review" };
}

function renderResearchSessionSummary() {
  const steps = RESEARCH_WORKFLOW_STEPS.map((step) => {
    const status = workflowStepStatus(step.experimentId);
    return `
      <div class="session-step">
        <span class="session-step-title">${escapeHtml(t(step.titleKey, step.titleFallback))}</span>
        <span class="status ${escapeAttr(status)}">${escapeHtml(workflowStepStatusLabel(status))}</span>
      </div>
    `;
  }).join("");
  const nextAction = researchNextAction();
  let actionHtml = "";
  if (nextAction.kind === "run" || nextAction.kind === "rerun") {
    actionHtml = `
      <button class="primary workflow-run" data-experiment="${escapeAttr(nextAction.step.experimentId)}">
        ${escapeHtml(nextAction.kind === "rerun" ? t("button.rerun_step", "Rerun step") : t("button.run_next_step", "Run next step"))}
      </button>
    `;
  } else {
    actionHtml = actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: "toponym_research_workflow", classes: "primary" });
  }
  return `
    <section class="output-card session-card">
      <div>
        <h3>${escapeHtml(t("section.research_session", "Research Session"))}</h3>
        <p class="muted">${escapeHtml(t("text.research_session_hint", "Track workflow progress and run the next required step."))}</p>
        <div class="session-steps">${steps}</div>
      </div>
      <div class="button-row">
        ${actionHtml}
      </div>
    </section>
  `;
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const action = button.dataset.action;
  const path = button.dataset.path || "";
  const target = button.dataset.target || "";
  if (action === "preview-table") {
    await previewTable(path, target || "tablePreview", button);
    return;
  }
  if (action === "preview-report") {
    await previewReport(path, target || "reportPreview", button);
    return;
  }
  if (action === "preview-evidence") {
    await previewEvidence(path, button);
    return;
  }
  if (action === "add-report") {
    addReportToBundle(path);
    return;
  }
  if (action === "remove-report") {
    removeReportFromBundle(path);
    return;
  }
  if (action === "run-manual-coding") {
    await startManualCodingSample(button);
    return;
  }
  if (action === "show-experiment-reports") {
    await focusExperimentReports(button.dataset.experiment || "", button);
    return;
  }
  if (action === "show-experiment-evidence") {
    await focusExperimentEvidence(button.dataset.experiment || "", button);
  }
});

async function loadSummary() {
  const response = await fetch("/api/summary");
  state.summary = await response.json();
  renderSummary();
}

async function loadLanguagePack() {
  const response = await fetch("/i18n.json");
  state.i18n = await response.json();
  const select = document.getElementById("languageSelect");
  if (select) select.value = state.lang;
  applyTranslations();
}

function t(key, fallback = "") {
  return state.i18n[state.lang]?.[key] || state.i18n.en?.[key] || fallback || key;
}

function applyTranslations() {
  document.documentElement.lang = state.lang;
  document.title = t("app.title", "Migration Research Workspace");
  document.querySelectorAll("[data-i18n]").forEach((item) => {
    item.textContent = t(item.dataset.i18n, item.textContent);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((item) => {
    item.setAttribute("placeholder", t(item.dataset.i18nPlaceholder, item.getAttribute("placeholder") || ""));
  });
  document.querySelectorAll("[data-i18n-value]").forEach((item) => {
    if (!item.dataset.userEdited) item.value = t(item.dataset.i18nValue, item.value || "");
  });
}

document.querySelectorAll("[data-i18n-value]").forEach((item) => {
  item.addEventListener("input", () => {
    item.dataset.userEdited = "true";
  });
});

function renderSummary() {
  const files = state.summary.files;
  const project = state.summary.project_state;
  const cards = [
    [t("card.datasets", "Datasets"), project.datasets.length],
    [t("card.experiments", "Experiments"), state.summary.experiments.length],
    [t("card.agents", "Agents"), project.agents.length],
    [t("card.pipeline_csv", "Pipeline CSV"), files.pipeline.length],
    [t("card.discovery_csv", "Discovery CSV"), files.discovery.length],
    [t("card.agent_files", "Agent files"), state.summary.agent_files.length],
  ];
  document.getElementById("summaryCards").innerHTML = cards.map(([label, value]) => `
    <div class="card"><strong>${value}</strong><span>${label}</span></div>
  `).join("");
  renderReadiness();
  Object.entries(state.summary.charts).forEach(([id, chart]) => drawBars(id, chart));
  renderDatasets();
  renderExperiments();
  renderToponymResearch();
  renderMethods();
  renderRunManifests();
  renderSelectedReports();
  renderSafetyModel();
  renderAgentContracts();
  renderExperimentOutputs();
  renderFiles("pipelineFiles", files.pipeline, "tablePreview");
  renderFiles("discoveryFiles", files.discovery, "discoveryPreview");
  document.getElementById("configPreview").textContent = JSON.stringify(state.summary.config, null, 2);
}

function renderReadiness() {
  const target = document.getElementById("readinessList");
  if (!target) return;
  target.innerHTML = state.summary.project_state.readiness.map((item) => `
    <div class="readiness ${escapeAttr(item.status)}">
      <strong>${escapeHtml(t(`state.${item.status}`, item.status))}</strong>
      <span>${escapeHtml(item.label)}</span>
    </div>
  `).join("");
}

function renderDatasets() {
  const target = document.getElementById("datasetList");
  if (!target) return;
  const datasets = state.summary.project_state.datasets || [];
  if (!datasets.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_configured_datasets", "No configured datasets."))}</p>`;
    return;
  }
  target.innerHTML = `<div class="file-list">${datasets.map((dataset) => `
    <div class="file">
      <div>
        <strong>${escapeHtml(dataset.source)} / ${escapeHtml(dataset.name || dataset.path)}</strong><br>
        <code>${escapeHtml(dataset.resolved_path || dataset.path)}</code><br>
        <span class="muted">${escapeHtml(dataset.row_count_note || "")}${dataset.row_count !== null && dataset.row_count !== undefined ? ` / ${formatNumber(dataset.row_count)} ${t("text.rows", "rows")}` : ""}</span>
      </div>
      ${dataset.exists ? actionButton("preview-table", t("button.preview", "Preview"), { path: dataset.resolved_path || dataset.path, target: "datasetPreview" }) : `<span class="status failed">${escapeHtml(t("status.missing", "missing"))}</span>`}
    </div>
  `).join("")}</div>`;
}

function drawBars(id, chart) {
  const target = document.getElementById(id);
  if (!target) return;
  if (!chart.labels.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_data_yet", "No data yet."))}</p>`;
    return;
  }
  const max = Math.max(...chart.values, 1);
  target.innerHTML = chart.labels.map((label, index) => {
    const value = chart.values[index];
    const width = Math.max(2, (value / max) * 100);
    return `<div class="bar-row">
      <div class="bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <div>${formatNumber(value)}</div>
    </div>`;
  }).join("");
}

function renderPresets() {
  const target = document.getElementById("presetList");
  target.innerHTML = Object.entries(state.summary.presets).map(([id, preset]) => `
    <section class="panel preset">
      <div>
        <h2>${escapeHtml(preset.label)}</h2>
        <p>${escapeHtml(preset.description)}</p>
        <code>${escapeHtml(preset.command.join(" "))}</code>
      </div>
      <button class="primary run-button" data-preset="${escapeAttr(id)}">${escapeHtml(t("button.run", "Run"))}</button>
    </section>
  `).join("");
  target.querySelectorAll(".run-button").forEach((button) => {
    button.addEventListener("click", () => startRun(button.dataset.preset, button));
  });
}

function renderExperiments() {
  const target = document.getElementById("experimentList");
  if (!target) return;
  const experiments = state.summary.experiments || [];
  if (!experiments.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_registry_experiments", "No registry experiments configured."))}</p>`;
    return;
  }
  target.innerHTML = experiments.map((experiment) => `
    <section class="panel preset">
      <div>
        <h2>${escapeHtml(t(`experiment.${experiment.id}.title`, experiment.title))}</h2>
        <p>${escapeHtml(experiment.id)} / ${escapeHtml(experiment.runner)} / ${escapeHtml(t(`status.${experiment.status}`, experiment.status || "unknown"))}</p>
        <code>${escapeHtml(experiment.agent_contract)}</code>
        <p class="muted">${escapeHtml(t("text.outputs", "Outputs"))}: ${escapeHtml((experiment.expected_outputs || []).join(", "))}</p>
        <div class="param-grid">${renderParameterInputs(experiment)}</div>
      </div>
      <button class="primary experiment-button" data-experiment="${escapeAttr(experiment.id)}">${escapeHtml(t("button.run", "Run"))}</button>
    </section>
  `).join("");
  target.querySelectorAll(".experiment-button").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment, button));
  });
}

function renderToponymResearch() {
  const target = document.getElementById("toponymResearchPanel");
  if (!target) return;
  const experiment = (state.summary.experiments || []).find((item) => item.id === "toponym_research_workflow");
  const output = (state.summary.experiment_outputs || []).find((item) => item.id === "toponym_research_workflow");
  const samplingOutput = (state.summary.experiment_outputs || []).find((item) => item.id === "sampling_coding");
  const generalTables = (output?.tables || []).filter((file) => !file.path.includes("texts_by_toponym"));
  const textTables = (output?.tables || []).filter((file) => file.path.includes("texts_by_toponym"));
  const keyToponymFrequency = (output?.tables || []).find((file) => file.name === "toponym_frequency.csv");
  const textsManifest = (output?.configs || []).find((file) => file.name === "texts_by_toponym_manifest.json");
  if (!experiment) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_registry_experiments", "No registry experiments configured."))}</p>`;
    return;
  }
  const sessionSummary = renderResearchSessionSummary();
  target.innerHTML = `
    <div id="researchSessionSummary">${sessionSummary}</div>
    <section class="output-card">
      <div>
        <h3>${escapeHtml(t("text.research_setup", "Research setup"))}</h3>
        <p class="muted">${escapeHtml(t("text.toponym_workflow_hint", "State a hypothesis, choose the text scope and run the toponym workflow."))}</p>
        <div class="param-grid">${renderParameterInputs(experiment)}</div>
      </div>
      <button class="primary experiment-button" data-experiment="${escapeAttr(experiment.id)}">${escapeHtml(t("button.run", "Run"))}</button>
    </section>
    <section class="output-card">
      <div>
        <h3>${escapeHtml(t("text.current_result", "Current result"))}</h3>
        <p class="muted">${escapeHtml(output?.hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${output.hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
        <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(output?.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
        <p class="muted">${escapeHtml(output?.output_dir || t("text.not_run_yet", "Not run yet."))}</p>
      </div>
      <div class="button-row">
        ${output?.primary_report ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "toponymResearchPreview", classes: "primary" }) : `<span class="status missing">${escapeHtml(t("text.not_run_yet", "Not run yet."))}</span>`}
        ${keyToponymFrequency ? actionButton("preview-table", t("button.open_toponym_frequency", "Toponym frequency"), { path: keyToponymFrequency.path, target: "tablePreview" }) : ""}
        ${textsManifest ? actionButton("preview-report", t("button.open_texts_manifest", "Texts export manifest"), { path: textsManifest.path, target: "toponymResearchPreview" }) : ""}
      </div>
      <div class="artifact-groups">
        <details open>
          <summary>${escapeHtml(t("section.reports", "Reports"))}</summary>
          ${renderArtifactButtons(output?.reports || [], "toponymResearchPreview", "report")}
        </details>
        <details>
          <summary>${escapeHtml(t("section.results_explorer", "Results Explorer"))}</summary>
          ${renderArtifactButtons(generalTables, "tablePreview", "table")}
        </details>
        <details>
          <summary>${escapeHtml(t("text.texts_by_toponym", "Texts by toponym"))}</summary>
          ${renderArtifactButtons(textTables, "tablePreview", "table")}
        </details>
        <details>
          <summary>${escapeHtml(t("section.evidence_browser", "Evidence Browser"))}</summary>
          ${renderArtifactButtons(output?.evidence || [], "evidencePreview", "evidence")}
        </details>
      </div>
      <div class="button-row">
        ${actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: experiment.id })}
        ${actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: experiment.id })}
      </div>
    </section>
    <section class="panel">
      <h2>${escapeHtml(t("section.research_workflow", "Research Workflow Steps"))}</h2>
      <p class="muted">${escapeHtml(t("text.research_workflow_hint", "Run the steps in order: detect places, interpret space frames, inspect migration narratives, then prepare coding sample."))}</p>
      <div class="workflow-grid">${renderResearchWorkflowCards()}</div>
    </section>
    <section class="panel">
      <h2>${escapeHtml(t("section.workflow_results_navigator", "Workflow Results Navigator"))}</h2>
      <p class="muted">${escapeHtml(t("text.workflow_results_navigator_hint", "Open key outputs by workflow step without browsing long artifact lists."))}</p>
      ${renderWorkflowResultsNavigator()}
    </section>
    <section class="panel">
      <h2>${escapeHtml(t("section.manual_coding_next_step", "Manual coding next step"))}</h2>
      <p class="muted">${escapeHtml(t("text.manual_coding_hint", "After reviewing key places and evidence, launch a coding sample for manual content analysis."))}</p>
      ${renderManualCodingNextStep(output, samplingOutput, textTables)}
    </section>
    <section class="panel"><h2>${escapeHtml(t("section.report_preview", "Report Preview"))}</h2><pre id="toponymResearchPreview">${escapeHtml(t("hint.select_report", "Select a report."))}</pre></section>
  `;
  target.querySelectorAll(".experiment-button").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment, button));
  });
  target.querySelectorAll(".workflow-run").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment, button));
  });
}

function refreshResearchSessionSummary() {
  const target = document.getElementById("researchSessionSummary");
  if (!target) return;
  target.innerHTML = renderResearchSessionSummary();
  target.querySelectorAll(".workflow-run").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment, button));
  });
}

function renderManualCodingNextStep(toponymOutput, samplingOutput, textTables) {
  const toponymReady = Boolean(toponymOutput?.primary_report);
  const sampleTable = (samplingOutput?.tables || []).find((item) => item.name === "coding_sample.csv") || (samplingOutput?.tables || [])[0];
  const sampleByToponymTable = (samplingOutput?.tables || []).find((item) => item.name === "coding_sample_by_toponym.csv");
  const codebook = (samplingOutput?.reports || []).find((item) => item.name === "coding_codebook.md");
  const codebookToponym = (samplingOutput?.reports || []).find((item) => item.name === "coding_codebook_toponym.md");
  const toponymOptions = (textTables || []).map((item) => {
    const name = item.name.replace(/\.csv$/i, "").replaceAll("_", " ");
    return `<option value="${escapeAttr(name)}">${escapeHtml(name)}</option>`;
  }).join("");
  return `
    <section class="output-card ${toponymReady ? "" : "muted-card"}">
      <div>
        <h3>${escapeHtml(t("text.manual_coding", "Manual coding sample"))}</h3>
        <p class="muted">${escapeHtml(toponymReady ? t("text.manual_coding_ready", "Toponym workflow is available. You can proceed to sampling.") : t("text.manual_coding_wait", "Run toponym workflow first to collect places and evidence."))}</p>
        <div class="param-grid">
          <label>
            <span>${escapeHtml(t("param.toponym", "Toponym filter"))}</span>
            <select id="manualCodingToponym">
              <option value="">${escapeHtml(t("param.toponym.none", "All places"))}</option>
              ${toponymOptions}
            </select>
          </label>
          <label>
            <span>${escapeHtml(t("param.sample_size", "Sample size"))}</span>
            <input id="manualCodingSampleSize" type="number" min="1" max="5000" value="100" />
          </label>
          <label>
            <span>${escapeHtml(t("param.stratify_by", "Stratify by"))}</span>
            <select id="manualCodingStratifyBy">
              <option value="source">${escapeHtml(t("param.stratify_by.source", "source"))}</option>
              <option value="month">${escapeHtml(t("param.stratify_by.month", "month"))}</option>
              <option value="sentiment">${escapeHtml(t("param.stratify_by.sentiment", "sentiment"))}</option>
              <option value="topic_id">${escapeHtml(t("param.stratify_by.topic_id", "topic_id"))}</option>
              <option value="migration_driver">${escapeHtml(t("param.stratify_by.migration_driver", "migration_driver"))}</option>
            </select>
          </label>
        </div>
      </div>
      <div class="button-row">
        ${actionButton("run-manual-coding", t("button.run_coding_sample", "Run coding sample"), { classes: "primary" })}
        ${sampleTable ? actionButton("preview-table", t("button.open_sample", "Open sample"), { path: sampleTable.path, target: "tablePreview" }) : ""}
        ${sampleByToponymTable ? actionButton("preview-table", t("button.open_toponym_sample", "Open toponym sample"), { path: sampleByToponymTable.path, target: "tablePreview" }) : ""}
        ${codebook ? actionButton("preview-report", t("button.open_codebook", "Open codebook"), { path: codebook.path, target: "toponymResearchPreview" }) : ""}
        ${codebookToponym ? actionButton("preview-report", t("button.open_toponym_codebook", "Open toponym codebook"), { path: codebookToponym.path, target: "toponymResearchPreview" }) : ""}
      </div>
    </section>
  `;
}

async function startManualCodingSample(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const toponym = document.getElementById("manualCodingToponym")?.value || "";
    const sampleSize = Number(document.getElementById("manualCodingSampleSize")?.value || "100");
    const stratifyBy = document.getElementById("manualCodingStratifyBy")?.value || "source";
    const params = {
      toponym,
      sample_size: sampleSize,
      stratify_by: stratifyBy,
      random_state: 42,
      report_language: state.lang === "ru" ? "ru" : "en",
    };
    document.getElementById("runLog").textContent = `${t("message.starting", "Starting")} sampling_coding...`;
    try {
      state.autoOpenExperiment = "sampling_coding";
      state.autoOpenTarget = "toponymResearchPreview";
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment: "sampling_coding", params }),
      });
      const run = await response.json();
      if (!response.ok) {
        document.getElementById("runLog").textContent = run.error || t("message.failed_start_experiment", "Failed to start experiment.");
        showToast(run.error || t("message.failed_start_experiment", "Failed to start experiment."), "error", 4200);
        return;
      }
      state.selectedRun = run.id;
      showToast(`${t("message.run_started", "Run started")}: ${experimentTitle("sampling_coding")}`, "info");
      await pollRuns(true);
      await loadSummary();
    } catch (error) {
      document.getElementById("runLog").textContent = `${t("message.failed_start_experiment", "Failed to start experiment.")}: ${error}`;
      showToast(`${t("message.failed_start_experiment", "Failed to start experiment.")}: ${error}`, "error", 4200);
    }
  });
}

function renderResearchWorkflowCards() {
  return RESEARCH_WORKFLOW_STEPS.map((step) => renderWorkflowCard(step)).join("");
}

function renderWorkflowCard(step) {
  const output = (state.summary.experiment_outputs || []).find((item) => item.id === step.experimentId);
  const statusClass = workflowStepStatus(step.experimentId);
  const statusLabel = workflowStepStatusLabel(statusClass);
  const keyTable = (output?.tables || []).find((item) => item.name === step.keyTable) || (output?.tables || [])[0];
  const runButton = `<button class="workflow-run" data-experiment="${escapeAttr(step.experimentId)}">${escapeHtml(t("button.run", "Run"))}</button>`;
  const reportButton = output?.primary_report
    ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "toponymResearchPreview" })
    : "";
  const tableButton = keyTable
    ? actionButton("preview-table", t("button.preview_result", "Preview result"), { path: keyTable.path, target: "tablePreview" })
    : "";
  const reportsButton = actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: step.experimentId });
  const evidenceButton = actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: step.experimentId });
  return `
    <article class="workflow-card">
      <div class="workflow-head">
        <span class="workflow-step">${step.order}</span>
        <div>
          <h3>${escapeHtml(t(step.titleKey, step.titleFallback))}</h3>
          <p class="muted">${escapeHtml(t(step.textKey, step.textFallback))}</p>
        </div>
        <span class="status ${escapeAttr(statusClass)}">${escapeHtml(statusLabel)}</span>
      </div>
      <div class="button-row">
        ${runButton}
        ${reportButton}
        ${tableButton}
        ${reportsButton}
        ${evidenceButton}
      </div>
    </article>
  `;
}

function renderWorkflowResultsNavigator() {
  const items = RESEARCH_WORKFLOW_STEPS.map((step) => {
    const output = outputByExperimentId(step.experimentId);
    const statusClass = workflowStepStatus(step.experimentId);
    const statusLabel = workflowStepStatusLabel(statusClass);
    const keyTable = (output?.tables || []).find((item) => item.name === step.keyTable) || (output?.tables || [])[0] || null;
    const runButton = !output?.primary_report
      ? `<button class="workflow-run" data-experiment="${escapeAttr(step.experimentId)}">${escapeHtml(t("button.run", "Run"))}</button>`
      : "";
    const reportButton = output?.primary_report
      ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "toponymResearchPreview", classes: "primary" })
      : "";
    const tableButton = keyTable
      ? actionButton("preview-table", t("button.preview_result", "Preview result"), { path: keyTable.path, target: "tablePreview" })
      : "";
    const evidenceButton = actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: step.experimentId });
    return `
      <div class="run-item">
        <div>
          <strong>${escapeHtml(t(step.titleKey, step.titleFallback))}</strong>
          <span class="status ${escapeAttr(statusClass)}">${escapeHtml(statusLabel)}</span><br>
          <span class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(output?.last_run_at) || t("text.not_run_yet", "Not run yet."))}</span>
        </div>
        <div class="button-row">
          ${runButton}
          ${reportButton}
          ${tableButton}
          ${evidenceButton}
          ${actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: step.experimentId })}
        </div>
      </div>
    `;
  }).join("");
  return `<div class="run-list">${items}</div>`;
}

function renderParameterInputs(experiment) {
  const parameters = [{ name: "hypothesis", type: "string", default: "" }, ...(experiment.parameters || [])];
  if (!parameters.length) return `<p class="muted">${escapeHtml(t("text.no_configurable_parameters", "No configurable parameters."))}</p>`;
  return parameters.map((param) => `
    <label class="${param.name === "hypothesis" ? "wide-param" : ""}">
      <span>${escapeHtml(t(`param.${param.name}`, param.name))}</span>
      ${param.name === "hypothesis" ? `<textarea
        rows="2"
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="hypothesis"
        placeholder="${escapeAttr(t("placeholder.hypothesis", "Research hypothesis or question"))}"
      >${escapeHtml(param.default || "")}</textarea>` : param.choices ? `<select
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="${escapeAttr(param.name)}"
      >${param.choices.map((choice) => `<option value="${escapeAttr(choice)}" ${choice === param.default ? "selected" : ""}>${escapeHtml(t(`param.${param.name}.${choice}`, choice))}</option>`).join("")}</select>` : `<input
        type="${param.type === "int" ? "number" : "text"}"
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="${escapeAttr(param.name)}"
        value="${escapeAttr(param.default ?? "")}"
        ${param.min !== undefined ? `min="${escapeAttr(param.min)}"` : ""}
        ${param.max !== undefined ? `max="${escapeAttr(param.max)}"` : ""}
      />`}
    </label>
  `).join("");
}

function collectExperimentParams(experimentId) {
  const params = {};
  document.querySelectorAll(`[data-param-experiment="${CSS.escape(experimentId)}"]`).forEach((input) => {
    params[input.dataset.paramName] = input.type === "number" ? Number(input.value) : input.value;
  });
  return params;
}

function renderMethods() {
  const target = document.getElementById("methodList");
  if (!target) return;
  target.innerHTML = (state.summary.methods || []).map((method) => `
    <section class="method-card">
      <h3>${escapeHtml(method.title)}</h3>
      <p><strong>${escapeHtml(t("text.backend", "Backend"))}:</strong> ${escapeHtml(method.backend)}</p>
      <p><strong>${escapeHtml(t("text.stage", "Stage"))}:</strong> ${escapeHtml(method.stage || "unspecified")}</p>
      <p><strong>${escapeHtml(t("text.inputs", "Inputs"))}:</strong> ${escapeHtml((method.inputs || []).join(", "))}</p>
      <p><strong>${escapeHtml(t("text.outputs", "Outputs"))}:</strong> ${escapeHtml((method.outputs || []).join(", "))}</p>
      <p><strong>${escapeHtml(t("text.quality_gates", "Quality gates"))}:</strong> ${escapeHtml((method.quality_gates || []).join("; "))}</p>
      <p><strong>${escapeHtml(t("text.used_by", "Used by"))}:</strong> ${escapeHtml((method.experiments || []).join(", "))}</p>
      <p class="muted">${escapeHtml(method.limitations)}</p>
    </section>
  `).join("");
}

async function analyzeMethodSample(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const target = document.getElementById("methodSampleResult");
    const text = document.getElementById("methodSampleText").value;
    target.innerHTML = `<p class="muted">${escapeHtml(t("message.analyzing_sample", "Analyzing sample..."))}</p>`;
    try {
      const response = await fetch("/api/method-sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        target.innerHTML = `<p class="status failed">${escapeHtml(payload.error || t("message.method_failed", "Method analysis failed"))}</p>`;
        return;
      }
      target.innerHTML = `
        <section class="method-card result-card">
          <h3>${escapeHtml(t("text.normalized_text", "Normalized text"))}</h3>
          <p>${escapeHtml(payload.normalized_text)}</p>
        </section>
        ${(payload.results || []).map((item) => `
          <section class="method-card result-card">
            <h3>${escapeHtml(item.method)}</h3>
            <p><strong>${escapeHtml(t("text.label", "Label"))}:</strong> ${escapeHtml(item.label)}</p>
            <p><strong>${escapeHtml(t("text.confidence", "Confidence"))}:</strong> ${escapeHtml(item.confidence)}</p>
            <pre>${escapeHtml(typeof item.evidence === "string" ? item.evidence : JSON.stringify(item.evidence, null, 2))}</pre>
          </section>
        `).join("")}
      `;
    } catch (error) {
      target.innerHTML = `<p class="status failed">${escapeHtml(t("message.method_failed", "Method analysis failed"))}: ${escapeHtml(error)}</p>`;
    }
  });
}

function renderAgentContracts() {
  const target = document.getElementById("agentContracts");
  if (!target) return;
  const experiments = state.summary.experiments || [];
  target.innerHTML = `<div class="file-list">${experiments.map((experiment) => `
    <div class="file">
      <div><strong>${escapeHtml(experiment.id)}</strong><br><code>${escapeHtml(experiment.agent_contract)}</code></div>
      <span>${escapeHtml(experiment.runner)}</span>
    </div>
  `).join("")}</div>`;
}

function sortedExperimentOutputs() {
  const outputs = [...(state.summary.experiment_outputs || [])];
  outputs.sort((a, b) => {
    const readyA = a.primary_report ? 1 : 0;
    const readyB = b.primary_report ? 1 : 0;
    if (readyA !== readyB) return readyB - readyA;
    const timeA = Number(a.last_run_at || 0);
    const timeB = Number(b.last_run_at || 0);
    if (timeA !== timeB) return timeB - timeA;
    return String(a.title || a.id || "").localeCompare(String(b.title || b.id || ""));
  });
  return outputs;
}

function renderExperimentFilterSelect(selectId, selectedValue) {
  const select = document.getElementById(selectId);
  if (!select) return selectedValue;
  const outputs = sortedExperimentOutputs();
  const options = [{ value: "all", label: t("label.all_experiments", "All experiments") }, ...outputs.map((item) => ({
    value: item.id,
    label: t(`experiment.${item.id}.title`, item.title || item.id),
  }))];
  const validValues = new Set(options.map((item) => item.value));
  const value = validValues.has(selectedValue) ? selectedValue : "all";
  select.innerHTML = options.map((option) => `
    <option value="${escapeAttr(option.value)}" ${option.value === value ? "selected" : ""}>${escapeHtml(option.label)}</option>
  `).join("");
  return value;
}

function filterOutputs(outputs, selectedValue) {
  if (selectedValue === "all") return outputs;
  return outputs.filter((item) => item.id === selectedValue);
}

function markReportPresetCustom() {
  if (state.reportFilterPreset !== "custom") {
    state.reportFilterPreset = "custom";
    syncFilterPresetButtons();
  }
}

function markEvidencePresetCustom() {
  if (state.evidenceFilterPreset !== "custom") {
    state.evidenceFilterPreset = "custom";
    syncFilterPresetButtons();
  }
}

function syncFilterPresetButtons() {
  document.getElementById("reportPresetWorkflow")?.classList.toggle("active", state.reportFilterPreset === "workflow");
  document.getElementById("reportPresetAll")?.classList.toggle("active", state.reportFilterPreset === "all");
  document.getElementById("evidencePresetWorkflow")?.classList.toggle("active", state.evidenceFilterPreset === "workflow");
  document.getElementById("evidencePresetAll")?.classList.toggle("active", state.evidenceFilterPreset === "all");
}

function applyReportFilterPreset(mode) {
  state.reportExperimentFilter = "all";
  state.reportIncludeInactive = false;
  state.reportExpandAll = false;
  state.reportArtifactFilter = "";
  state.reportWorkflowOnly = mode === "workflow";
  state.reportFilterPreset = mode;
  renderExperimentOutputs();
}

function applyEvidenceFilterPreset(mode) {
  state.evidenceExperimentFilter = "all";
  state.evidenceIncludeInactive = false;
  state.evidenceExpandAll = false;
  state.evidenceArtifactFilter = "";
  state.evidenceWorkflowOnly = mode === "workflow";
  state.evidenceFilterPreset = mode;
  renderExperimentOutputs();
}

function workflowExperimentIds() {
  return new Set(RESEARCH_WORKFLOW_STEPS.map((step) => step.experimentId));
}

function normalizeSearchText(value) {
  return String(value || "").toLowerCase().trim();
}

function containsFilter(value, query) {
  if (!query) return true;
  return normalizeSearchText(value).includes(query);
}

function filterArtifactFiles(files, query) {
  if (!query) return files;
  return (files || []).filter((file) => containsFilter(file?.name, query) || containsFilter(file?.path, query));
}

function outputMatchesFilter(item, query) {
  if (!query) return true;
  return [
    item?.id,
    item?.title,
    item?.hypothesis,
    item?.output_dir,
  ].some((value) => containsFilter(value, query));
}

function renderExperimentOutputs() {
  state.reportExperimentFilter = renderExperimentFilterSelect("reportExperimentFilter", state.reportExperimentFilter);
  state.evidenceExperimentFilter = renderExperimentFilterSelect("evidenceExperimentFilter", state.evidenceExperimentFilter);
  const reportArtifactFilter = document.getElementById("reportArtifactFilter");
  if (reportArtifactFilter) reportArtifactFilter.value = state.reportArtifactFilter;
  const evidenceArtifactFilter = document.getElementById("evidenceArtifactFilter");
  if (evidenceArtifactFilter) evidenceArtifactFilter.value = state.evidenceArtifactFilter;
  const reportExpandAll = document.getElementById("reportExpandAll");
  if (reportExpandAll) reportExpandAll.checked = state.reportExpandAll;
  const evidenceExpandAll = document.getElementById("evidenceExpandAll");
  if (evidenceExpandAll) evidenceExpandAll.checked = state.evidenceExpandAll;
  const reportWorkflowOnly = document.getElementById("reportWorkflowOnly");
  if (reportWorkflowOnly) reportWorkflowOnly.checked = state.reportWorkflowOnly;
  const evidenceWorkflowOnly = document.getElementById("evidenceWorkflowOnly");
  if (evidenceWorkflowOnly) evidenceWorkflowOnly.checked = state.evidenceWorkflowOnly;
  const reportIncludeInactive = document.getElementById("reportIncludeInactive");
  if (reportIncludeInactive) reportIncludeInactive.checked = state.reportIncludeInactive;
  const evidenceIncludeInactive = document.getElementById("evidenceIncludeInactive");
  if (evidenceIncludeInactive) evidenceIncludeInactive.checked = state.evidenceIncludeInactive;
  syncFilterPresetButtons();
  renderKeyWorkflowArtifacts();
  renderExperimentReports();
  renderExperimentEvidence();
}

function renderKeyWorkflowArtifacts() {
  const target = document.getElementById("keyWorkflowArtifacts");
  if (!target) return;
  const items = RESEARCH_WORKFLOW_STEPS.map((step) => {
    const output = outputByExperimentId(step.experimentId);
    const statusClass = workflowStepStatus(step.experimentId);
    const statusLabel = workflowStepStatusLabel(statusClass);
    const keyTable = (output?.tables || []).find((item) => item.name === step.keyTable) || (output?.tables || [])[0] || null;
    const actionButtons = [
      output?.primary_report
        ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "reportPreview", classes: "primary" })
        : "",
      keyTable
        ? actionButton("preview-table", t("button.preview_result", "Preview result"), { path: keyTable.path, target: "tablePreview" })
        : "",
      output?.primary_report
        ? actionButton("add-report", t("button.add", "Add"), { path: output.primary_report.path })
        : "",
      actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: step.experimentId }),
      actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: step.experimentId }),
    ].filter(Boolean).join("");
    return `
      <div class="run-item">
        <div>
          <strong>${escapeHtml(t(step.titleKey, step.titleFallback))}</strong>
          <span class="status ${escapeAttr(statusClass)}">${escapeHtml(statusLabel)}</span><br>
          <span class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(output?.last_run_at) || t("text.not_run_yet", "Not run yet."))}</span>
        </div>
        <div class="button-row">${actionButtons}</div>
      </div>
    `;
  }).join("");
  target.innerHTML = `<p class="muted">${escapeHtml(t("text.key_workflow_artifacts_hint", "Quick access to key artifacts for each workflow step."))}</p><div class="run-list">${items}</div>`;
}

function outputHasArtifacts(item) {
  return Boolean(
    item?.primary_report
    || (item?.reports || []).length
    || (item?.evidence || []).length
    || (item?.tables || []).length
    || (item?.configs || []).length,
  );
}

function renderExperimentReports() {
  const target = document.getElementById("experimentReportList");
  if (!target) return;
  const query = normalizeSearchText(state.reportArtifactFilter);
  let outputs = filterOutputs(sortedExperimentOutputs(), state.reportExperimentFilter);
  if (state.reportWorkflowOnly) {
    const workflowIds = workflowExperimentIds();
    outputs = outputs.filter((item) => workflowIds.has(item.id));
  }
  if (!state.reportIncludeInactive) {
    outputs = outputs.filter((item) => Boolean(item.primary_report));
  }
  outputs = outputs.map((item) => {
    const reports = filterArtifactFiles(item.reports || [], query);
    const primary = item.primary_report && reports.some((file) => file.path === item.primary_report.path)
      ? item.primary_report
      : reports[0] || null;
    const otherReports = reports.filter((file) => !primary || file.path !== primary.path);
    return { ...item, _reportsFiltered: reports, _primaryFiltered: primary, _otherReportsFiltered: otherReports };
  }).filter((item) => (
    !query
    || item._reportsFiltered.length > 0
    || outputMatchesFilter(item, query)
  ));
  if (!outputs.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_files", "No files yet."))}</p>`;
    return;
  }
  const openDetails = state.reportExpandAll || outputs.length <= 1 || state.reportExperimentFilter !== "all" || Boolean(query);
  target.innerHTML = outputs.map((item) => `
    <details class="output-accordion" ${openDetails ? "open" : ""}>
      <summary>
        <span>${escapeHtml(t(`experiment.${item.id}.title`, item.title || item.id))}</span>
        <span class="status ${escapeAttr(item._primaryFiltered ? "completed" : "missing")}">${escapeHtml(item._primaryFiltered ? t("status.completed", "completed") : t("status.missing", "missing"))}</span>
      </summary>
      <section class="output-card ${item._primaryFiltered ? "" : "muted-card"}">
        <div>
          <p class="muted">${escapeHtml(item.hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${item.hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
          <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(item.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
          <p class="muted">${escapeHtml(item.output_dir || t("text.not_run_yet", "Not run yet."))}</p>
        </div>
        <p class="muted">${escapeHtml(t("text.filtered_reports", "Reports shown"))}: ${item._reportsFiltered.length}/${item.reports.length}</p>
        ${item._primaryFiltered ? `<div class="button-row">
          ${actionButton("preview-report", t("button.open_report", "Open report"), { path: item._primaryFiltered.path, target: "reportPreview", classes: "primary" })}
          ${actionButton("add-report", t("button.add", "Add"), { path: item._primaryFiltered.path })}
        </div>` : `<span class="status missing">${escapeHtml(t("text.not_run_yet", "Not run yet."))}</span>`}
        ${item._otherReportsFiltered.length > 0 ? `<details><summary>${escapeHtml(t("text.other_reports", "Other reports"))} (${item._otherReportsFiltered.length})</summary>${renderArtifactButtons(item._otherReportsFiltered, "reportPreview")}</details>` : ""}
      </section>
    </details>
  `).join("");
}

function renderExperimentEvidence() {
  const target = document.getElementById("experimentEvidenceList");
  if (!target) return;
  const query = normalizeSearchText(state.evidenceArtifactFilter);
  let outputs = filterOutputs(sortedExperimentOutputs(), state.evidenceExperimentFilter);
  if (state.evidenceWorkflowOnly) {
    const workflowIds = workflowExperimentIds();
    outputs = outputs.filter((item) => workflowIds.has(item.id));
  }
  if (!state.evidenceIncludeInactive) {
    outputs = outputs.filter((item) => outputHasArtifacts(item));
  }
  outputs = outputs.map((item) => {
    const evidence = filterArtifactFiles(item.evidence || [], query);
    const tables = filterArtifactFiles(item.tables || [], query);
    const configs = filterArtifactFiles(item.configs || [], query);
    return { ...item, _evidenceFiltered: evidence, _tablesFiltered: tables, _configsFiltered: configs };
  }).filter((item) => (
    !query
    || item._evidenceFiltered.length > 0
    || item._tablesFiltered.length > 0
    || item._configsFiltered.length > 0
    || outputMatchesFilter(item, query)
  ));
  if (!outputs.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_files", "No files yet."))}</p>`;
    return;
  }
  const openDetails = state.evidenceExpandAll || outputs.length <= 1 || state.evidenceExperimentFilter !== "all" || Boolean(query);
  target.innerHTML = outputs.map((item) => `
    <details class="output-accordion" ${openDetails ? "open" : ""}>
      <summary>
        <span>${escapeHtml(t(`experiment.${item.id}.title`, item.title || item.id))}</span>
        <span class="status ${escapeAttr(outputHasArtifacts(item) ? "completed" : "missing")}">${escapeHtml(outputHasArtifacts(item) ? t("status.completed", "completed") : t("status.missing", "missing"))}</span>
      </summary>
      <section class="output-card ${item.output_dir ? "" : "muted-card"}">
        <div>
          <p class="muted">${escapeHtml(item.hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${item.hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
          <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(item.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
          <p class="muted">${escapeHtml(t("text.output_summary", "Output"))}: ${item.counts.reports} ${escapeHtml(t("section.reports", "Reports"))}, ${item.counts.evidence} evidence, ${item.counts.tables} CSV</p>
          <p class="muted">${escapeHtml(t("text.filtered_evidence", "Files shown"))}: ${item._evidenceFiltered.length + item._tablesFiltered.length + item._configsFiltered.length}/${item.evidence.length + item.tables.length + item.configs.length}</p>
        </div>
        <div class="artifact-groups">
          <details open>
            <summary>${escapeHtml(t("section.evidence_browser", "Evidence Browser"))} (${item._evidenceFiltered.length})</summary>
            ${renderArtifactButtons(item._evidenceFiltered, "evidencePreview", "evidence")}
          </details>
          <details>
            <summary>${escapeHtml(t("section.results_explorer", "Results Explorer"))} (${item._tablesFiltered.length})</summary>
            ${renderArtifactButtons(item._tablesFiltered, "tablePreview", "table")}
          </details>
          <details>
            <summary>${escapeHtml(t("section.configuration", "Configuration"))} (${item._configsFiltered.length})</summary>
            ${renderArtifactButtons(item._configsFiltered, "evidencePreview", "report")}
          </details>
        </div>
      </section>
    </details>
  `).join("");
}

function renderArtifactButtons(files, previewId, mode = "report") {
  if (!files.length) return `<p class="muted">${escapeHtml(t("text.no_files", "No files yet."))}</p>`;
  return `<div class="compact-file-list">${files.map((file) => `
    <div class="compact-file">
      <code>${escapeHtml(file.name)}</code>
      ${mode === "evidence" ? actionButton("preview-evidence", t("button.browse", "Browse"), { path: file.path }) : ""}
      ${mode === "table" ? actionButton("preview-table", t("button.preview", "Preview"), { path: file.path, target: previewId }) : ""}
      ${mode === "report" ? actionButton("preview-report", t("button.open", "Open"), { path: file.path, target: previewId }) : ""}
    </div>
  `).join("")}</div>`;
}

function renderRunManifests() {
  const target = document.getElementById("runManifestList");
  if (!target) return;
  const manifests = state.summary.run_manifests || [];
  if (!manifests.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_run_manifests", "No run manifests found."))}</p>`;
    return;
  }
  target.innerHTML = manifests.map((manifest) => `
    <div class="run-item">
      <div>
        <strong>${escapeHtml(manifest.experiment_id || manifest.title || "run")}</strong><br>
        <code>${escapeHtml(manifest.path)}</code><br>
        <span class="muted">${escapeHtml(manifest.runner || "")} / ${escapeHtml(JSON.stringify(manifest.params || {}))}</span>
      </div>
      <div class="button-row">
        <button data-manifest-open="${escapeAttr(manifest.path)}">${escapeHtml(t("button.open", "Open"))}</button>
        <button data-manifest-a="${escapeAttr(manifest.path)}">${escapeHtml(t("button.compare_a", "A"))}</button>
        <button data-manifest-b="${escapeAttr(manifest.path)}">${escapeHtml(t("button.compare_b", "B"))}</button>
      </div>
    </div>
  `).join("");
  target.querySelectorAll("[data-manifest-open]").forEach((button) => {
    button.addEventListener("click", () => previewReport(button.dataset.manifestOpen, "runLog", button));
  });
  target.querySelectorAll("[data-manifest-a]").forEach((button) => {
    button.addEventListener("click", () => selectManifest("A", button.dataset.manifestA));
  });
  target.querySelectorAll("[data-manifest-b]").forEach((button) => {
    button.addEventListener("click", () => selectManifest("B", button.dataset.manifestB));
  });
}

function renderSafetyModel() {
  const target = document.getElementById("safetyModel");
  if (!target) return;
  const safety = state.summary.safety || {};
  target.innerHTML = `
    <div class="status-grid">
      <div class="readiness ready"><strong>${escapeHtml(t("text.mode", "mode"))}</strong><span>${escapeHtml(safety.execution_model || "")}</span></div>
      <div class="readiness ready"><strong>${escapeHtml(t("text.read", "read"))}</strong><span>${escapeHtml((safety.allowed_read_roots || []).join(", "))}</span></div>
      <div class="readiness ready"><strong>${escapeHtml(t("text.write", "write"))}</strong><span>${escapeHtml((safety.allowed_write_roots || []).join(", "))}</span></div>
    </div>
    <h3>${escapeHtml(t("text.forbidden_actions", "Forbidden actions"))}</h3>
    <ul>${(safety.forbidden || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h3>${escapeHtml(t("text.review_gates", "Review gates"))}</h3>
    <ul>${(safety.review_gates || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
  `;
}

async function selectManifest(slot, path) {
  if (slot === "A") state.compareA = path;
  if (slot === "B") state.compareB = path;
  document.getElementById("runCompareSelection").textContent = `A: ${state.compareA || "-"} / B: ${state.compareB || "-"}`;
  if (state.compareA && state.compareB) await compareRunManifests();
}

async function compareRunManifests() {
  const params = new URLSearchParams({ a: state.compareA, b: state.compareB });
  const response = await fetch(`/api/run-compare?${params.toString()}`);
  const payload = await response.json();
  const target = document.getElementById("runCompareResult");
  if (payload.error) {
    target.innerHTML = `<p class="status failed">${escapeHtml(payload.error)}</p>`;
    return;
  }
  if (!payload.differences.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_differences", "No differences in compared manifest summary fields."))}</p>`;
    return;
  }
  target.innerHTML = `<div class="table-wrap"><table><thead><tr><th>${escapeHtml(t("text.field", "Field"))}</th><th>A</th><th>B</th></tr></thead>
    <tbody>${payload.differences.map((item) => `<tr><td>${escapeHtml(item.field)}</td><td>${escapeHtml(JSON.stringify(item.a))}</td><td>${escapeHtml(JSON.stringify(item.b))}</td></tr>`).join("")}</tbody></table></div>`;
}

async function startExperiment(experiment, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    document.getElementById("runLog").textContent = `${t("message.starting", "Starting")} ${experiment}...`;
    const params = collectExperimentParams(experiment);
    try {
      state.autoOpenExperiment = experiment;
      state.autoOpenTarget = experiment === "toponym_research_workflow" || experiment === "sampling_coding"
        ? "toponymResearchPreview"
        : "reportPreview";
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment, params }),
      });
      const run = await response.json();
      if (!response.ok) {
        document.getElementById("runLog").textContent = run.error || t("message.failed_start_experiment", "Failed to start experiment.");
        showToast(run.error || t("message.failed_start_experiment", "Failed to start experiment."), "error", 4200);
        return;
      }
      state.selectedRun = run.id;
      showToast(`${t("message.run_started", "Run started")}: ${experimentTitle(experiment)}`, "info");
      await pollRuns(true);
    } catch (error) {
      document.getElementById("runLog").textContent = `${t("message.failed_start_experiment", "Failed to start experiment.")}: ${error}`;
      showToast(`${t("message.failed_start_experiment", "Failed to start experiment.")}: ${error}`, "error", 4200);
    }
  });
}

async function startRun(preset, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    document.getElementById("runLog").textContent = `${t("message.starting", "Starting")} ${preset}...`;
    try {
      state.autoOpenExperiment = null;
      state.autoOpenTarget = "reportPreview";
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset }),
      });
      const run = await response.json();
      if (!response.ok) {
        document.getElementById("runLog").textContent = run.error || t("message.failed_start_run", "Failed to start run.");
        showToast(run.error || t("message.failed_start_run", "Failed to start run."), "error", 4200);
        return;
      }
      state.selectedRun = run.id;
      showToast(`${t("message.run_started", "Run started")}: ${run.label || preset}`, "info");
      await pollRuns(true);
    } catch (error) {
      document.getElementById("runLog").textContent = `${t("message.failed_start_run", "Failed to start run.")}: ${error}`;
      showToast(`${t("message.failed_start_run", "Failed to start run.")}: ${error}`, "error", 4200);
    }
  });
}

async function pollRuns(force = false) {
  if (state.polling && !force) return;
  state.polling = true;
  const response = await fetch("/api/runs");
  const payload = await response.json();
  const previousStatuses = { ...state.runStatusById };
  state.runs = payload.runs || [];
  state.runStatusById = Object.fromEntries((state.runs || []).map((run) => [run.id, run.status]));
  notifyRunTransitions(previousStatuses, state.runs);
  if (state.summary) {
    refreshResearchSessionSummary();
  }
  if (!state.selectedRun && payload.runs.length) state.selectedRun = payload.runs[0].id;
  renderRuns(payload.runs);
  const selectedRun = payload.runs.find((run) => run.id === state.selectedRun);
  if (state.selectedRun) {
    const log = await fetch(`/api/run-log?id=${encodeURIComponent(state.selectedRun)}`);
    document.getElementById("runLog").textContent = await log.text();
  }
  if (selectedRun && selectedRun.status !== "running" && state.autoOpenExperiment && selectedRun.preset === state.autoOpenExperiment) {
    const experimentId = state.autoOpenExperiment;
    const target = state.autoOpenTarget;
    state.autoOpenExperiment = null;
    state.autoOpenTarget = "reportPreview";
    await loadSummary();
    await openPrimaryReportForExperiment(experimentId, target);
  }
  state.polling = false;
  if (payload.runs.some((run) => run.status === "running")) setTimeout(() => pollRuns(), 1500);
}

function notifyRunTransitions(previousStatuses, runs) {
  for (const run of runs || []) {
    if (!run?.id) continue;
    const previous = previousStatuses[run.id];
    const current = run.status || "";
    if (previous === "running" && current !== "running" && !state.notifiedRunFinal[run.id]) {
      if (current === "completed") {
        showToast(`${t("message.run_completed", "Run completed")}: ${run.label || run.preset || run.id}`, "success");
      } else if (current.startsWith("failed")) {
        showToast(`${t("message.run_failed", "Run failed")}: ${run.label || run.preset || run.id}`, "error", 4200);
      }
      state.notifiedRunFinal[run.id] = true;
    }
  }
}

async function openPrimaryReportForExperiment(experimentId, preferredTarget = "reportPreview") {
  const output = (state.summary?.experiment_outputs || []).find((item) => item.id === experimentId);
  if (!output?.primary_report?.path) return;
  const target = document.getElementById(preferredTarget) ? preferredTarget : "reportPreview";
  setActiveTab(target === "toponymResearchPreview" ? "toponymResearch" : "reports");
  await previewReport(output.primary_report.path, target);
}

async function focusExperimentReports(experimentId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.reportExperimentFilter = experimentId || "all";
    setActiveTab("reports");
    renderExperimentOutputs();
    if (!experimentId || experimentId === "all") return;
    await openPrimaryReportForExperiment(experimentId, "reportPreview");
  });
}

async function focusExperimentEvidence(experimentId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.evidenceExperimentFilter = experimentId || "all";
    setActiveTab("evidence");
    renderExperimentOutputs();
  });
}

function renderRuns(runs) {
  const target = document.getElementById("runList");
  if (!target) return;
  if (!runs.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_runs", "No runs yet."))}</p>`;
    return;
  }
  target.innerHTML = runs.slice(0, 12).map((run) => {
    const statusClass = run.status.startsWith("failed") ? "failed" : run.status;
    return `<div class="run-item">
      <div><strong>${escapeHtml(run.label)}</strong><br><code>${escapeHtml(run.id)}</code></div>
      <button class="status ${escapeAttr(statusClass)}" data-run="${escapeAttr(run.id)}">${escapeHtml(t(`status.${statusClass}`, run.status))}</button>
    </div>`;
  }).join("");
  target.querySelectorAll("[data-run]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedRun = button.dataset.run;
      await pollRuns(true);
    });
  });
}

function renderFiles(targetId, files, previewId) {
  const target = document.getElementById(targetId);
  if (!files.length) {
    target.innerHTML = `<p>${escapeHtml(t("text.no_files", "No files yet."))}</p>`;
    return;
  }
  target.innerHTML = `<div class="file-list">${files.map((file) => `
    <div class="file">
      <div><strong>${escapeHtml(file.name)}</strong><br><code>${escapeHtml(file.path)}</code></div>
      ${previewId === "evidencePreview" && (file.name.endsWith(".csv") || file.name.endsWith(".json")) ? actionButton("preview-evidence", t("button.browse", "Browse"), { path: file.path }) : ""}
      ${previewId !== "evidencePreview" && file.name.endsWith(".csv") ? actionButton("preview-table", t("button.preview", "Preview"), { path: file.path, target: previewId }) : ""}
      ${previewId !== "evidencePreview" && (file.name.endsWith(".md") || file.name.endsWith(".json")) ? actionButton("preview-report", t("button.open", "Open"), { path: file.path, target: previewId }) : ""}
      ${previewId === "reportPreview" && (file.name.endsWith(".md") || file.name.endsWith(".json") || file.name.endsWith(".csv")) ? actionButton("add-report", t("button.add", "Add"), { path: file.path }) : ""}
    </div>
  `).join("")}</div>`;
}

async function previewTable(path, targetId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    if (targetId === "tablePreview") state.selectedTablePath = path;
    const params = new URLSearchParams({ path });
    if (targetId === "tablePreview") {
      params.set("q", document.getElementById("tableFilterInput")?.value || "");
      params.set("limit", document.getElementById("tableLimitInput")?.value || "100");
    }
    const response = await fetch(`/api/table?${params.toString()}`);
    const payload = await response.json();
    const target = document.getElementById(targetId);
    const meta = document.getElementById("tableMeta");
    if (payload.error) {
      target.textContent = payload.error;
      if (meta && targetId === "tablePreview") meta.textContent = "";
      return;
    }
    if (meta && targetId === "tablePreview") {
      meta.textContent = `${payload.returned_rows} ${t("text.rows_shown", "rows shown")} / ${payload.scanned_rows} ${t("text.rows_scanned", "rows scanned")} / ${formatBytes(payload.size)}`;
    }
    if (!payload.rows.length) {
      target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_matching_rows", "No matching rows."))}</p>`;
      return;
    }
    target.innerHTML = `<div class="table-wrap"><table><thead><tr>${payload.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
      <tbody>${payload.rows.map((row) => `<tr>${payload.columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  });
}

async function previewReport(path, targetId = "reportPreview", triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const response = await fetch(`/api/report?path=${encodeURIComponent(path)}`);
    document.getElementById(targetId).textContent = await response.text();
  });
}

async function previewEvidence(path, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.selectedEvidencePath = path;
    const params = new URLSearchParams({
      path,
      source: document.getElementById("evidenceSourceInput")?.value || "",
      toponym: document.getElementById("evidenceToponymInput")?.value || "",
      sentiment: document.getElementById("evidenceSentimentInput")?.value || "",
      driver: document.getElementById("evidenceDriverInput")?.value || "",
      topic: document.getElementById("evidenceTopicInput")?.value || "",
      text: document.getElementById("evidenceTextInput")?.value || "",
      limit: document.getElementById("evidenceLimitInput")?.value || "100",
    });
    const response = await fetch(`/api/evidence?${params.toString()}`);
    const payload = await response.json();
    const target = document.getElementById("evidencePreview");
    const meta = document.getElementById("evidenceMeta");
    if (payload.error) {
      target.textContent = payload.error;
      meta.textContent = "";
      return;
    }
    meta.textContent = `${payload.returned_rows} ${t("text.rows_shown", "rows shown")} / ${payload.total_rows} ${t("text.evidence_rows", "evidence rows")}`;
    if (!payload.rows.length) {
      target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_matching_evidence", "No matching evidence."))}</p>`;
      return;
    }
    target.innerHTML = `<div class="table-wrap"><table><thead><tr>${payload.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
      <tbody>${payload.rows.map((row) => `<tr>${payload.columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  });
}

function addReportToBundle(path) {
  if (!state.selectedReports.includes(path)) state.selectedReports.push(path);
  renderSelectedReports();
}

function removeReportFromBundle(path) {
  state.selectedReports = state.selectedReports.filter((item) => item !== path);
  renderSelectedReports();
}

function renderSelectedReports() {
  const target = document.getElementById("selectedReports");
  if (!target) return;
  if (!state.selectedReports.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_selected_reports", "No selected reports."))}</p>`;
    return;
  }
  target.innerHTML = state.selectedReports.map((path) => `
    <div class="selected-item">
      <code>${escapeHtml(path)}</code>
      ${actionButton("remove-report", t("button.remove", "Remove"), { path })}
    </div>
  `).join("");
}

async function buildReportBundle(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const status = document.getElementById("reportBundleStatus");
    status.textContent = t("message.building_bundle", "Building bundle...");
    const response = await fetch("/api/report-bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: document.getElementById("reportBundleTitle").value,
        paths: state.selectedReports,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload.error) {
      status.textContent = payload.error || t("message.failed_build_bundle", "Failed to build report bundle.");
      return;
    }
    status.textContent = `${t("message.bundle_created", "Bundle created")}: ${payload.path} (${payload.count} ${t("text.files", "files")})`;
    await previewReport(payload.path, "reportPreview");
  });
}

function formatNumber(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatDateTime(value) {
  const number = Number(value || 0);
  if (!number) return "";
  try {
    const locale = state.lang === "ru" ? "ru-RU" : "en-US";
    return new Intl.DateTimeFormat(locale, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(number * 1000));
  } catch (_) {
    return "";
  }
}

function formatBytes(value) {
  const number = Number(value || 0);
  if (number < 1024) return `${number} B`;
  if (number < 1024 * 1024) return `${(number / 1024).toFixed(1)} KB`;
  return `${(number / 1024 / 1024).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/\\/g, "\\\\");
}

function actionButton(action, label, options = {}) {
  const path = options.path || "";
  const target = options.target || "";
  const experiment = options.experiment || "";
  const classes = options.classes || "";
  return `<button${classes ? ` class="${escapeAttr(classes)}"` : ""} data-action="${escapeAttr(action)}"${path ? ` data-path="${escapeAttr(path)}"` : ""}${target ? ` data-target="${escapeAttr(target)}"` : ""}${experiment ? ` data-experiment="${escapeAttr(experiment)}"` : ""}>${escapeHtml(label)}</button>`;
}

loadLanguagePack().then(() => loadSummary()).then(() => pollRuns(true));
