const savedUiFilters = (() => {
  try {
    const raw = localStorage.getItem("webapp.uiFilters");
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
})();

const savedSelectedReports = (() => {
  try {
    const raw = localStorage.getItem("webapp.reportBundleSelection");
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    const clean = [];
    const seen = new Set();
    for (const item of parsed) {
      if (typeof item !== "string") continue;
      const path = item.trim();
      if (!path || seen.has(path)) continue;
      seen.add(path);
      clean.push(path);
      if (clean.length >= 200) break;
    }
    return clean;
  } catch (_) {
    return [];
  }
})();

const savedExperimentParamDrafts = (() => {
  try {
    const raw = localStorage.getItem("webapp.experimentParamDrafts");
    const parsed = raw ? JSON.parse(raw) : {};
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const clean = {};
    for (const [experimentId, values] of Object.entries(parsed)) {
      if (!values || typeof values !== "object" || Array.isArray(values)) continue;
      clean[experimentId] = {};
      for (const [name, value] of Object.entries(values)) {
        if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
          clean[experimentId][name] = value;
        }
      }
    }
    return clean;
  } catch (_) {
    return {};
  }
})();

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
  selectedReports: savedSelectedReports,
  experimentParamDrafts: savedExperimentParamDrafts,
  reportVisiblePrimaryPaths: [],
  runEvidenceDigestByRun: {},
  runComparisonBoardByRun: {},
  runSeriesBoardByRun: {},
  hypothesisSessionsByRun: {},
  hypothesisMatrixByRun: {},
  hypothesisCompareByContext: {},
  recentArtifacts: (() => {
    try {
      const raw = localStorage.getItem("webapp.recentArtifacts");
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed.slice(0, 20) : [];
    } catch (_) {
      return [];
    }
  })(),
  reportExperimentFilter: typeof savedUiFilters.reportExperimentFilter === "string" ? savedUiFilters.reportExperimentFilter : "all",
  evidenceExperimentFilter: typeof savedUiFilters.evidenceExperimentFilter === "string" ? savedUiFilters.evidenceExperimentFilter : "all",
  reportRunFilter: typeof savedUiFilters.reportRunFilter === "string" ? savedUiFilters.reportRunFilter : "all",
  evidenceRunFilter: typeof savedUiFilters.evidenceRunFilter === "string" ? savedUiFilters.evidenceRunFilter : "all",
  reportArtifactFilter: typeof savedUiFilters.reportArtifactFilter === "string" ? savedUiFilters.reportArtifactFilter : "",
  evidenceArtifactFilter: typeof savedUiFilters.evidenceArtifactFilter === "string" ? savedUiFilters.evidenceArtifactFilter : "",
  reportFilterPreset: typeof savedUiFilters.reportFilterPreset === "string" ? savedUiFilters.reportFilterPreset : "all",
  evidenceFilterPreset: typeof savedUiFilters.evidenceFilterPreset === "string" ? savedUiFilters.evidenceFilterPreset : "all",
  reportExpandAll: Boolean(savedUiFilters.reportExpandAll),
  evidenceExpandAll: Boolean(savedUiFilters.evidenceExpandAll),
  reportWorkflowOnly: Boolean(savedUiFilters.reportWorkflowOnly),
  evidenceWorkflowOnly: Boolean(savedUiFilters.evidenceWorkflowOnly),
  reportIncludeInactive: Boolean(savedUiFilters.reportIncludeInactive),
  evidenceIncludeInactive: Boolean(savedUiFilters.evidenceIncludeInactive),
  runSeriesLimit: [3, 5, 7, 10].includes(Number(savedUiFilters.runSeriesLimit)) ? Number(savedUiFilters.runSeriesLimit) : 5,
  autoOpenExperiment: null,
  autoOpenTarget: "reportPreview",
  lang: localStorage.getItem("webapp.language") || "ru",
  i18n: {},
};

function persistUiFilters() {
  try {
    localStorage.setItem("webapp.uiFilters", JSON.stringify({
      reportExperimentFilter: state.reportExperimentFilter,
      evidenceExperimentFilter: state.evidenceExperimentFilter,
      reportRunFilter: state.reportRunFilter,
      evidenceRunFilter: state.evidenceRunFilter,
      reportArtifactFilter: state.reportArtifactFilter,
      evidenceArtifactFilter: state.evidenceArtifactFilter,
      reportFilterPreset: state.reportFilterPreset,
      evidenceFilterPreset: state.evidenceFilterPreset,
      reportExpandAll: state.reportExpandAll,
      evidenceExpandAll: state.evidenceExpandAll,
      reportWorkflowOnly: state.reportWorkflowOnly,
      evidenceWorkflowOnly: state.evidenceWorkflowOnly,
      reportIncludeInactive: state.reportIncludeInactive,
      evidenceIncludeInactive: state.evidenceIncludeInactive,
      runSeriesLimit: state.runSeriesLimit,
    }));
  } catch (_) {
    // ignore local persistence issues
  }
}

function persistSelectedReports() {
  try {
    const clean = [];
    const seen = new Set();
    for (const item of state.selectedReports) {
      if (typeof item !== "string") continue;
      const path = item.trim();
      if (!path || seen.has(path)) continue;
      seen.add(path);
      clean.push(path);
      if (clean.length >= 200) break;
    }
    state.selectedReports = clean;
    localStorage.setItem("webapp.reportBundleSelection", JSON.stringify(clean));
  } catch (_) {
    // ignore local persistence issues
  }
}

function clearRunEvidenceDigestCache() {
  state.runEvidenceDigestByRun = {};
}

function clearRunComparisonBoardCache() {
  state.runComparisonBoardByRun = {};
}

function clearRunSeriesBoardCache() {
  state.runSeriesBoardByRun = {};
}

function clearHypothesisSessionsCache() {
  state.hypothesisSessionsByRun = {};
}

function clearHypothesisMatrixCache() {
  state.hypothesisMatrixByRun = {};
}

function clearHypothesisCompareCache() {
  state.hypothesisCompareByContext = {};
}

function persistExperimentParamDrafts() {
  try {
    localStorage.setItem("webapp.experimentParamDrafts", JSON.stringify(state.experimentParamDrafts || {}));
  } catch (_) {
    // ignore local persistence issues
  }
}

function setExperimentParamDraft(experimentId, paramName, value) {
  if (!experimentId || !paramName) return;
  if (!state.experimentParamDrafts[experimentId]) state.experimentParamDrafts[experimentId] = {};
  state.experimentParamDrafts[experimentId][paramName] = value;
  persistExperimentParamDrafts();
}

function getExperimentParamDraft(experimentId, paramName) {
  return state.experimentParamDrafts?.[experimentId]?.[paramName];
}

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

document.addEventListener("input", (event) => {
  const input = event.target?.closest?.("[data-param-experiment][data-param-name]");
  if (!input) return;
  const experimentId = input.dataset.paramExperiment || "";
  const paramName = input.dataset.paramName || "";
  const value = input.type === "number" ? Number(input.value) : input.value;
  setExperimentParamDraft(experimentId, paramName, value);
});

document.addEventListener("change", (event) => {
  const baselineSelect = event.target?.closest?.("select[data-action='set-comparison-baseline']");
  if (baselineSelect) {
    void setComparisonBaseline(baselineSelect);
    return;
  }
  const seriesLimitSelect = event.target?.closest?.("select[data-action='set-run-series-limit']");
  if (seriesLimitSelect) {
    const nextValue = Number(seriesLimitSelect.value || 5);
    state.runSeriesLimit = [3, 5, 7, 10].includes(nextValue) ? nextValue : 5;
    clearRunSeriesBoardCache();
    persistUiFilters();
    renderRunFocusedResult();
    return;
  }
  const input = event.target?.closest?.("[data-param-experiment][data-param-name]");
  if (!input) return;
  const experimentId = input.dataset.paramExperiment || "";
  const paramName = input.dataset.paramName || "";
  const value = input.type === "number" ? Number(input.value) : input.value;
  setExperimentParamDraft(experimentId, paramName, value);
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
document.getElementById("reportBundleAddWorkflow")?.addEventListener("click", (event) => addWorkflowReportsToBundle(event.currentTarget));
document.getElementById("reportBundleAddVisible")?.addEventListener("click", (event) => addVisibleReportsToBundle(event.currentTarget));
document.getElementById("reportBundleClearSelected")?.addEventListener("click", (event) => clearSelectedReports(event.currentTarget));
document.getElementById("runCompareExportButton")?.addEventListener("click", (event) => buildRunComparison(event.currentTarget));
document.getElementById("clearRecentArtifacts")?.addEventListener("click", () => {
  state.recentArtifacts = [];
  persistRecentArtifacts();
  renderRecentArtifacts();
});
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
document.getElementById("reportRunFilter")?.addEventListener("change", (event) => {
  state.reportRunFilter = event.target.value || "all";
  markReportPresetCustom();
  renderExperimentReports();
});
document.getElementById("evidenceRunFilter")?.addEventListener("change", (event) => {
  state.evidenceRunFilter = event.target.value || "all";
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
document.getElementById("reportPresetCurrentRun")?.addEventListener("click", () => applyReportCurrentRunPreset());
document.getElementById("evidencePresetWorkflow")?.addEventListener("click", () => applyEvidenceFilterPreset("workflow"));
document.getElementById("evidencePresetAll")?.addEventListener("click", () => applyEvidenceFilterPreset("all"));
document.getElementById("evidencePresetCurrentRun")?.addEventListener("click", () => applyEvidenceCurrentRunPreset());
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

function runStatusClass(value) {
  const raw = String(value || "");
  if (raw.startsWith("failed")) return "failed";
  if (raw === "running") return "running";
  if (raw === "completed") return "completed";
  return "missing";
}

function outputWithRunContext(item) {
  const latest = latestRunsByPreset();
  return { ...item, _run: latest[item.id] || null };
}

function outputByExperimentId(experimentId) {
  return (state.summary?.experiment_outputs || []).find((item) => item.id === experimentId);
}

function experimentTitle(experimentId) {
  const fromSummary = (state.summary?.experiments || []).find((item) => item.id === experimentId);
  return t(`experiment.${experimentId}.title`, fromSummary?.title || experimentId);
}

function experimentRunStatus(experimentId, output) {
  const latest = latestRunsByPreset()[experimentId];
  if (latest?.status) return runStatusClass(latest.status);
  return output?.primary_report ? "completed" : "missing";
}

function renderExperimentCounts(output) {
  const reportsCount = (output?.reports || []).length;
  const tablesCount = (output?.tables || []).length;
  const evidenceCount = (output?.evidence || []).length;
  return `${t("section.reports", "Reports")}: ${reportsCount} / ${t("section.results_explorer", "Results Explorer")}: ${tablesCount} / ${t("section.evidence_browser", "Evidence Browser")}: ${evidenceCount}`;
}

function formatParamSummary(params, maxItems = 3) {
  if (!params || typeof params !== "object") return "-";
  const entries = Object.entries(params);
  if (!entries.length) return "-";
  const short = entries.slice(0, maxItems).map(([key, value]) => `${key}=${String(value)}`);
  const tail = entries.length > maxItems ? ` +${entries.length - maxItems}` : "";
  return `${short.join(", ")}${tail}`;
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
  if (action === "move-report-up") {
    moveReportInBundle(path, -1);
    return;
  }
  if (action === "move-report-down") {
    moveReportInBundle(path, 1);
    return;
  }
  if (action === "run-manual-coding") {
    await startManualCodingSample(button);
    return;
  }
  if (action === "run-experiment") {
    await startExperiment(button.dataset.experiment || "", button);
    return;
  }
  if (action === "show-experiment-reports") {
    await focusExperimentReports(button.dataset.experiment || "", button);
    return;
  }
  if (action === "show-experiment-evidence") {
    await focusExperimentEvidence(button.dataset.experiment || "", button);
    return;
  }
  if (action === "reuse-last-params") {
    applyParamsToExperimentInputs(button.dataset.experiment || "", button.dataset.params || "");
    return;
  }
  if (action === "copy-last-params") {
    await copyParamsFromButton(button);
    return;
  }
  if (action === "build-run-packet") {
    await buildRunPacket(button);
    return;
  }
  if (action === "reset-experiment-params") {
    resetExperimentParams(button.dataset.experiment || "");
    return;
  }
  if (action === "open-recent-artifact") {
    await openRecentArtifact(button.dataset.path || "", button.dataset.target || "", button.dataset.experiment || "", button);
    return;
  }
  if (action === "remove-recent-artifact") {
    removeRecentArtifact(button.dataset.path || "", button.dataset.experiment || "");
    return;
  }
  if (action === "focus-run-reports") {
    await focusRunOutputs(button.dataset.target || "", "reports");
    return;
  }
  if (action === "focus-run-evidence") {
    await focusRunOutputs(button.dataset.target || "", "evidence");
    return;
  }
  if (action === "prepare-coding-from-run") {
    await prepareManualCodingFromRun(button.dataset.target || "");
    return;
  }
  if (action === "open-result-pack") {
    await openResultPack(button.dataset.experiment || "", button.dataset.target || "", button);
    return;
  }
  if (action === "open-run-log") {
    await openRunLog(button.dataset.target || "", button);
    return;
  }
  if (action === "focus-hypothesis-run") {
    await focusHypothesisRun(button.dataset.target || "", button.dataset.experiment || "", button);
    return;
  }
  if (action === "export-hypothesis-session") {
    await exportHypothesisSession(
      button.dataset.experiment || "",
      button.dataset.target || "",
      button.dataset.sessionKey || "",
      button,
    );
    return;
  }
  if (action === "export-hypothesis-matrix") {
    await exportHypothesisMatrix(
      button.dataset.experiment || "",
      button.dataset.target || "",
      button,
    );
    return;
  }
  if (action === "compare-hypothesis-sessions") {
    await runHypothesisCompare(button.dataset.target || "", button.dataset.experiment || "", button);
    return;
  }
  if (action === "export-hypothesis-compare") {
    await exportHypothesisCompareFromControls(button.dataset.target || "", button.dataset.experiment || "", button);
    return;
  }
  if (action === "export-run-series") {
    await exportRunSeries(button.dataset.experiment || "", button.dataset.target || "", state.runSeriesLimit, button);
    return;
  }
  if (action === "use-toponym-for-coding") {
    useToponymForCoding(button.dataset.target || "");
    return;
  }
});

async function loadSummary() {
  const response = await fetch("/api/summary");
  state.summary = await response.json();
  clearRunEvidenceDigestCache();
  clearRunComparisonBoardCache();
  clearRunSeriesBoardCache();
  clearHypothesisSessionsCache();
  clearHypothesisMatrixCache();
  clearHypothesisCompareCache();
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
  renderRecentArtifacts();
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
  const latest = latestRunsByPreset();
  target.innerHTML = experiments.map((experiment) => {
    const output = outputByExperimentId(experiment.id);
    const run = latest[experiment.id] || null;
    const statusClass = experimentRunStatus(experiment.id, output);
    const statusLabel = workflowStepStatusLabel(statusClass);
    const runIsCompleted = statusClass === "completed";
    const lastRunAt = formatDateTime(run?.created_at || output?.last_run_at) || t("text.not_run_yet", "Not run yet.");
    const keyTable = output?.key_table || (output?.tables || [])[0];
    const keyEvidence = output?.key_evidence || (output?.evidence || [])[0];
    const hasReusableParams = Boolean(output?.last_params && Object.keys(output.last_params).length);
    const currentRunReportsLabel = `${t("button.current_run", "Current run")} / ${t("section.reports", "Reports")}`;
    const currentRunEvidenceLabel = `${t("button.current_run", "Current run")} / ${t("section.evidence_browser", "Evidence Browser")}`;
    return `
    <section class="panel preset experiment-card">
      <div>
        <h2>${escapeHtml(t(`experiment.${experiment.id}.title`, experiment.title))}</h2>
        <p>${escapeHtml(experiment.id)} / ${escapeHtml(experiment.runner)} / ${escapeHtml(t(`status.${experiment.status}`, experiment.status || "unknown"))}</p>
        <code>${escapeHtml(experiment.agent_contract)}</code>
        <div class="experiment-meta-grid">
          <span class="status ${escapeAttr(statusClass)}">${escapeHtml(statusLabel)}</span>
          <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(lastRunAt)}</p>
          <p class="muted">${escapeHtml(t("label.run_id", "Run ID"))}: ${escapeHtml(run?.id || "-")}</p>
          <p class="muted">${escapeHtml(t("text.outputs", "Outputs"))}: ${escapeHtml(output?.output_dir || t("text.not_run_yet", "Not run yet."))}</p>
          <p class="muted">${escapeHtml(t("text.last_params", "Last params"))}: ${escapeHtml(formatParamSummary(output?.last_params || {}))}</p>
          <p class="muted">${escapeHtml(renderExperimentCounts(output))}</p>
        </div>
        <p class="muted">${escapeHtml(t("text.outputs", "Outputs"))}: ${escapeHtml((experiment.expected_outputs || []).join(", "))}</p>
        <div class="param-grid">${renderParameterInputs(experiment)}</div>
      </div>
      <div class="button-row experiment-actions">
        <button class="primary experiment-button" data-experiment="${escapeAttr(experiment.id)}">${escapeHtml(t("button.run", "Run"))}</button>
        ${hasReusableParams ? actionButton("reuse-last-params", t("button.reuse_last_params", "Reuse last params"), { experiment: experiment.id, params: JSON.stringify(output.last_params) }) : ""}
        ${hasReusableParams ? actionButton("copy-last-params", t("button.copy_params", "Copy params"), { experiment: experiment.id, params: JSON.stringify(output.last_params) }) : ""}
        ${output?.manifest_path ? actionButton("build-run-packet", t("button.build_run_packet", "Build run packet"), { experiment: experiment.id, path: output.manifest_path }) : ""}
        ${actionButton("reset-experiment-params", t("button.reset_params", "Reset params"), { experiment: experiment.id })}
        ${output?.primary_report || keyTable || keyEvidence ? actionButton("open-result-pack", t("button.open_result_pack", "Open result pack"), { experiment: experiment.id, target: run?.id || "", classes: "primary" }) : ""}
        ${run?.id ? actionButton("focus-run-reports", currentRunReportsLabel, { target: run.id, disabled: !runIsCompleted }) : ""}
        ${run?.id ? actionButton("focus-run-evidence", currentRunEvidenceLabel, { target: run.id, disabled: !runIsCompleted }) : ""}
        ${run?.id && (experiment.id === "toponym_research_workflow" || experiment.id === "research_story_e2e")
          ? actionButton("prepare-coding-from-run", t("button.open_manual_coding", "Open manual coding step"), { target: run.id, disabled: !runIsCompleted })
          : ""}
        ${output?.manifest_path ? actionButton("preview-report", t("button.open_manifest", "Open manifest"), { path: output.manifest_path, target: "reportPreview" }) : ""}
        ${output?.primary_report ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "reportPreview" }) : ""}
        ${keyTable ? actionButton("preview-table", t("button.preview_result", "Preview result"), { path: keyTable.path, target: "tablePreview" }) : ""}
        ${keyEvidence ? actionButton("preview-evidence", t("button.browse", "Browse"), { path: keyEvidence.path }) : ""}
        ${actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: experiment.id })}
        ${actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: experiment.id })}
      </div>
    </section>
  `;
  }).join("");
  target.querySelectorAll(".experiment-button").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment, button));
  });
}

function renderToponymResearch() {
  const target = document.getElementById("toponymResearchPanel");
  if (!target) return;
  const experiment = (state.summary.experiments || []).find((item) => item.id === "toponym_research_workflow");
  const output = (state.summary.experiment_outputs || []).find((item) => item.id === "toponym_research_workflow");
  const e2eExperiment = (state.summary.experiments || []).find((item) => item.id === "research_story_e2e");
  const e2eOutput = (state.summary.experiment_outputs || []).find((item) => item.id === "research_story_e2e");
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
    ${renderResearchStoryE2E(e2eExperiment, e2eOutput)}
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
    <section class="panel" id="manualCodingStepPanel">
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

function renderResearchStoryE2E(experiment, output) {
  if (!experiment) return "";
  const run = latestRunForExperiment(experiment.id);
  const runStatus = run ? runStatusClass(run.status) : "missing";
  const runIsCompleted = runStatus === "completed";
  const summaryJson = (output?.configs || []).find((file) => file.name === "research_story_e2e_summary.json");
  const stepsCsv = (output?.tables || []).find((file) => file.name === "research_story_e2e_steps.csv");
  const codingSample = (output?.tables || []).find((file) => file.name === "coding_sample_by_toponym.csv")
    || (output?.tables || []).find((file) => file.name === "coding_sample.csv");
  const hypothesis = output?.last_params?.hypothesis || "";
  return `
    <section class="output-card">
      <div>
        <h3>${escapeHtml(t("section.research_story_e2e", "One-click research story (E2E)"))}</h3>
        <p class="muted">${escapeHtml(t("text.research_story_e2e_hint", "Run the full researcher chain in one launch: corpus prep -> toponyms -> place perception -> migration narratives -> coding sample."))}</p>
        <p class="muted">${escapeHtml(hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
        <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(output?.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
        <p class="muted">${escapeHtml(output?.output_dir || t("text.not_run_yet", "Not run yet."))}</p>
        <div class="param-grid">${renderParameterInputs(experiment)}</div>
      </div>
      <div class="button-row">
        <button class="primary experiment-button" data-experiment="${escapeAttr(experiment.id)}">${escapeHtml(t("button.run", "Run"))}</button>
        ${output?.primary_report ? actionButton("preview-report", t("button.open_report", "Open report"), { path: output.primary_report.path, target: "toponymResearchPreview" }) : ""}
        ${summaryJson ? actionButton("preview-report", t("button.open_e2e_summary", "Open E2E summary"), { path: summaryJson.path, target: "toponymResearchPreview" }) : ""}
        ${stepsCsv ? actionButton("preview-table", t("button.open_e2e_steps", "Open E2E steps"), { path: stepsCsv.path, target: "tablePreview" }) : ""}
        ${codingSample ? actionButton("preview-table", t("button.open_e2e_coding_sample", "Open coding sample"), { path: codingSample.path, target: "tablePreview" }) : ""}
        ${run?.id ? actionButton("focus-run-reports", t("button.current_run", "Current run"), { target: run.id, disabled: !runIsCompleted }) : ""}
        ${run?.id ? actionButton("focus-run-evidence", `${t("button.current_run", "Current run")} / ${t("section.evidence_browser", "Evidence Browser")}`, { target: run.id, disabled: !runIsCompleted }) : ""}
        ${run?.id ? actionButton("prepare-coding-from-run", t("button.open_manual_coding", "Open manual coding step"), { target: run.id, disabled: !runIsCompleted }) : ""}
        ${actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: experiment.id })}
        ${actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: experiment.id })}
      </div>
    </section>
  `;
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
  const output = outputByExperimentId(experiment.id);
  return parameters.map((param) => {
    const draftValue = getExperimentParamDraft(experiment.id, param.name);
    const fallbackValue = param.name === "hypothesis"
      ? (output?.hypothesis || param.default || "")
      : (param.default ?? "");
    const value = draftValue !== undefined ? draftValue : fallbackValue;
    const selectedValue = String(value ?? "");
    return `
    <label class="${param.name === "hypothesis" ? "wide-param" : ""}">
      <span>${escapeHtml(t(`param.${param.name}`, param.name))}</span>
      ${param.name === "hypothesis" ? `<textarea
        rows="2"
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="hypothesis"
        placeholder="${escapeAttr(t("placeholder.hypothesis", "Research hypothesis or question"))}"
      >${escapeHtml(selectedValue)}</textarea>` : param.choices ? `<select
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="${escapeAttr(param.name)}"
      >${param.choices.map((choice) => `<option value="${escapeAttr(choice)}" ${String(choice) === selectedValue ? "selected" : ""}>${escapeHtml(t(`param.${param.name}.${choice}`, choice))}</option>`).join("")}</select>` : `<input
        type="${param.type === "int" ? "number" : "text"}"
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="${escapeAttr(param.name)}"
        value="${escapeAttr(selectedValue)}"
        ${param.min !== undefined ? `min="${escapeAttr(param.min)}"` : ""}
        ${param.max !== undefined ? `max="${escapeAttr(param.max)}"` : ""}
      />`}
    </label>
  `;
  }).join("");
}

function collectExperimentParams(experimentId) {
  const params = {};
  document.querySelectorAll(`[data-param-experiment="${CSS.escape(experimentId)}"]`).forEach((input) => {
    params[input.dataset.paramName] = input.type === "number" ? Number(input.value) : input.value;
  });
  return params;
}

function defaultParamsForExperiment(experimentId) {
  const experiment = (state.summary?.experiments || []).find((item) => item.id === experimentId);
  if (!experiment) return { hypothesis: "" };
  const defaults = { hypothesis: "" };
  for (const param of experiment.parameters || []) {
    if (!param?.name) continue;
    defaults[param.name] = param.default ?? "";
  }
  return defaults;
}

function applyObjectParamsToInputs(experimentId, params) {
  let applied = 0;
  document.querySelectorAll(`[data-param-experiment="${CSS.escape(experimentId)}"]`).forEach((input) => {
    const name = input.dataset.paramName || "";
    if (!name || !(name in params)) return;
    const value = params[name];
    if (input.type === "number") {
      const numeric = Number(value);
      input.value = Number.isFinite(numeric) ? String(numeric) : "";
    } else {
      input.value = value === null || value === undefined ? "" : String(value);
    }
    const stored = input.type === "number" ? Number(input.value) : input.value;
    setExperimentParamDraft(experimentId, name, stored);
    applied += 1;
  });
  return applied;
}

function applyParamsToExperimentInputs(experimentId, rawParams) {
  if (!experimentId || !rawParams) return;
  let params = {};
  try {
    const parsed = JSON.parse(rawParams);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) params = parsed;
  } catch (_) {
    return;
  }
  const applied = applyObjectParamsToInputs(experimentId, params);
  if (applied > 0) {
    showToast(`${t("message.reused_last_params", "Loaded params from last run")}: ${experimentTitle(experimentId)}`, "success");
  }
}

function resetExperimentParams(experimentId) {
  if (!experimentId) return;
  const defaults = defaultParamsForExperiment(experimentId);
  state.experimentParamDrafts[experimentId] = defaults;
  persistExperimentParamDrafts();
  const applied = applyObjectParamsToInputs(experimentId, defaults);
  if (applied > 0) {
    showToast(`${t("message.params_reset", "Params reset to defaults")}: ${experimentTitle(experimentId)}`, "info");
  }
}

async function copyParamsFromButton(button) {
  const experimentId = button.dataset.experiment || "";
  const rawParams = button.dataset.params || "";
  if (!rawParams) return;
  const payload = rawParams;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(payload);
    } else {
      throw new Error("Clipboard API unavailable");
    }
    showToast(`${t("message.params_copied", "Params copied")}: ${experimentTitle(experimentId)}`, "success");
  } catch (_) {
    showToast(`${t("message.params_copy_failed", "Failed to copy params")}: ${experimentTitle(experimentId)}`, "error", 4200);
  }
}

async function buildRunPacket(button) {
  const experimentId = button.dataset.experiment || "";
  const manifestPath = button.dataset.path || "";
  if (!manifestPath && !experimentId) return;
  return withButtonBusy(button, async () => {
    try {
      const response = await fetch("/api/run-packet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ experiment: experimentId, manifest_path: manifestPath }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        showToast(payload.error || t("message.failed_build_run_packet", "Failed to build run packet."), "error", 4200);
        return;
      }
      showToast(`${t("message.run_packet_created", "Run packet created")}: ${payload.path}`, "success");
      upsertRecentArtifact(payload.path, "reportPreview", "report");
      setActiveTab("reports");
      await previewReport(payload.path, "reportPreview");
    } catch (error) {
      showToast(`${t("message.failed_build_run_packet", "Failed to build run packet.")}: ${error}`, "error", 4200);
    }
  });
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
  const outputs = [...(state.summary.experiment_outputs || [])].map((item) => outputWithRunContext(item));
  outputs.sort((a, b) => {
    const runA = Number(a._run?.created_at || 0);
    const runB = Number(b._run?.created_at || 0);
    if (runA !== runB) return runB - runA;
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

function renderRunFilterSelect(selectId, selectedValue, outputs) {
  const select = document.getElementById(selectId);
  if (!select) return selectedValue;
  const runs = [];
  const seen = new Set();
  for (const item of outputs || []) {
    const run = item?._run;
    if (!run?.id || seen.has(run.id)) continue;
    seen.add(run.id);
    runs.push(run);
  }
  runs.sort((a, b) => Number(b.created_at || 0) - Number(a.created_at || 0));
  const options = [{ value: "all", label: t("label.all_runs", "All runs") }, ...runs.map((run) => ({
    value: run.id,
    label: `${run.label || run.preset || run.id} (${run.id})`,
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

function filterOutputsByRun(outputs, selectedRun) {
  if (selectedRun === "all") return outputs;
  return outputs.filter((item) => item?._run?.id === selectedRun);
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
  document.getElementById("reportPresetCurrentRun")?.classList.toggle("active", state.reportFilterPreset === "current_run");
  document.getElementById("evidencePresetWorkflow")?.classList.toggle("active", state.evidenceFilterPreset === "workflow");
  document.getElementById("evidencePresetAll")?.classList.toggle("active", state.evidenceFilterPreset === "all");
  document.getElementById("evidencePresetCurrentRun")?.classList.toggle("active", state.evidenceFilterPreset === "current_run");
}

function currentRunId() {
  const runById = Object.fromEntries((state.runs || []).map((run) => [run.id, run]));
  if (state.selectedRun && runById[state.selectedRun]) return state.selectedRun;
  const completed = (state.runs || []).find((run) => run.status === "completed");
  if (completed?.id) return completed.id;
  if ((state.runs || [])[0]?.id) return (state.runs || [])[0].id;
  return "";
}

function applyReportFilterPreset(mode) {
  state.reportExperimentFilter = "all";
  state.reportRunFilter = "all";
  state.reportIncludeInactive = false;
  state.reportExpandAll = false;
  state.reportArtifactFilter = "";
  state.reportWorkflowOnly = mode === "workflow";
  state.reportFilterPreset = mode;
  renderExperimentOutputs();
}

function applyEvidenceFilterPreset(mode) {
  state.evidenceExperimentFilter = "all";
  state.evidenceRunFilter = "all";
  state.evidenceIncludeInactive = false;
  state.evidenceExpandAll = false;
  state.evidenceArtifactFilter = "";
  state.evidenceWorkflowOnly = mode === "workflow";
  state.evidenceFilterPreset = mode;
  renderExperimentOutputs();
}

function applyReportCurrentRunPreset() {
  const runId = currentRunId();
  if (!runId) {
    showToast(t("text.no_runs", "No runs yet."), "info");
    return;
  }
  state.reportExperimentFilter = "all";
  state.reportRunFilter = runId;
  state.reportIncludeInactive = false;
  state.reportExpandAll = false;
  state.reportArtifactFilter = "";
  state.reportWorkflowOnly = false;
  state.reportFilterPreset = "current_run";
  renderExperimentOutputs();
}

function applyEvidenceCurrentRunPreset() {
  const runId = currentRunId();
  if (!runId) {
    showToast(t("text.no_runs", "No runs yet."), "info");
    return;
  }
  state.evidenceExperimentFilter = "all";
  state.evidenceRunFilter = runId;
  state.evidenceIncludeInactive = false;
  state.evidenceExpandAll = false;
  state.evidenceArtifactFilter = "";
  state.evidenceWorkflowOnly = false;
  state.evidenceFilterPreset = "current_run";
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

function groupOutputsByRun(outputs) {
  const groups = new Map();
  for (const item of outputs || []) {
    const run = item?._run || null;
    const key = run?.id || "__no_run__";
    if (!groups.has(key)) {
      groups.set(key, { run, items: [] });
    }
    groups.get(key).items.push(item);
  }
  return Array.from(groups.values()).sort((a, b) => {
    const timeA = Number(a.run?.created_at || 0);
    const timeB = Number(b.run?.created_at || 0);
    if (timeA !== timeB) return timeB - timeA;
    if (a.run && !b.run) return -1;
    if (!a.run && b.run) return 1;
    return 0;
  });
}

function renderRunGroupTitle(run, count) {
  if (!run?.id) return `${t("text.not_linked_to_run", "Not linked to an active run")} (${count})`;
  const base = `${t("label.run_id", "Run ID")}: ${run.id}`;
  return `${base} (${count})`;
}

function evidenceTextFromRow(row) {
  return String(
    row?.text
    || row?.excerpt
    || row?.summary
    || row?.query
    || "",
  ).trim();
}

function evidenceMetaFromRow(row) {
  return {
    source: String(row?.source || row?.source_path || row?.filename || "").trim(),
    toponym: String(row?.toponym || row?.parent_city || "").trim(),
    sentiment: String(row?.sentiment || "").trim(),
    driver: String(row?.migration_driver || row?.driver || "").trim(),
  };
}

async function fetchRunEvidenceDigest(runId, linkedOutputs, maxItems = 5) {
  const result = [];
  const seen = new Set();
  const evidenceFiles = [];
  for (const item of linkedOutputs || []) {
    for (const file of (item?.evidence || [])) {
      evidenceFiles.push({ file, experimentId: item?.id, experimentTitle: item?.title });
      if (evidenceFiles.length >= 8) break;
    }
    if (evidenceFiles.length >= 8) break;
  }
  for (const entry of evidenceFiles) {
    const path = entry.file?.path;
    if (!path) continue;
    try {
      const params = new URLSearchParams({ path, limit: "20" });
      const response = await fetch(`/api/evidence?${params.toString()}`);
      if (!response.ok) continue;
      const payload = await response.json();
      for (const row of payload.rows || []) {
        const text = evidenceTextFromRow(row);
        if (!text) continue;
        const key = `${path}|${row.row_index || ""}|${text.slice(0, 120)}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const meta = evidenceMetaFromRow(row);
        result.push({
          evidence_path: path,
          experiment_id: entry.experimentId || "",
          experiment_title: entry.experimentTitle || "",
          text,
          source: meta.source,
          toponym: meta.toponym,
          sentiment: meta.sentiment,
          driver: meta.driver,
        });
        if (result.length >= maxItems) return result;
      }
    } catch (_) {
      // continue with remaining files
    }
  }
  return result;
}

function renderRunEvidenceDigestItems(items) {
  if (!items.length) {
    return `<p class="muted">${escapeHtml(t("text.no_evidence_digest", "No evidence snippets available for this run yet."))}</p>`;
  }
  const topToponym = rankMostFrequent(items, (item) => item.toponym);
  const topDriver = rankMostFrequent(items, (item) => item.driver);
  const summaryBits = [];
  if (topToponym.value) {
    summaryBits.push(`${t("text.top_toponym", "top toponym")}: ${topToponym.value} (${topToponym.count})`);
  }
  if (topDriver.value) {
    summaryBits.push(`${t("text.top_driver", "top driver")}: ${topDriver.value} (${topDriver.count})`);
  }
  const summary = summaryBits.length
    ? `<p class="muted">${escapeHtml(t("text.evidence_summary", "Evidence summary"))}: ${escapeHtml(summaryBits.join(" | "))}</p>`
    : "";
  return `${summary}<div class="run-evidence-list">${items.map((item, index) => `
    <article class="run-evidence-item">
      <div class="run-evidence-head">
        <strong>${escapeHtml(`${t("text.snippet", "Snippet")} ${index + 1}`)}</strong>
        <span class="muted">${escapeHtml(item.source || item.experiment_id || "")}</span>
      </div>
      <p>${escapeHtml(item.text.slice(0, 420))}</p>
      <p class="muted">
        ${escapeHtml(t("label.toponym", "Toponym"))}: ${escapeHtml(item.toponym || "-")} |
        ${escapeHtml(t("label.sentiment", "Sentiment"))}: ${escapeHtml(item.sentiment || "-")} |
        ${escapeHtml(t("label.driver", "Driver"))}: ${escapeHtml(item.driver || "-")}
      </p>
      <div class="button-row">
        ${item.toponym ? actionButton("use-toponym-for-coding", t("button.use_toponym", "Use toponym"), { target: item.toponym }) : ""}
        ${actionButton("preview-evidence", t("button.browse", "Browse"), { path: item.evidence_path })}
      </div>
    </article>
  `).join("")}</div>`;
}

async function ensureRunEvidenceDigest(runId, linkedOutputs) {
  const container = document.getElementById("runEvidenceDigest");
  if (!container) return;
  container.dataset.runId = runId;
  const cached = state.runEvidenceDigestByRun[runId];
  if (Array.isArray(cached)) {
    container.innerHTML = renderRunEvidenceDigestItems(cached);
    return;
  }
  container.innerHTML = `<p class="muted">${escapeHtml(t("message.loading_evidence_digest", "Loading evidence snippets..."))}</p>`;
  const items = await fetchRunEvidenceDigest(runId, linkedOutputs, 5);
  state.runEvidenceDigestByRun[runId] = items;
  if (container.dataset.runId !== runId) return;
  container.innerHTML = renderRunEvidenceDigestItems(items);
}

function recommendedToponymForRun(runId) {
  const items = state.runEvidenceDigestByRun[runId] || [];
  return rankMostFrequent(items, (item) => item.toponym).value || "";
}

function rankMostFrequent(items, selector) {
  const counts = {};
  for (const item of items || []) {
    const value = String(selector(item) || "").trim();
    if (!value) continue;
    counts[value] = (counts[value] || 0) + 1;
  }
  const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return { value: ranked[0]?.[0] || "", count: ranked[0]?.[1] || 0 };
}

function hasTableArtifact(linkedOutputs, names) {
  const expected = new Set((names || []).map((item) => String(item || "").toLowerCase()));
  if (!expected.size) return false;
  for (const output of linkedOutputs || []) {
    for (const table of output?.tables || []) {
      const name = String(table?.name || "").toLowerCase();
      if (expected.has(name)) return true;
    }
  }
  return false;
}

function findPrimaryReportPath(linkedOutputs) {
  for (const output of linkedOutputs || []) {
    const value = String(output?.primary_report?.path || "").trim();
    if (value) return value;
  }
  return "";
}

function findTableArtifactPath(linkedOutputs, names) {
  const expected = new Set((names || []).map((item) => String(item || "").toLowerCase()));
  if (!expected.size) return "";
  for (const output of linkedOutputs || []) {
    for (const table of output?.tables || []) {
      const name = String(table?.name || "").toLowerCase();
      if (expected.has(name)) return String(table?.path || "");
    }
  }
  return "";
}

function researchReadinessItems(linkedOutputs) {
  const reportPath = findPrimaryReportPath(linkedOutputs);
  const toponymFrequencyPath = findTableArtifactPath(linkedOutputs, ["toponym_frequency.csv"]);
  const narrativeMatrixPath = findTableArtifactPath(linkedOutputs, ["migration_narrative_matrix.csv"]);
  const codingSamplePath = findTableArtifactPath(linkedOutputs, ["coding_sample_by_toponym.csv", "coding_sample.csv"]);
  return [
    {
      key: "checklist.primary_report",
      ok: Boolean(reportPath),
      action: reportPath
        ? actionButton("preview-report", t("button.open", "Open"), { path: reportPath, target: "reportPreview" })
        : actionButton("run-experiment", t("button.run", "Run"), { experiment: "toponym_research_workflow" }),
    },
    {
      key: "checklist.toponym_frequency",
      ok: Boolean(toponymFrequencyPath),
      action: toponymFrequencyPath
        ? actionButton("preview-table", t("button.open", "Open"), { path: toponymFrequencyPath, target: "tablePreview" })
        : actionButton("run-experiment", t("button.run", "Run"), { experiment: "toponym_research_workflow" }),
    },
    {
      key: "checklist.narrative_matrix",
      ok: Boolean(narrativeMatrixPath),
      action: narrativeMatrixPath
        ? actionButton("preview-table", t("button.open", "Open"), { path: narrativeMatrixPath, target: "tablePreview" })
        : actionButton("run-experiment", t("button.run", "Run"), { experiment: "migration_narratives" }),
    },
    {
      key: "checklist.coding_sample",
      ok: Boolean(codingSamplePath),
      action: codingSamplePath
        ? actionButton("preview-table", t("button.open", "Open"), { path: codingSamplePath, target: "tablePreview" })
        : actionButton("run-experiment", t("button.run", "Run"), { experiment: "sampling_coding" }),
    },
  ];
}

function renderResearchReadinessChecklist(linkedOutputs) {
  const items = researchReadinessItems(linkedOutputs);
  return `<ul class="readiness-checklist">${items.map((item) => `
    <li>
      <div class="readiness-label">
        <span class="status ${item.ok ? "completed" : "missing"}">${escapeHtml(item.ok ? t("text.ready", "ready") : t("text.missing", "missing"))}</span>
        <span>${escapeHtml(t(item.key, item.key))}</span>
      </div>
      <div class="button-row">${item.action || ""}</div>
    </li>
  `).join("")}</ul>`;
}

function researchReadinessSummary(linkedOutputs) {
  const items = researchReadinessItems(linkedOutputs);
  const total = items.length;
  const ready = items.filter((item) => item.ok).length;
  return { items, total, ready, ratio: total ? ready / total : 0 };
}

function renderNextResearchAction(linkedOutputs, preferredRun, runStatus, runIsCompleted) {
  if (runStatus === "running") {
    return `
      <section class="next-action-card">
        <h4>${escapeHtml(t("section.next_research_action", "Next research action"))}</h4>
        <p class="muted">${escapeHtml(t("text.next_action_running", "Run is still in progress. Wait for completion and inspect the run log if needed."))}</p>
        <div class="button-row">
          ${actionButton("open-run-log", t("button.open_run_log", "Open run log"), { target: preferredRun.id, classes: "primary" })}
        </div>
      </section>
    `;
  }
  if (runStatus === "failed") {
    return `
      <section class="next-action-card">
        <h4>${escapeHtml(t("section.next_research_action", "Next research action"))}</h4>
        <p class="muted">${escapeHtml(t("text.next_action_failed", "Run failed. Inspect the run log and relaunch the failed step."))}</p>
        <div class="button-row">
          ${actionButton("open-run-log", t("button.open_run_log", "Open run log"), { target: preferredRun.id, classes: "primary" })}
        </div>
      </section>
    `;
  }
  const items = researchReadinessItems(linkedOutputs);
  const missing = items.find((item) => !item.ok) || null;
  if (missing) {
    return `
      <section class="next-action-card">
        <h4>${escapeHtml(t("section.next_research_action", "Next research action"))}</h4>
        <p class="muted">${escapeHtml(t("text.next_action_missing", "The next required artifact is missing."))}: ${escapeHtml(t(missing.key, missing.key))}</p>
        <div class="button-row">${missing.action || ""}</div>
      </section>
    `;
  }
  return `
    <section class="next-action-card">
      <h4>${escapeHtml(t("section.next_research_action", "Next research action"))}</h4>
      <p class="muted">${escapeHtml(t("text.next_action_ready", "Checklist is complete. Continue with synthesis and manual coding review."))}</p>
      <div class="button-row">
        ${actionButton("prepare-coding-from-run", t("button.open_manual_coding", "Open manual coding step"), { target: preferredRun.id, classes: "primary", disabled: !runIsCompleted })}
        ${actionButton("open-result-pack", t("button.open_result_pack", "Open result pack"), { target: preferredRun.id, disabled: !runIsCompleted })}
      </div>
    </section>
  `;
}

async function fetchComparisonCandidates(experimentId, runId) {
  const params = new URLSearchParams({
    experiment_id: experimentId || "",
    run_id: runId || "",
    limit: "6",
  });
  const response = await fetch(`/api/run-comparison-candidates?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed", current: null, baselines: [] };
  }
  return payload;
}

async function fetchRunComparison(pathA, pathB) {
  const params = new URLSearchParams({ a: pathA || "", b: pathB || "" });
  const response = await fetch(`/api/run-compare?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed" };
  }
  return payload;
}

async function fetchRunSeries(experimentId, runId, limit = 5) {
  const params = new URLSearchParams({
    experiment_id: experimentId || "",
    run_id: runId || "",
    limit: String(limit || 5),
  });
  const response = await fetch(`/api/run-series?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed", rows: [] };
  }
  return payload;
}

async function exportRunSeries(experimentId, runId, limit = 5, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const response = await fetch("/api/run-series", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        experiment_id: experimentId || "",
        run_id: runId || "",
        limit: Number(limit) || 5,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.error) {
      showToast(payload?.error || t("message.failed_build_series", "Failed to build run series."), "error", 4200);
      return;
    }
    const markdownPath = payload?.paths?.markdown || "";
    if (markdownPath) {
      upsertRecentArtifact(markdownPath, "reportPreview", "report", experimentId || "");
      setActiveTab("reports");
      await previewReport(markdownPath, "reportPreview");
    }
    showToast(`${t("message.series_created", "Run series created")}: ${markdownPath || "-"}`, "success");
  });
}

async function fetchHypothesisSessions(experimentId, runId, sessionLimit = 6, runLimit = 5) {
  const params = new URLSearchParams({
    experiment_id: experimentId || "",
    run_id: runId || "",
    session_limit: String(sessionLimit || 6),
    run_limit: String(runLimit || 5),
  });
  const response = await fetch(`/api/hypothesis-sessions?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed", sessions: [] };
  }
  return payload;
}

async function exportHypothesisSession(experimentId, runId, hypothesisKey = "", triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const response = await fetch("/api/hypothesis-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        experiment_id: experimentId || "",
        run_id: runId || "",
        hypothesis_key: hypothesisKey || "",
        session_limit: 6,
        run_limit: Number(state.runSeriesLimit) || 5,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.error) {
      showToast(payload?.error || t("message.failed_build_hypothesis_session", "Failed to build hypothesis packet."), "error", 4200);
      return;
    }
    const markdownPath = payload?.paths?.markdown || "";
    if (markdownPath) {
      upsertRecentArtifact(markdownPath, "reportPreview", "report", experimentId || "");
      setActiveTab("reports");
      await previewReport(markdownPath, "reportPreview");
    }
    showToast(`${t("message.hypothesis_session_created", "Hypothesis packet created")}: ${markdownPath || "-"}`, "success");
  });
}

async function fetchHypothesisMatrix(experimentId, runId, sessionLimit = 8, runLimit = 5) {
  const params = new URLSearchParams({
    experiment_id: experimentId || "",
    run_id: runId || "",
    session_limit: String(sessionLimit || 8),
    run_limit: String(runLimit || 5),
  });
  const response = await fetch(`/api/hypothesis-matrix?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed", rows: [] };
  }
  return payload;
}

async function exportHypothesisMatrix(experimentId, runId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const response = await fetch("/api/hypothesis-matrix", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        experiment_id: experimentId || "",
        run_id: runId || "",
        session_limit: 8,
        run_limit: Number(state.runSeriesLimit) || 5,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.error) {
      showToast(payload?.error || t("message.failed_build_hypothesis_matrix", "Failed to build hypothesis matrix."), "error", 4200);
      return;
    }
    const markdownPath = payload?.paths?.markdown || "";
    if (markdownPath) {
      upsertRecentArtifact(markdownPath, "reportPreview", "report", experimentId || "");
      setActiveTab("reports");
      await previewReport(markdownPath, "reportPreview");
    }
    showToast(`${t("message.hypothesis_matrix_created", "Hypothesis matrix created")}: ${markdownPath || "-"}`, "success");
  });
}

function hypothesisCompareContextKey(runId, experimentId) {
  return `${runId || ""}::${experimentId || ""}`;
}

function hypothesisCompareControlIds(runId, experimentId) {
  const safe = `${runId || "run"}_${experimentId || "experiment"}`.replace(/[^a-zA-Z0-9_-]+/g, "_");
  return {
    selectA: `hypothesisCompareA_${safe}`,
    selectB: `hypothesisCompareB_${safe}`,
  };
}

function selectedHypothesisKeys(runId, experimentId) {
  const ids = hypothesisCompareControlIds(runId, experimentId);
  const selectA = document.getElementById(ids.selectA);
  const selectB = document.getElementById(ids.selectB);
  return {
    keyA: String(selectA?.value || "").trim(),
    keyB: String(selectB?.value || "").trim(),
  };
}

async function fetchHypothesisCompare(experimentId, runId, keyA, keyB, runLimit = 5) {
  const params = new URLSearchParams({
    experiment_id: experimentId || "",
    run_id: runId || "",
    a: keyA || "",
    b: keyB || "",
    run_limit: String(runLimit || 5),
  });
  const response = await fetch(`/api/hypothesis-compare?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok || payload?.error) {
    return { error: payload?.error || "failed" };
  }
  return payload;
}

async function exportHypothesisCompare(experimentId, runId, keyA, keyB, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const response = await fetch("/api/hypothesis-compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        experiment_id: experimentId || "",
        run_id: runId || "",
        hypothesis_key_a: keyA || "",
        hypothesis_key_b: keyB || "",
        run_limit: Number(state.runSeriesLimit) || 5,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload?.error) {
      showToast(payload?.error || t("message.failed_build_hypothesis_compare", "Failed to build hypothesis comparison."), "error", 4200);
      return;
    }
    const markdownPath = payload?.paths?.markdown || "";
    if (markdownPath) {
      upsertRecentArtifact(markdownPath, "reportPreview", "report", experimentId || "");
      setActiveTab("reports");
      await previewReport(markdownPath, "reportPreview");
    }
    showToast(`${t("message.hypothesis_compare_created", "Hypothesis comparison created")}: ${markdownPath || "-"}`, "success");
  });
}

async function runHypothesisCompare(runId, experimentId, triggerButton = null) {
  const key = hypothesisCompareContextKey(runId, experimentId);
  const selected = selectedHypothesisKeys(runId, experimentId);
  if (!selected.keyA || !selected.keyB) {
    showToast(t("message.hypothesis_compare_missing_selection", "Select two hypothesis sessions to compare."), "error", 3200);
    return;
  }
  if (selected.keyA === selected.keyB) {
    showToast(t("message.hypothesis_compare_same_selection", "Choose two different hypothesis sessions."), "error", 3200);
    return;
  }
  return withButtonBusy(triggerButton, async () => {
    state.hypothesisCompareByContext[key] = {
      status: "loading",
      experimentId,
      runId,
      keyA: selected.keyA,
      keyB: selected.keyB,
      payload: null,
      error: "",
    };
    renderHypothesisMatrixBoard(runId);
    const payload = await fetchHypothesisCompare(experimentId, runId, selected.keyA, selected.keyB, state.runSeriesLimit);
    if (payload?.error) {
      state.hypothesisCompareByContext[key] = {
        status: "error",
        experimentId,
        runId,
        keyA: selected.keyA,
        keyB: selected.keyB,
        payload: null,
        error: String(payload.error),
      };
      renderHypothesisMatrixBoard(runId);
      return;
    }
    state.hypothesisCompareByContext[key] = {
      status: "ready",
      experimentId,
      runId,
      keyA: selected.keyA,
      keyB: selected.keyB,
      payload,
      error: "",
    };
    renderHypothesisMatrixBoard(runId);
  });
}

async function exportHypothesisCompareFromControls(runId, experimentId, triggerButton = null) {
  const selected = selectedHypothesisKeys(runId, experimentId);
  if (!selected.keyA || !selected.keyB || selected.keyA === selected.keyB) {
    showToast(t("message.hypothesis_compare_missing_selection", "Select two hypothesis sessions to compare."), "error", 3200);
    return;
  }
  return exportHypothesisCompare(experimentId, runId, selected.keyA, selected.keyB, triggerButton);
}

async function focusHypothesisRun(runId, experimentId = "", triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    if (runId && (state.runs || []).some((item) => item?.id === runId)) {
      await openRunLog(runId);
      return;
    }
    if (experimentId) {
      state.reportExperimentFilter = experimentId;
      state.evidenceExperimentFilter = experimentId;
    }
    if (runId) {
      state.reportRunFilter = runId;
      state.evidenceRunFilter = runId;
      state.reportFilterPreset = "current_run";
      state.evidenceFilterPreset = "current_run";
    }
    renderExperimentOutputs();
    setActiveTab("reports");
    const output = sortedExperimentOutputs().find((item) => item.id === experimentId && item?._run?.id === runId);
    if (output?.primary_report?.path) {
      await previewReport(output.primary_report.path, "reportPreview");
    }
  });
}

function tableMetricDelta(comparison, tableName) {
  const item = (comparison?.table_comparisons || []).find((row) => row?.table === tableName);
  if (!item) return { status: "missing", delta: null, table: null, currentPath: "", previousPath: "" };
  const current = Number(item?.a?.top_value);
  const previous = Number(item?.b?.top_value);
  if (Number.isFinite(current) && Number.isFinite(previous)) {
    const delta = current - previous;
    const status = delta > 0 ? "up" : (delta < 0 ? "down" : "same");
    return { status, delta, table: item.table, currentPath: item?.a?.path || "", previousPath: item?.b?.path || "" };
  }
  return { status: "same", delta: null, table: item.table, currentPath: item?.a?.path || "", previousPath: item?.b?.path || "" };
}

function metricDeltaBadge(metric) {
  const text = metric.delta === null
    ? t(`delta.${metric.status}`, metric.status)
    : `${metric.delta > 0 ? "+" : ""}${metric.delta}`;
  return `<span class="delta-chip ${escapeAttr(metric.status)}">${escapeHtml(text)}</span>`;
}

function renderRunComparisonBoard(runId) {
  const target = document.getElementById("runComparisonBoard");
  if (!target) return;
  const board = state.runComparisonBoardByRun[runId];
  if (!board || board.status === "loading") {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.comparison_loading", "Loading comparison board..."))}</p>`;
    return;
  }
  if (board.status === "error") {
    target.innerHTML = `<p class="status failed">${escapeHtml(board.error || t("text.comparison_failed", "Failed to build comparison board."))}</p>`;
    return;
  }
  const rows = board.rows || [];
  if (!rows.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.comparison_no_baseline", "No previous run baseline is available yet."))}</p>`;
    return;
  }
  const metricDefs = [
    { table: "toponym_frequency.csv", label: t("metric.toponym_frequency", "Toponym frequency") },
    { table: "migration_driver_distribution.csv", label: t("metric.migration_driver_distribution", "Migration drivers") },
    { table: "sentiment_per_toponym.csv", label: t("metric.sentiment_per_toponym", "Sentiment per toponym") },
    { table: "topics_per_toponym.csv", label: t("metric.topics_per_toponym", "Topics per toponym") },
  ];
  target.innerHTML = rows.map((row) => {
    const comparison = row.comparison || {};
    const metrics = metricDefs.map((metric) => ({
      ...metric,
      ...tableMetricDelta(comparison, metric.table),
    }));
    const baselineOptions = Array.isArray(row.baselines) ? row.baselines : [];
    const selectedBaseline = baselineOptions.find((item) => item.path === row.selected_baseline_path) || baselineOptions[0] || null;
    const changedTables = (comparison.table_comparisons || []).filter((item) => item?.changed).length;
    const diffCount = (comparison.differences || []).length;
    const previousRunId = selectedBaseline?.run_id || row.previous_run_id || "-";
    const baselineControl = baselineOptions.length
      ? `
        <label class="comparison-baseline">
          <span>${escapeHtml(t("text.baseline_run", "Baseline run"))}</span>
          <select data-action="set-comparison-baseline" data-run-id="${escapeAttr(runId)}" data-experiment="${escapeAttr(row.experiment_id || "")}">
            ${baselineOptions.map((item) => `<option value="${escapeAttr(item.path || "")}" ${item.path === row.selected_baseline_path ? "selected" : ""}>${escapeHtml(item.label || item.run_id || item.path || "-")}</option>`).join("")}
          </select>
        </label>
      `
      : `<p class="muted">${escapeHtml(t("text.comparison_no_baseline", "No previous run baseline is available yet."))}</p>`;
    const statusLine = row.loading
      ? `<p class="muted">${escapeHtml(t("text.comparison_updating", "Updating comparison..."))}</p>`
      : (row.error ? `<p class="status failed">${escapeHtml(row.error)}</p>` : "");
    return `
      <article class="comparison-item">
        <div>
          <strong>${escapeHtml(t(`experiment.${row.experiment_id}.title`, row.experiment_id || "experiment"))}</strong>
          <p class="muted">${escapeHtml(t("text.compare_current", "Current"))}: ${escapeHtml(row.current_run_id || "-")} / ${escapeHtml(t("text.compare_previous", "Previous"))}: ${escapeHtml(previousRunId)}</p>
          <p class="muted">${escapeHtml(t("text.changed_tables", "Changed tables"))}: ${changedTables}; ${escapeHtml(t("text.difference_count", "Differences"))}: ${diffCount}</p>
          ${baselineControl}
          ${statusLine}
        </div>
        <div class="comparison-metrics">
          ${metrics.map((metric) => `
            <div class="comparison-metric">
              <span>${escapeHtml(metric.label)}</span>
              ${metricDeltaBadge(metric)}
              ${metric.currentPath ? actionButton("preview-table", t("button.open", "Open"), { path: metric.currentPath, target: "tablePreview" }) : ""}
            </div>
          `).join("")}
        </div>
      </article>
    `;
  }).join("");
}

async function ensureRunComparisonBoard(runId, linkedOutputs) {
  if (!runId) return;
  const current = state.runComparisonBoardByRun[runId];
  if (current?.status === "ready" || current?.status === "loading") {
    renderRunComparisonBoard(runId);
    return;
  }
  state.runComparisonBoardByRun[runId] = { status: "loading", rows: [] };
  renderRunComparisonBoard(runId);
  const rows = [];
  try {
    for (const output of linkedOutputs || []) {
      const candidates = await fetchComparisonCandidates(output.id, runId);
      if (candidates?.error || !candidates?.current) continue;
      const baseline = (candidates.baselines || [])[0] || null;
      let comparison = {};
      let rowError = "";
      if (baseline?.path && candidates.current?.path) {
        const payload = await fetchRunComparison(candidates.current.path, baseline.path);
        if (payload?.error) {
          rowError = String(payload.error);
        } else {
          comparison = payload;
        }
      }
      rows.push({
        experiment_id: output.id,
        current_run_id: candidates.current.run_id || "",
        previous_run_id: baseline?.run_id || "",
        current_manifest_path: candidates.current.path || "",
        selected_baseline_path: baseline?.path || "",
        baselines: candidates.baselines || [],
        comparison,
        loading: false,
        error: rowError,
      });
    }
    state.runComparisonBoardByRun[runId] = { status: "ready", rows };
  } catch (error) {
    state.runComparisonBoardByRun[runId] = { status: "error", rows: [], error: String(error) };
  }
  renderRunComparisonBoard(runId);
}

async function setComparisonBaseline(select) {
  const runId = select?.dataset?.runId || "";
  const experimentId = select?.dataset?.experiment || "";
  const baselinePath = select?.value || "";
  if (!runId || !experimentId || !baselinePath) return;
  const board = state.runComparisonBoardByRun[runId];
  if (!board || board.status !== "ready") return;
  const row = (board.rows || []).find((item) => item?.experiment_id === experimentId);
  if (!row || !row.current_manifest_path || row.selected_baseline_path === baselinePath) return;
  row.selected_baseline_path = baselinePath;
  row.loading = true;
  row.error = "";
  renderRunComparisonBoard(runId);
  const payload = await fetchRunComparison(row.current_manifest_path, baselinePath);
  if (payload?.error) {
    row.error = String(payload.error);
    row.loading = false;
    renderRunComparisonBoard(runId);
    return;
  }
  const selected = (row.baselines || []).find((item) => item.path === baselinePath) || null;
  row.previous_run_id = selected?.run_id || row.previous_run_id || "";
  row.comparison = payload;
  row.loading = false;
  row.error = "";
  renderRunComparisonBoard(runId);
}

function formatSeriesMetric(metric) {
  if (!metric || metric.error) return "n/a";
  const label = String(metric.top_label || "").trim();
  const value = metric.top_value;
  if (!label && (value === null || value === undefined || value === "")) return "n/a";
  if (value === null || value === undefined || value === "") return label || "n/a";
  return `${label || "-"} (${value})`;
}

function renderRunSeriesBoard(runId) {
  const target = document.getElementById("runSeriesBoard");
  if (!target) return;
  const board = state.runSeriesBoardByRun[runId];
  if (!board || board.status === "loading") {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.series_loading", "Loading run series..."))}</p>`;
    return;
  }
  if (board.status === "error") {
    target.innerHTML = `<p class="status failed">${escapeHtml(board.error || t("text.series_failed", "Failed to load run series."))}</p>`;
    return;
  }
  const rows = board.rows || [];
  if (!rows.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_series_data", "No run series data is available yet."))}</p>`;
    return;
  }
  target.innerHTML = rows.map((row) => {
    const series = row.series || {};
    const items = Array.isArray(series.rows) ? series.rows : [];
    const warning = String(series.warning || "").trim();
    const error = String(row.error || "").trim();
    const tableRows = items.map((item) => {
      const metrics = item.metrics || {};
      return `
        <tr>
          <td><code>${escapeHtml(item.run_id || "-")}</code></td>
          <td>${escapeHtml(item.hypothesis || "-")}</td>
          <td>${escapeHtml((item.changed_params || []).join(", ") || "-")}</td>
          <td>${escapeHtml(formatSeriesMetric(metrics.toponym_frequency || {}))}</td>
          <td>${escapeHtml(formatSeriesMetric(metrics.migration_drivers || {}))}</td>
          <td>${escapeHtml(formatSeriesMetric(metrics.sentiment_per_toponym || {}))}</td>
          <td>${escapeHtml(formatSeriesMetric(metrics.topics_per_toponym || {}))}</td>
        </tr>
      `;
    }).join("");
    return `
      <article class="series-item">
        <div class="series-head">
          <div>
            <strong>${escapeHtml(t(`experiment.${row.experiment_id}.title`, row.experiment_id || "experiment"))}</strong>
            <p class="muted">${escapeHtml(t("text.series_runs", "Selected runs"))}: ${escapeHtml(String(series.selected_count || 0))} / ${escapeHtml(t("text.series_available", "Available runs"))}: ${escapeHtml(String(series.available_runs || 0))}</p>
          </div>
          <div class="button-row">
            ${actionButton("export-run-series", t("button.export_run_series", "Export run series"), { experiment: row.experiment_id, target: runId, classes: "primary", disabled: !items.length })}
          </div>
        </div>
        ${error ? `<p class="status failed">${escapeHtml(error)}</p>` : ""}
        ${warning ? `<p class="muted">${escapeHtml(warning)}</p>` : ""}
        <div class="series-table-wrap">
          <table class="series-table">
            <thead>
              <tr>
                <th>${escapeHtml(t("label.run_id", "Run ID"))}</th>
                <th>${escapeHtml(t("text.hypothesis", "Hypothesis"))}</th>
                <th>${escapeHtml(t("text.changed_params", "Changed params"))}</th>
                <th>${escapeHtml(t("metric.toponym_frequency", "Toponym frequency"))}</th>
                <th>${escapeHtml(t("metric.migration_driver_distribution", "Migration drivers"))}</th>
                <th>${escapeHtml(t("metric.sentiment_per_toponym", "Sentiment per toponym"))}</th>
                <th>${escapeHtml(t("metric.topics_per_toponym", "Topics per toponym"))}</th>
              </tr>
            </thead>
            <tbody>${tableRows || `<tr><td colspan="7">${escapeHtml(t("text.no_series_data", "No run series data is available yet."))}</td></tr>`}</tbody>
          </table>
        </div>
      </article>
    `;
  }).join("");
}

async function ensureRunSeriesBoard(runId, linkedOutputs, limit = 5) {
  if (!runId) return;
  const current = state.runSeriesBoardByRun[runId];
  if (current?.status === "ready" && current?.limit === limit) {
    renderRunSeriesBoard(runId);
    return;
  }
  if (current?.status === "loading" && current?.limit === limit) {
    renderRunSeriesBoard(runId);
    return;
  }
  state.runSeriesBoardByRun[runId] = { status: "loading", rows: [], limit };
  renderRunSeriesBoard(runId);
  const rows = [];
  try {
    for (const output of linkedOutputs || []) {
      const payload = await fetchRunSeries(output.id, runId, limit);
      if (payload?.error) {
        rows.push({ experiment_id: output.id, series: { rows: [] }, error: String(payload.error) });
        continue;
      }
      rows.push({
        experiment_id: output.id,
        series: payload,
        error: "",
      });
    }
    state.runSeriesBoardByRun[runId] = { status: "ready", rows, limit };
  } catch (error) {
    state.runSeriesBoardByRun[runId] = { status: "error", rows: [], limit, error: String(error) };
  }
  renderRunSeriesBoard(runId);
}

function renderHypothesisSessionsBoard(runId) {
  const target = document.getElementById("hypothesisSessionsBoard");
  if (!target) return;
  const board = state.hypothesisSessionsByRun[runId];
  if (!board || board.status === "loading") {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.hypothesis_sessions_loading", "Loading hypothesis sessions..."))}</p>`;
    return;
  }
  if (board.status === "error") {
    target.innerHTML = `<p class="status failed">${escapeHtml(board.error || t("text.hypothesis_sessions_failed", "Failed to load hypothesis sessions."))}</p>`;
    return;
  }
  const rows = board.rows || [];
  if (!rows.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.hypothesis_sessions_empty", "No hypothesis sessions are available yet."))}</p>`;
    return;
  }
  target.innerHTML = rows.map((row) => {
    const payload = row.payload || {};
    const sessions = Array.isArray(payload.sessions) ? payload.sessions : [];
    const warning = String(payload.warning || "").trim();
    const cards = sessions.map((session) => {
      const hypothesis = String(session.hypothesis || "").trim() || t("text.no_hypothesis", "No hypothesis recorded.");
      const changedParams = (session.changed_params || []).join(", ") || "-";
      const latestRunId = session.latest_run_id || "";
      const metrics = session.latest_metrics || {};
      return `
        <article class="hypothesis-card ${session.current ? "active" : ""}">
          <div>
            <strong>${escapeHtml(hypothesis)}</strong>
            <p class="muted">${escapeHtml(t("text.series_runs", "Selected runs"))}: ${escapeHtml(String(session.run_count || 0))}; ${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(latestRunId || "-")}</p>
            <p class="muted">${escapeHtml(t("text.changed_params", "Changed params"))}: ${escapeHtml(changedParams)}</p>
            <p class="muted">${escapeHtml(t("metric.toponym_frequency", "Toponym frequency"))}: ${escapeHtml(formatSeriesMetric(metrics.toponym_frequency || {}))}</p>
          </div>
          <div class="button-row">
            ${actionButton("focus-hypothesis-run", t("button.open_hypothesis_run", "Open run context"), { target: latestRunId, experiment: row.experiment_id, classes: "primary", disabled: !latestRunId })}
            ${session.latest_report_path ? actionButton("preview-report", t("button.open_report", "Open report"), { path: session.latest_report_path, target: "reportPreview", classes: "primary" }) : ""}
            ${session.evidence_paths?.[0] ? actionButton("preview-evidence", t("button.open_evidence_view", "Open evidence view"), { path: session.evidence_paths[0], target: "evidencePreview" }) : ""}
            ${actionButton("export-hypothesis-session", t("button.export_hypothesis_session", "Export hypothesis packet"), { experiment: row.experiment_id, target: latestRunId, sessionKey: session.hypothesis_key })}
          </div>
        </article>
      `;
    }).join("");
    return `
      <section class="hypothesis-group">
        <h4>${escapeHtml(t(`experiment.${row.experiment_id}.title`, row.experiment_id || "experiment"))}</h4>
        ${warning ? `<p class="muted">${escapeHtml(warning)}</p>` : ""}
        ${cards || `<p class="muted">${escapeHtml(t("text.hypothesis_sessions_empty", "No hypothesis sessions are available yet."))}</p>`}
      </section>
    `;
  }).join("");
}

async function ensureHypothesisSessionsBoard(runId, linkedOutputs, runLimit = 5) {
  if (!runId) return;
  const current = state.hypothesisSessionsByRun[runId];
  if (current?.status === "ready" && current?.runLimit === runLimit) {
    renderHypothesisSessionsBoard(runId);
    return;
  }
  if (current?.status === "loading" && current?.runLimit === runLimit) {
    renderHypothesisSessionsBoard(runId);
    return;
  }
  state.hypothesisSessionsByRun[runId] = { status: "loading", rows: [], runLimit };
  renderHypothesisSessionsBoard(runId);
  const rows = [];
  try {
    for (const output of linkedOutputs || []) {
      const payload = await fetchHypothesisSessions(output.id, runId, 6, runLimit);
      if (payload?.error) {
        rows.push({ experiment_id: output.id, payload: { sessions: [] }, error: String(payload.error) });
        continue;
      }
      rows.push({ experiment_id: output.id, payload, error: "" });
    }
    state.hypothesisSessionsByRun[runId] = { status: "ready", rows, runLimit };
  } catch (error) {
    state.hypothesisSessionsByRun[runId] = { status: "error", rows: [], runLimit, error: String(error) };
  }
  renderHypothesisSessionsBoard(runId);
}

function renderHypothesisMatrixBoard(runId) {
  const target = document.getElementById("hypothesisMatrixBoard");
  if (!target) return;
  const board = state.hypothesisMatrixByRun[runId];
  if (!board || board.status === "loading") {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.hypothesis_matrix_loading", "Loading hypothesis matrix..."))}</p>`;
    return;
  }
  if (board.status === "error") {
    target.innerHTML = `<p class="status failed">${escapeHtml(board.error || t("text.hypothesis_matrix_failed", "Failed to load hypothesis matrix."))}</p>`;
    return;
  }
  const rows = board.rows || [];
  if (!rows.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.hypothesis_matrix_empty", "No hypothesis matrix rows are available yet."))}</p>`;
    return;
  }
  target.innerHTML = rows.map((row) => {
    const payload = row.payload || {};
    const matrixRows = Array.isArray(payload.rows) ? payload.rows : [];
    const warning = String(payload.warning || "").trim();
    const contextKey = hypothesisCompareContextKey(runId, row.experiment_id);
    const compareState = state.hypothesisCompareByContext[contextKey] || {};
    const defaultA = compareState.keyA || (matrixRows[0]?.hypothesis_key || "");
    const defaultB = compareState.keyB || (matrixRows[1]?.hypothesis_key || matrixRows[0]?.hypothesis_key || "");
    const compareControlIds = hypothesisCompareControlIds(runId, row.experiment_id);
    const selectOptions = matrixRows.map((item) => {
      const key = String(item.hypothesis_key || "");
      const title = String(item.hypothesis || "").trim() || t("text.no_hypothesis", "No hypothesis recorded.");
      return `<option value="${escapeAttr(key)}">${escapeHtml(title)}</option>`;
    }).join("");
    const tableRows = matrixRows.map((item) => {
      const hypothesis = String(item.hypothesis || "").trim() || t("text.no_hypothesis", "No hypothesis recorded.");
      const changedCount = Number(item.changed_params_count || 0);
      const changedLabel = changedCount > 0 ? String(changedCount) : "-";
      const artifacts = `${Number(item.key_table_count || 0)} / ${Number(item.evidence_count || 0)}`;
      const toponymMetric = formatSeriesMetric({ top_label: item.toponym_label, top_value: item.toponym_value });
      const driverMetric = formatSeriesMetric({ top_label: item.driver_label, top_value: item.driver_value });
      const sentimentMetric = formatSeriesMetric({ top_label: item.sentiment_label, top_value: item.sentiment_value });
      const topicMetric = formatSeriesMetric({ top_label: item.topic_label, top_value: item.topic_value });
      const latestRunId = String(item.latest_run_id || "");
      return `
        <tr class="${item.current ? "focus-highlight" : ""}">
          <td>${escapeHtml(hypothesis)}</td>
          <td>${escapeHtml(String(item.run_count || 0))}</td>
          <td>${escapeHtml(latestRunId || "-")}</td>
          <td>${escapeHtml(toponymMetric)}</td>
          <td>${escapeHtml(driverMetric)}</td>
          <td>${escapeHtml(sentimentMetric)}</td>
          <td>${escapeHtml(topicMetric)}</td>
          <td>${escapeHtml(changedLabel)}</td>
          <td>${escapeHtml(artifacts)}</td>
          <td>
            <div class="button-row">
              ${actionButton("focus-hypothesis-run", t("button.open_hypothesis_run", "Open run context"), { target: latestRunId, experiment: row.experiment_id, classes: "primary", disabled: !latestRunId })}
              ${item.report_path ? actionButton("preview-report", t("button.open_report", "Open report"), { path: item.report_path, target: "reportPreview" }) : ""}
              ${actionButton("export-hypothesis-session", t("button.export_hypothesis_session", "Export hypothesis packet"), { experiment: row.experiment_id, target: latestRunId, sessionKey: item.hypothesis_key || "" })}
            </div>
          </td>
        </tr>
      `;
    }).join("");
    return `
      <section class="matrix-group">
        <div class="series-head">
          <h4>${escapeHtml(t(`experiment.${row.experiment_id}.title`, row.experiment_id || "experiment"))}</h4>
          ${actionButton("export-hypothesis-matrix", t("button.export_hypothesis_matrix", "Export matrix"), { experiment: row.experiment_id, target: runId })}
        </div>
        ${warning ? `<p class="muted">${escapeHtml(warning)}</p>` : ""}
        ${matrixRows.length >= 2 ? `
          <div class="hypothesis-compare-controls">
            <label>
              <span>${escapeHtml(t("label.compare_a", "A"))}</span>
              <select id="${escapeAttr(compareControlIds.selectA)}">
                ${selectOptions}
              </select>
            </label>
            <label>
              <span>${escapeHtml(t("label.compare_b", "B"))}</span>
              <select id="${escapeAttr(compareControlIds.selectB)}">
                ${selectOptions}
              </select>
            </label>
            ${actionButton("compare-hypothesis-sessions", t("button.compare_hypothesis", "Compare hypotheses"), { experiment: row.experiment_id, target: runId, classes: "primary" })}
            ${actionButton("export-hypothesis-compare", t("button.export_hypothesis_compare", "Export comparison"), { experiment: row.experiment_id, target: runId })}
          </div>
        ` : ""}
        ${renderHypothesisCompareSummary(compareState)}
        ${tableRows ? `
          <div class="matrix-table-wrap">
            <table class="series-table">
              <thead>
                <tr>
                  <th>${escapeHtml(t("text.hypothesis", "Hypothesis"))}</th>
                  <th>${escapeHtml(t("text.series_runs", "Selected runs"))}</th>
                  <th>${escapeHtml(t("text.last_run", "Last run"))}</th>
                  <th>${escapeHtml(t("metric.toponym_frequency", "Toponym frequency"))}</th>
                  <th>${escapeHtml(t("metric.migration_driver_distribution", "Migration drivers"))}</th>
                  <th>${escapeHtml(t("metric.sentiment_per_toponym", "Sentiment per toponym"))}</th>
                  <th>${escapeHtml(t("metric.topics_per_toponym", "Topics per toponym"))}</th>
                  <th>${escapeHtml(t("text.changed_params", "Changed params"))}</th>
                  <th>${escapeHtml(t("text.artifact_counts", "Artifact counts"))}</th>
                  <th>${escapeHtml(t("button.open", "Open"))}</th>
                </tr>
              </thead>
              <tbody>${tableRows}</tbody>
            </table>
          </div>
        ` : `<p class="muted">${escapeHtml(t("text.hypothesis_matrix_empty", "No hypothesis matrix rows are available yet."))}</p>`}
      </section>
    `;
  }).join("");
  rows.forEach((row) => {
    const payload = row.payload || {};
    const matrixRows = Array.isArray(payload.rows) ? payload.rows : [];
    if (matrixRows.length < 1) return;
    const contextKey = hypothesisCompareContextKey(runId, row.experiment_id);
    const compareState = state.hypothesisCompareByContext[contextKey] || {};
    const defaultA = compareState.keyA || (matrixRows[0]?.hypothesis_key || "");
    const defaultB = compareState.keyB || (matrixRows[1]?.hypothesis_key || matrixRows[0]?.hypothesis_key || "");
    const ids = hypothesisCompareControlIds(runId, row.experiment_id);
    const selectA = document.getElementById(ids.selectA);
    const selectB = document.getElementById(ids.selectB);
    if (selectA && defaultA) selectA.value = defaultA;
    if (selectB && defaultB) selectB.value = defaultB;
  });
}

function compareDeltaBadge(delta) {
  if (!Number.isFinite(delta)) return `<span class="delta-chip missing">${escapeHtml(t("delta.missing", "n/a"))}</span>`;
  const status = delta > 0 ? "up" : (delta < 0 ? "down" : "same");
  const text = `${delta > 0 ? "+" : ""}${delta}`;
  return `<span class="delta-chip ${escapeAttr(status)}">${escapeHtml(text)}</span>`;
}

function renderHypothesisCompareSummary(compareState) {
  if (!compareState || compareState.status === "idle" || !compareState.status) return "";
  if (compareState.status === "loading") {
    return `<p class="muted">${escapeHtml(t("text.hypothesis_compare_loading", "Comparing hypothesis sessions..."))}</p>`;
  }
  if (compareState.status === "error") {
    return `<p class="status failed">${escapeHtml(compareState.error || t("text.hypothesis_compare_failed", "Failed to compare hypothesis sessions."))}</p>`;
  }
  const payload = compareState.payload || {};
  const left = payload.hypothesis_a || {};
  const right = payload.hypothesis_b || {};
  const metricRows = Array.isArray(payload.metric_rows) ? payload.metric_rows : [];
  const deltaCounts = payload.delta_counts || {};
  const metricsHtml = metricRows.map((item) => `
    <div class="comparison-metric">
      <strong>${escapeHtml(item.metric_label || "")}</strong>
      ${compareDeltaBadge(Number(item.delta))}
      <span class="muted">${escapeHtml(`${item.a_label || "-"} (${item.a_value ?? "n/a"}) vs ${item.b_label || "-"} (${item.b_value ?? "n/a"})`)}</span>
    </div>
  `).join("");
  return `
    <div class="hypothesis-compare-summary">
      <p class="muted">
        ${escapeHtml(t("text.compare_current", "Current"))}: ${escapeHtml(left.title || left.key || "-")} |
        ${escapeHtml(t("text.compare_previous", "Previous"))}: ${escapeHtml(right.title || right.key || "-")}
      </p>
      <div class="comparison-metrics">
        ${metricsHtml || `<p class="muted">${escapeHtml(t("text.no_key_table_comparisons", "No comparable key tables found."))}</p>`}
      </div>
      <p class="muted">
        ${escapeHtml(t("text.series_runs", "Selected runs"))}: ${escapeHtml(String(left.run_count || 0))} vs ${escapeHtml(String(right.run_count || 0))}
        (${compareDeltaBadge(Number(deltaCounts.run_count))})
      </p>
    </div>
  `;
}

async function ensureHypothesisMatrixBoard(runId, linkedOutputs, runLimit = 5) {
  if (!runId) return;
  const current = state.hypothesisMatrixByRun[runId];
  if (current?.status === "ready" && current?.runLimit === runLimit) {
    renderHypothesisMatrixBoard(runId);
    return;
  }
  if (current?.status === "loading" && current?.runLimit === runLimit) {
    renderHypothesisMatrixBoard(runId);
    return;
  }
  state.hypothesisMatrixByRun[runId] = { status: "loading", rows: [], runLimit };
  renderHypothesisMatrixBoard(runId);
  const rows = [];
  try {
    for (const output of linkedOutputs || []) {
      const payload = await fetchHypothesisMatrix(output.id, runId, 8, runLimit);
      if (payload?.error) {
        rows.push({ experiment_id: output.id, payload: { rows: [] }, error: String(payload.error) });
        continue;
      }
      rows.push({ experiment_id: output.id, payload, error: "" });
    }
    state.hypothesisMatrixByRun[runId] = { status: "ready", rows, runLimit };
  } catch (error) {
    state.hypothesisMatrixByRun[runId] = { status: "error", rows: [], runLimit, error: String(error) };
  }
  renderHypothesisMatrixBoard(runId);
}

function renderRunFocusedResult() {
  const target = document.getElementById("runFocusedResult");
  if (!target) return;
  const outputs = sortedExperimentOutputs();
  const runById = Object.fromEntries((state.runs || []).map((run) => [run.id, run]));
  const preferredRun = (state.reportRunFilter !== "all" ? runById[state.reportRunFilter] : null)
    || (state.selectedRun ? runById[state.selectedRun] : null)
    || (state.runs || []).find((run) => run.status === "completed")
    || (state.runs || [])[0]
    || null;
  if (!preferredRun) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_runs", "No runs yet."))}</p>`;
    return;
  }
  const linkedOutputs = outputs.filter((item) => item?._run?.id === preferredRun.id);
  const statusClass = runStatusClass(preferredRun.status);
  const runIsCompleted = statusClass === "completed";
  const readiness = researchReadinessSummary(linkedOutputs);
  const rows = linkedOutputs.map((item) => {
    const hypothesis = String(item?.last_params?.hypothesis || "").trim();
    const paramsSummary = formatParamSummary(item?.last_params || {});
    const hasReusableParams = Boolean(item?.last_params && Object.keys(item.last_params).length);
    return `
      <div class="run-focused-item">
        <div>
          <strong>${escapeHtml(t(`experiment.${item.id}.title`, item.title || item.id))}</strong><br>
          <span class="muted">${escapeHtml(t("text.output_summary", "Output"))}: ${item.counts.reports} ${escapeHtml(t("section.reports", "Reports"))}, ${item.counts.evidence} evidence, ${item.counts.tables} CSV</span>
          <div class="run-focused-meta">
            <p class="muted">${escapeHtml(t("text.hypothesis", "Hypothesis"))}: ${escapeHtml(hypothesis || t("text.no_hypothesis", "No hypothesis recorded."))}</p>
            <p class="muted">${escapeHtml(t("text.last_params", "Last params"))}: ${escapeHtml(paramsSummary)}</p>
          </div>
        </div>
        <div class="button-row">
          ${actionButton("open-result-pack", t("button.open_result_pack", "Open result pack"), { experiment: item.id, target: preferredRun.id, classes: "primary", disabled: !runIsCompleted })}
          ${item.primary_report ? actionButton("preview-report", t("button.open_report", "Open report"), { path: item.primary_report.path, target: "reportPreview", classes: "primary" }) : ""}
          ${item.manifest_path ? actionButton("preview-report", t("button.open_manifest", "Open manifest"), { path: item.manifest_path, target: "reportPreview" }) : ""}
          ${hasReusableParams ? actionButton("copy-last-params", t("button.copy_params", "Copy params"), { experiment: item.id, params: JSON.stringify(item.last_params) }) : ""}
          ${actionButton("show-experiment-reports", t("button.open_reports_view", "Open reports view"), { experiment: item.id })}
          ${actionButton("show-experiment-evidence", t("button.open_evidence_view", "Open evidence view"), { experiment: item.id })}
        </div>
      </div>
    `;
  }).join("");
  target.innerHTML = `
    <section class="output-card">
      <div>
        <h3>${escapeHtml(t("text.current_run_focus", "Current run focus"))}</h3>
        <p class="muted">${escapeHtml(t("label.run_id", "Run ID"))}: ${escapeHtml(preferredRun.id)}</p>
        <p class="muted">${escapeHtml(t("text.status", "Status"))}: <span class="status ${escapeAttr(statusClass)}">${escapeHtml(t(`status.${statusClass}`, statusClass))}</span></p>
        <p class="muted">${escapeHtml(t("text.run_label", "Run label"))}: ${escapeHtml(preferredRun.label || preferredRun.preset || preferredRun.id)}</p>
        <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(preferredRun.created_at) || t("text.not_run_yet", "Not run yet."))}</p>
        <p class="muted">${escapeHtml(t("text.readiness_score", "Readiness score"))}: ${readiness.ready}/${readiness.total}</p>
        <div class="readiness-progress" role="progressbar" aria-valuemin="0" aria-valuemax="${readiness.total}" aria-valuenow="${readiness.ready}">
          <div class="readiness-progress-fill" style="width:${Math.round(readiness.ratio * 100)}%"></div>
        </div>
      </div>
      <div class="button-row">
        ${actionButton("open-run-log", t("button.open_run_log", "Open run log"), { target: preferredRun.id, disabled: !preferredRun?.id })}
        ${actionButton("open-result-pack", t("button.open_result_pack", "Open result pack"), { target: preferredRun.id, classes: "primary", disabled: !runIsCompleted })}
        ${actionButton("focus-run-reports", t("button.open_reports_view", "Open reports view"), { target: preferredRun.id, classes: "primary", disabled: !runIsCompleted })}
        ${actionButton("focus-run-evidence", t("button.open_evidence_view", "Open evidence view"), { target: preferredRun.id, disabled: !runIsCompleted })}
        ${actionButton("prepare-coding-from-run", t("button.open_manual_coding", "Open manual coding step"), { target: preferredRun.id, classes: "primary", disabled: !runIsCompleted })}
      </div>
      <div class="artifact-groups">
        ${renderNextResearchAction(linkedOutputs, preferredRun, statusClass, runIsCompleted)}
        <details open>
          <summary>${escapeHtml(t("section.run_comparison_board", "Run comparison board"))}</summary>
          <div id="runComparisonBoard"><p class="muted">${escapeHtml(t("text.comparison_loading", "Loading comparison board..."))}</p></div>
        </details>
        <details open>
          <summary>${escapeHtml(t("section.run_series_trends", "Run series trends"))}</summary>
          <div class="series-controls">
            <label>
              <span>${escapeHtml(t("text.series_limit", "Runs in series"))}</span>
              <select data-action="set-run-series-limit" id="runSeriesLimitSelect">
                ${[3, 5, 7, 10].map((value) => `<option value="${value}" ${Number(state.runSeriesLimit) === value ? "selected" : ""}>${value}</option>`).join("")}
              </select>
            </label>
          </div>
          <div id="runSeriesBoard"><p class="muted">${escapeHtml(t("text.series_loading", "Loading run series..."))}</p></div>
        </details>
        <details open>
          <summary>${escapeHtml(t("section.hypothesis_sessions", "Hypothesis sessions"))}</summary>
          <div id="hypothesisSessionsBoard"><p class="muted">${escapeHtml(t("text.hypothesis_sessions_loading", "Loading hypothesis sessions..."))}</p></div>
        </details>
        <details open>
          <summary>${escapeHtml(t("section.hypothesis_matrix", "Hypothesis comparison matrix"))}</summary>
          <div id="hypothesisMatrixBoard"><p class="muted">${escapeHtml(t("text.hypothesis_matrix_loading", "Loading hypothesis matrix..."))}</p></div>
        </details>
        <details open>
          <summary>${escapeHtml(t("section.reports", "Reports"))} (${linkedOutputs.length})</summary>
          ${linkedOutputs.length ? rows : `<p class="muted">${escapeHtml(t("text.no_linked_outputs_for_run", "No linked outputs were found for this run yet."))}</p>`}
        </details>
        <details open>
          <summary>${escapeHtml(t("section.evidence_digest", "Evidence digest"))}</summary>
          <div id="runEvidenceDigest"></div>
        </details>
        <details open>
          <summary>${escapeHtml(t("section.research_readiness", "Research readiness checklist"))}</summary>
          ${renderResearchReadinessChecklist(linkedOutputs)}
        </details>
      </div>
    </section>
  `;
  void ensureRunComparisonBoard(preferredRun.id, linkedOutputs);
  void ensureRunSeriesBoard(preferredRun.id, linkedOutputs, state.runSeriesLimit);
  void ensureHypothesisSessionsBoard(preferredRun.id, linkedOutputs, state.runSeriesLimit);
  void ensureHypothesisMatrixBoard(preferredRun.id, linkedOutputs, state.runSeriesLimit);
  ensureRunEvidenceDigest(preferredRun.id, linkedOutputs);
}

function renderExperimentOutputs() {
  state.reportExperimentFilter = renderExperimentFilterSelect("reportExperimentFilter", state.reportExperimentFilter);
  state.evidenceExperimentFilter = renderExperimentFilterSelect("evidenceExperimentFilter", state.evidenceExperimentFilter);
  const outputs = sortedExperimentOutputs();
  state.reportRunFilter = renderRunFilterSelect("reportRunFilter", state.reportRunFilter, outputs);
  state.evidenceRunFilter = renderRunFilterSelect("evidenceRunFilter", state.evidenceRunFilter, outputs);
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
  renderRunFocusedResult();
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
  persistUiFilters();
  const query = normalizeSearchText(state.reportArtifactFilter);
  let outputs = filterOutputs(sortedExperimentOutputs(), state.reportExperimentFilter);
  outputs = filterOutputsByRun(outputs, state.reportRunFilter);
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
    state.reportVisiblePrimaryPaths = [];
    target.innerHTML = `<p>${escapeHtml(t("text.no_files", "No files yet."))}</p>`;
    return;
  }
  state.reportVisiblePrimaryPaths = [...new Set(outputs.map((item) => item._primaryFiltered?.path).filter(Boolean))];
  const openDetails = state.reportExpandAll || outputs.length <= 1 || state.reportExperimentFilter !== "all" || state.reportRunFilter !== "all" || Boolean(query);
  const groups = groupOutputsByRun(outputs);
  target.innerHTML = groups.map((group) => {
    const run = group.run;
    const statusClass = runStatusClass(run?.status || "");
    const runHeader = `
      <div class="run-group-head">
        <strong>${escapeHtml(renderRunGroupTitle(run, group.items.length))}</strong>
        <span class="status ${escapeAttr(statusClass)}">${escapeHtml(t(`status.${statusClass}`, statusClass))}</span>
        ${run?.created_at ? `<span class="muted">${escapeHtml(formatDateTime(run.created_at))}</span>` : ""}
      </div>
    `;
    const cards = group.items.map((item) => `
      <details class="output-accordion" ${openDetails ? "open" : ""}>
        <summary>
          <span>${escapeHtml(t(`experiment.${item.id}.title`, item.title || item.id))}</span>
          <span class="status ${escapeAttr(item._primaryFiltered ? "completed" : "missing")}">${escapeHtml(item._primaryFiltered ? t("status.completed", "completed") : t("status.missing", "missing"))}</span>
        </summary>
        <section class="output-card ${item._primaryFiltered ? "" : "muted-card"}">
          <div>
            <p class="muted">${escapeHtml(item.hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${item.hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
            <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(item.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
            <p class="muted">${escapeHtml(t("label.run_id", "Run ID"))}: ${escapeHtml(item?._run?.id || t("text.not_linked_to_run", "Not linked to an active run"))}</p>
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
    return `<section class="output-run-group">${runHeader}${cards}</section>`;
  }).join("");
}

function renderExperimentEvidence() {
  const target = document.getElementById("experimentEvidenceList");
  if (!target) return;
  persistUiFilters();
  const query = normalizeSearchText(state.evidenceArtifactFilter);
  let outputs = filterOutputs(sortedExperimentOutputs(), state.evidenceExperimentFilter);
  outputs = filterOutputsByRun(outputs, state.evidenceRunFilter);
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
  const openDetails = state.evidenceExpandAll || outputs.length <= 1 || state.evidenceExperimentFilter !== "all" || state.evidenceRunFilter !== "all" || Boolean(query);
  const groups = groupOutputsByRun(outputs);
  target.innerHTML = groups.map((group) => {
    const run = group.run;
    const statusClass = runStatusClass(run?.status || "");
    const runHeader = `
      <div class="run-group-head">
        <strong>${escapeHtml(renderRunGroupTitle(run, group.items.length))}</strong>
        <span class="status ${escapeAttr(statusClass)}">${escapeHtml(t(`status.${statusClass}`, statusClass))}</span>
        ${run?.created_at ? `<span class="muted">${escapeHtml(formatDateTime(run.created_at))}</span>` : ""}
      </div>
    `;
    const cards = group.items.map((item) => `
      <details class="output-accordion" ${openDetails ? "open" : ""}>
        <summary>
          <span>${escapeHtml(t(`experiment.${item.id}.title`, item.title || item.id))}</span>
          <span class="status ${escapeAttr(outputHasArtifacts(item) ? "completed" : "missing")}">${escapeHtml(outputHasArtifacts(item) ? t("status.completed", "completed") : t("status.missing", "missing"))}</span>
        </summary>
        <section class="output-card ${item.output_dir ? "" : "muted-card"}">
          <div>
            <p class="muted">${escapeHtml(item.hypothesis ? `${t("text.hypothesis", "Hypothesis")}: ${item.hypothesis}` : t("text.no_hypothesis", "No hypothesis recorded."))}</p>
            <p class="muted">${escapeHtml(t("text.last_run", "Last run"))}: ${escapeHtml(formatDateTime(item.last_run_at) || t("text.not_run_yet", "Not run yet."))}</p>
            <p class="muted">${escapeHtml(t("label.run_id", "Run ID"))}: ${escapeHtml(item?._run?.id || t("text.not_linked_to_run", "Not linked to an active run"))}</p>
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
    return `<section class="output-run-group">${runHeader}${cards}</section>`;
  }).join("");
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
  document.getElementById("runCompareSelection").textContent = `${t("label.compare_a", "A")}: ${state.compareA || "-"} / ${t("label.compare_b", "B")}: ${state.compareB || "-"}`;
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
  const artifactCountsA = payload.artifacts?.a?.counts || {};
  const artifactCountsB = payload.artifacts?.b?.counts || {};
  const differencesHtml = payload.differences?.length
    ? `<div class="table-wrap"><table><thead><tr><th>${escapeHtml(t("text.section", "Section"))}</th><th>${escapeHtml(t("text.field", "Field"))}</th><th>A</th><th>B</th></tr></thead>
        <tbody>${payload.differences.map((item) => `<tr><td>${escapeHtml(item.section || "")}</td><td>${escapeHtml(item.field)}</td><td>${escapeHtml(formatComparisonValue(item.a))}</td><td>${escapeHtml(formatComparisonValue(item.b))}</td></tr>`).join("")}</tbody></table></div>`
    : `<p class="muted">${escapeHtml(t("text.no_differences", "No differences in compared manifest summary fields or key artifact profiles."))}</p>`;
  const tablesHtml = payload.table_comparisons?.length
    ? `<div class="table-wrap"><table><thead><tr><th>${escapeHtml(t("text.table", "Table"))}</th><th>${escapeHtml(t("text.rows_sampled", "Rows sampled"))} A</th><th>${escapeHtml(t("text.preview", "Preview"))} A</th><th>${escapeHtml(t("text.rows_sampled", "Rows sampled"))} B</th><th>${escapeHtml(t("text.preview", "Preview"))} B</th></tr></thead>
        <tbody>${payload.table_comparisons.map((item) => `<tr><td>${escapeHtml(item.table || "")}</td><td>${escapeHtml(item.a?.rows_sampled ?? "missing")}</td><td>${escapeHtml(item.a?.preview || "")}</td><td>${escapeHtml(item.b?.rows_sampled ?? "missing")}</td><td>${escapeHtml(item.b?.preview || "")}</td></tr>`).join("")}</tbody></table></div>`
    : `<p class="muted">${escapeHtml(t("text.no_key_table_comparisons", "No comparable key tables found."))}</p>`;
  target.innerHTML = `
    <div class="status-grid">
      <div class="readiness ready"><strong>${escapeHtml(t("text.artifact_counts", "Artifact counts"))} A</strong><span>${escapeHtml(formatArtifactCounts(artifactCountsA))}</span></div>
      <div class="readiness ready"><strong>${escapeHtml(t("text.artifact_counts", "Artifact counts"))} B</strong><span>${escapeHtml(formatArtifactCounts(artifactCountsB))}</span></div>
    </div>
    <h3>${escapeHtml(t("text.differences", "Differences"))}</h3>
    ${differencesHtml}
    <h3>${escapeHtml(t("text.key_table_comparison", "Key table comparison"))}</h3>
    ${tablesHtml}
  `;
}

async function buildRunComparison(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const status = document.getElementById("runCompareExportStatus");
    if (!state.compareA || !state.compareB) {
      const message = t("hint.run_compare", "Select A and B manifests to compare.");
      if (status) status.textContent = message;
      showToast(message, "info");
      return;
    }
    try {
      const response = await fetch("/api/run-comparison", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ a: state.compareA, b: state.compareB }),
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        const message = payload.error || t("message.failed_build_comparison", "Failed to build run comparison.");
        if (status) status.textContent = message;
        showToast(message, "error", 4200);
        return;
      }
      const markdownPath = payload.paths?.markdown || "";
      const message = `${t("message.comparison_created", "Run comparison created")}: ${markdownPath}`;
      if (status) status.textContent = message;
      if (markdownPath) {
        upsertRecentArtifact(markdownPath, "reportPreview", "report");
        setActiveTab("reports");
        await previewReport(markdownPath, "reportPreview");
      }
      showToast(message, "success");
    } catch (error) {
      const message = `${t("message.failed_build_comparison", "Failed to build run comparison.")}: ${error}`;
      if (status) status.textContent = message;
      showToast(message, "error", 4200);
    }
  });
}

function formatComparisonValue(value) {
  if (value === undefined || value === null) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function formatArtifactCounts(counts) {
  const entries = Object.entries(counts || {});
  if (!entries.length) return "-";
  return entries.map(([key, value]) => `${key}: ${value}`).join(", ");
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
  const hasFinalizedRun = (state.runs || []).some((run) => previousStatuses[run.id] === "running" && run.status !== "running");
  notifyRunTransitions(previousStatuses, state.runs);
  if (state.summary) {
    if (hasFinalizedRun) {
      await loadSummary();
    } else {
      refreshResearchSessionSummary();
      renderExperimentOutputs();
    }
  }
  if (!state.selectedRun && payload.runs.length) state.selectedRun = payload.runs[0].id;
  renderRuns(payload.runs);
  renderRunTimeline(payload.runs);
  const selectedRun = payload.runs.find((run) => run.id === state.selectedRun);
  if (state.selectedRun) {
    const log = await fetch(`/api/run-log?id=${encodeURIComponent(state.selectedRun)}`);
    document.getElementById("runLog").textContent = await log.text();
  }
  if (selectedRun && selectedRun.status !== "running" && state.autoOpenExperiment && selectedRun.preset === state.autoOpenExperiment) {
    const experimentId = state.autoOpenExperiment;
    const target = state.autoOpenTarget;
    state.reportRunFilter = selectedRun.id;
    state.evidenceRunFilter = selectedRun.id;
    state.reportFilterPreset = "current_run";
    state.evidenceFilterPreset = "current_run";
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

function resolveOutputForResultPack(experimentId, runId) {
  const outputs = sortedExperimentOutputs();
  if (experimentId && runId) return outputs.find((item) => item.id === experimentId && item?._run?.id === runId) || null;
  if (experimentId) return outputs.find((item) => item.id === experimentId) || null;
  if (runId) return outputs.find((item) => item?._run?.id === runId) || null;
  return outputs[0] || null;
}

async function openResultPack(experimentId = "", runId = "", triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const output = resolveOutputForResultPack(experimentId, runId);
    if (!output || (!output.primary_report && !output.key_table && !output.key_evidence)) {
      showToast(t("message.result_pack_not_ready", "Result pack is not ready yet."), "info");
      return;
    }
    if (output.id) {
      state.reportExperimentFilter = output.id;
      state.evidenceExperimentFilter = output.id;
    }
    const selectedRun = runId || output?._run?.id || "";
    if (selectedRun) {
      state.reportRunFilter = selectedRun;
      state.evidenceRunFilter = selectedRun;
      state.reportFilterPreset = "current_run";
      state.evidenceFilterPreset = "current_run";
    }
    renderExperimentOutputs();
    setActiveTab("reports");
    if (output.primary_report?.path) await previewReport(output.primary_report.path, "reportPreview");
    if (output.key_table?.path) await previewTable(output.key_table.path, "tablePreview");
    if (output.key_evidence?.path) await previewEvidence(output.key_evidence.path);
    showToast(`${t("message.result_pack_opened", "Result pack opened")}: ${experimentTitle(output.id || experimentId || "run")}`, "success");
  });
}

async function openRunLog(runId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    if (!runId) return;
    state.selectedRun = runId;
    setActiveTab("runs");
    await pollRuns(true);
  });
}

async function focusRunOutputs(runId, tab = "reports") {
  if (!runId) return;
  if (tab === "evidence") {
    state.evidenceRunFilter = runId;
    state.evidenceFilterPreset = "current_run";
    setActiveTab("evidence");
    renderExperimentOutputs();
    return;
  }
  state.reportRunFilter = runId;
  state.reportFilterPreset = "current_run";
  setActiveTab("reports");
  renderExperimentOutputs();
  const output = sortedExperimentOutputs().find((item) => item?._run?.id === runId && item.primary_report);
  if (output?.primary_report?.path) {
    await previewReport(output.primary_report.path, "reportPreview");
  }
}

function applyManualCodingPrefill(prefill = {}) {
  const topInput = document.getElementById("manualCodingToponym");
  const sampleInput = document.getElementById("manualCodingSampleSize");
  const stratifyInput = document.getElementById("manualCodingStratifyBy");
  if (topInput && prefill.toponym) {
    const target = String(prefill.toponym || "").toLowerCase();
    const matched = Array.from(topInput.options || []).find((option) => String(option.value || "").toLowerCase() === target);
    if (matched) topInput.value = matched.value;
  }
  if (sampleInput && Number.isFinite(Number(prefill.sample_size))) {
    sampleInput.value = String(Number(prefill.sample_size));
  }
  if (stratifyInput && prefill.stratify_by) {
    const matched = Array.from(stratifyInput.options || []).find((option) => String(option.value || "") === String(prefill.stratify_by));
    if (matched) stratifyInput.value = matched.value;
  }
}

function openManualCodingStep(prefill = null) {
  setActiveTab("toponymResearch");
  const panel = document.getElementById("manualCodingStepPanel");
  if (!panel) {
    if (prefill) applyManualCodingPrefill(prefill);
    return;
  }
  panel.classList.remove("focus-highlight");
  void panel.offsetWidth;
  panel.classList.add("focus-highlight");
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  if (prefill) applyManualCodingPrefill(prefill);
  setTimeout(() => panel.classList.remove("focus-highlight"), 1200);
}

async function prepareManualCodingFromRun(runId) {
  const cached = state.runEvidenceDigestByRun[runId];
  if (!Array.isArray(cached)) {
    const linkedOutputs = sortedExperimentOutputs().filter((item) => item?._run?.id === runId);
    state.runEvidenceDigestByRun[runId] = await fetchRunEvidenceDigest(runId, linkedOutputs, 5);
  }
  const toponym = recommendedToponymForRun(runId);
  const prefill = {
    toponym,
    sample_size: 120,
    stratify_by: "source",
  };
  openManualCodingStep(prefill);
  if (toponym) {
    showToast(`${t("message.prefill_applied", "Prefill applied")}: ${toponym}`, "info");
  } else {
    showToast(t("message.prefill_default", "Manual coding defaults applied."), "info");
  }
}

function useToponymForCoding(toponymValue) {
  const toponym = String(toponymValue || "").trim();
  if (!toponym) {
    openManualCodingStep();
    return;
  }
  openManualCodingStep({ toponym, sample_size: 120, stratify_by: "source" });
  showToast(`${t("message.toponym_applied", "Toponym applied for coding")}: ${toponym}`, "success");
}

async function focusExperimentReports(experimentId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.reportExperimentFilter = experimentId || "all";
    const runId = experimentId ? (latestRunForExperiment(experimentId)?.id || "") : "";
    state.reportRunFilter = runId || "all";
    state.reportFilterPreset = runId ? "current_run" : "custom";
    setActiveTab("reports");
    renderExperimentOutputs();
    if (!experimentId || experimentId === "all") return;
    await openPrimaryReportForExperiment(experimentId, "reportPreview");
  });
}

async function focusExperimentEvidence(experimentId, triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.evidenceExperimentFilter = experimentId || "all";
    const runId = experimentId ? (latestRunForExperiment(experimentId)?.id || "") : "";
    state.evidenceRunFilter = runId || "all";
    state.evidenceFilterPreset = runId ? "current_run" : "custom";
    setActiveTab("evidence");
    renderExperimentOutputs();
  });
}

function latestRunForExperiment(experimentId) {
  if (!experimentId) return null;
  return latestRunsByPreset()[experimentId] || null;
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

function renderRunTimeline(runs) {
  const target = document.getElementById("runTimeline");
  if (!target) return;
  if (!runs.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_runs", "No runs yet."))}</p>`;
    return;
  }
  target.innerHTML = runs.slice(0, 12).map((run) => {
    const statusClass = runStatusClass(run.status);
    const runIsCompleted = statusClass === "completed";
    const started = formatDateTime(run.created_at) || t("text.not_run_yet", "Not run yet.");
    const finished = run.finished_at ? formatDateTime(run.finished_at) : t("text.running", "running");
    const duration = run.finished_at
      ? formatDuration(Math.max(0, Number(run.finished_at) - Number(run.created_at || run.finished_at)))
      : t("text.running", "running");
    return `
      <div class="run-item">
        <div>
          <strong>${escapeHtml(run.label || run.preset || run.id)}</strong><br>
          <code>${escapeHtml(run.id)}</code><br>
          <span class="muted">${escapeHtml(t("text.started_at", "Started"))}: ${escapeHtml(started)}</span><br>
          <span class="muted">${escapeHtml(t("text.finished_at", "Finished"))}: ${escapeHtml(finished)}</span><br>
          <span class="muted">${escapeHtml(t("text.duration", "Duration"))}: ${escapeHtml(duration)}</span>
        </div>
        <div class="button-row">
          <button class="status ${escapeAttr(statusClass)}" data-run="${escapeAttr(run.id)}">${escapeHtml(t(`status.${statusClass}`, run.status))}</button>
          ${actionButton("open-result-pack", t("button.open_result_pack", "Open result pack"), { target: run.id, disabled: !runIsCompleted })}
          ${actionButton("focus-run-reports", t("button.open_reports_view", "Open reports view"), { target: run.id, disabled: !runIsCompleted })}
          ${actionButton("focus-run-evidence", t("button.open_evidence_view", "Open evidence view"), { target: run.id, disabled: !runIsCompleted })}
        </div>
      </div>
    `;
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
    upsertRecentArtifact(path, targetId || "tablePreview", "table");
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
    if (targetId !== "runLog") upsertRecentArtifact(path, targetId || "reportPreview", "report");
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
    upsertRecentArtifact(path, "evidencePreview", "evidence");
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
  persistSelectedReports();
  renderSelectedReports();
}

function removeReportFromBundle(path) {
  state.selectedReports = state.selectedReports.filter((item) => item !== path);
  persistSelectedReports();
  renderSelectedReports();
}

function moveReportInBundle(path, direction) {
  const index = state.selectedReports.indexOf(path);
  if (index < 0) return;
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= state.selectedReports.length) return;
  const swapped = state.selectedReports.slice();
  const current = swapped[index];
  swapped[index] = swapped[targetIndex];
  swapped[targetIndex] = current;
  state.selectedReports = swapped;
  persistSelectedReports();
  renderSelectedReports();
}

function renderSelectedReports() {
  const target = document.getElementById("selectedReports");
  const meta = document.getElementById("selectedReportMeta");
  if (meta) meta.textContent = `${t("text.selected_reports_count", "Selected reports")}: ${state.selectedReports.length}`;
  if (!target) return;
  if (!state.selectedReports.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_selected_reports", "No selected reports."))}</p>`;
    return;
  }
  target.innerHTML = state.selectedReports.map((path, index) => `
    <div class="selected-item">
      <code>${escapeHtml(path)}</code>
      <div class="button-row">
        ${index > 0 ? actionButton("move-report-up", t("button.move_up", "Move up"), { path }) : ""}
        ${index < state.selectedReports.length - 1 ? actionButton("move-report-down", t("button.move_down", "Move down"), { path }) : ""}
        ${actionButton("remove-report", t("button.remove", "Remove"), { path })}
      </div>
    </div>
  `).join("");
}

async function addWorkflowReportsToBundle(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const outputs = state.summary?.experiment_outputs || [];
    let added = 0;
    for (const step of RESEARCH_WORKFLOW_STEPS) {
      const output = outputs.find((item) => item.id === step.experimentId);
      const path = output?.primary_report?.path;
      if (!path) continue;
      if (state.selectedReports.includes(path)) continue;
      state.selectedReports.push(path);
      added += 1;
    }
    persistSelectedReports();
    renderSelectedReports();
    const status = document.getElementById("reportBundleStatus");
    if (added > 0) {
      if (status) status.textContent = `${t("message.workflow_reports_added", "Workflow reports added")}: ${added}`;
      showToast(`${t("message.workflow_reports_added", "Workflow reports added")}: ${added}`, "success");
      return;
    }
    if (status) status.textContent = t("message.no_workflow_reports", "No workflow reports to add.");
    showToast(t("message.no_workflow_reports", "No workflow reports to add."), "info");
  });
}

async function addVisibleReportsToBundle(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    const visible = state.reportVisiblePrimaryPaths || [];
    let added = 0;
    for (const path of visible) {
      if (state.selectedReports.includes(path)) continue;
      state.selectedReports.push(path);
      added += 1;
    }
    persistSelectedReports();
    renderSelectedReports();
    const status = document.getElementById("reportBundleStatus");
    if (added > 0) {
      if (status) status.textContent = `${t("message.visible_reports_added", "Visible reports added")}: ${added}`;
      showToast(`${t("message.visible_reports_added", "Visible reports added")}: ${added}`, "success");
      return;
    }
    if (status) status.textContent = t("message.no_visible_reports", "No visible reports to add.");
    showToast(t("message.no_visible_reports", "No visible reports to add."), "info");
  });
}

async function clearSelectedReports(triggerButton = null) {
  return withButtonBusy(triggerButton, async () => {
    state.selectedReports = [];
    persistSelectedReports();
    renderSelectedReports();
    const status = document.getElementById("reportBundleStatus");
    if (status) status.textContent = t("message.selected_reports_cleared", "Selected reports cleared.");
  });
}

function recentArtifactLabel(path) {
  const normalized = String(path || "").replaceAll("\\", "/");
  const parts = normalized.split("/");
  return parts[parts.length - 1] || path || "";
}

function persistRecentArtifacts() {
  try {
    localStorage.setItem("webapp.recentArtifacts", JSON.stringify(state.recentArtifacts || []));
  } catch (_) {
    // ignore persistence issues for local-only UX cache
  }
}

function upsertRecentArtifact(path, target, mode) {
  if (!path || !mode) return;
  const key = `${mode}|${path}`;
  const others = (state.recentArtifacts || []).filter((item) => `${item.mode}|${item.path}` !== key);
  const next = [{ path, target, mode, label: recentArtifactLabel(path) }, ...others].slice(0, 20);
  state.recentArtifacts = next;
  persistRecentArtifacts();
  renderRecentArtifacts();
}

function removeRecentArtifact(path, mode) {
  const key = `${mode}|${path}`;
  state.recentArtifacts = (state.recentArtifacts || []).filter((item) => `${item.mode}|${item.path}` !== key);
  persistRecentArtifacts();
  renderRecentArtifacts();
}

function renderRecentArtifacts() {
  const target = document.getElementById("recentArtifacts");
  if (!target) return;
  if (!state.recentArtifacts.length) {
    target.innerHTML = `<p class="muted">${escapeHtml(t("text.no_recent_artifacts", "No recent artifacts yet."))}</p>`;
    return;
  }
  target.innerHTML = state.recentArtifacts.map((item) => `
    <div class="selected-item">
      <div>
        <strong>${escapeHtml(item.label || recentArtifactLabel(item.path))}</strong><br>
        <code>${escapeHtml(item.path)}</code><br>
        <span class="muted">${escapeHtml(t(`label.artifact_mode.${item.mode}`, item.mode || ""))}</span>
      </div>
      <div class="button-row">
        ${actionButton("open-recent-artifact", t("button.open", "Open"), { path: item.path, target: item.target || "", experiment: item.mode })}
        ${actionButton("remove-recent-artifact", t("button.remove", "Remove"), { path: item.path, experiment: item.mode })}
      </div>
    </div>
  `).join("");
}

async function openRecentArtifact(path, target, mode, triggerButton = null) {
  if (!path || !mode) return;
  if (mode === "table") {
    setActiveTab("results");
    await previewTable(path, target || "tablePreview", triggerButton);
    return;
  }
  if (mode === "evidence") {
    setActiveTab("evidence");
    await previewEvidence(path, triggerButton);
    return;
  }
  setActiveTab(target === "toponymResearchPreview" ? "toponymResearch" : "reports");
  await previewReport(path, target || "reportPreview", triggerButton);
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

function formatDuration(secondsValue) {
  const total = Number(secondsValue || 0);
  if (!Number.isFinite(total) || total < 1) return "0s";
  const seconds = Math.round(total);
  const minutes = Math.floor(seconds / 60);
  const rem = seconds % 60;
  if (minutes === 0) return `${seconds}s`;
  if (minutes < 60) return `${minutes}m ${rem}s`;
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  return `${hours}h ${remMinutes}m`;
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
  const params = options.params || "";
  const sessionKey = options.sessionKey || "";
  const classes = options.classes || "";
  const disabled = options.disabled ? " disabled" : "";
  return `<button${classes ? ` class="${escapeAttr(classes)}"` : ""} data-action="${escapeAttr(action)}"${path ? ` data-path="${escapeAttr(path)}"` : ""}${target ? ` data-target="${escapeAttr(target)}"` : ""}${experiment ? ` data-experiment="${escapeAttr(experiment)}"` : ""}${params ? ` data-params="${escapeAttr(params)}"` : ""}${sessionKey ? ` data-session-key="${escapeAttr(sessionKey)}"` : ""}${disabled}>${escapeHtml(label)}</button>`;
}

loadLanguagePack().then(() => loadSummary()).then(() => pollRuns(true));
