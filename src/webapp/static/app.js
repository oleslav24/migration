const state = { summary: null, selectedRun: null, polling: false, selectedTablePath: null, selectedEvidencePath: null, compareA: null, compareB: null, selectedReports: [] };

document.getElementById("methodSampleButton")?.addEventListener("click", () => analyzeMethodSample());
document.getElementById("tableRefreshButton")?.addEventListener("click", () => {
  if (state.selectedTablePath) previewTable(state.selectedTablePath, "tablePreview");
});
document.getElementById("tableFilterInput")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && state.selectedTablePath) previewTable(state.selectedTablePath, "tablePreview");
});
document.getElementById("evidenceRefreshButton")?.addEventListener("click", () => {
  if (state.selectedEvidencePath) previewEvidence(state.selectedEvidencePath);
});
document.getElementById("reportBundleButton")?.addEventListener("click", () => buildReportBundle());

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.tab).classList.add("active");
  });
});

async function loadSummary() {
  const response = await fetch("/api/summary");
  state.summary = await response.json();
  renderSummary();
}

function renderSummary() {
  const files = state.summary.files;
  const project = state.summary.project_state;
  const cards = [
    ["Datasets", project.datasets.length],
    ["Experiments", state.summary.experiments.length],
    ["Agents", project.agents.length],
    ["Pipeline CSV", files.pipeline.length],
    ["Discovery CSV", files.discovery.length],
    ["Agent files", state.summary.agent_files.length],
  ];
  document.getElementById("summaryCards").innerHTML = cards.map(([label, value]) => `
    <div class="card"><strong>${value}</strong><span>${label}</span></div>
  `).join("");
  renderReadiness();
  Object.entries(state.summary.charts).forEach(([id, chart]) => drawBars(id, chart));
  renderDatasets();
  renderExperiments();
  renderMethods();
  renderRunManifests();
  renderSelectedReports();
  renderSafetyModel();
  renderAgentContracts();
  renderFiles("pipelineFiles", files.pipeline, "tablePreview");
  renderFiles("discoveryFiles", files.discovery, "discoveryPreview");
  renderFiles("agentFiles", state.summary.agent_files, "evidencePreview");
  renderFiles("reportFiles", state.summary.agent_files.filter((file) => file.name.endsWith(".md")), "reportPreview");
  document.getElementById("configPreview").textContent = JSON.stringify(state.summary.config, null, 2);
}

function renderReadiness() {
  const target = document.getElementById("readinessList");
  if (!target) return;
  target.innerHTML = state.summary.project_state.readiness.map((item) => `
    <div class="readiness ${escapeAttr(item.status)}">
      <strong>${escapeHtml(item.status)}</strong>
      <span>${escapeHtml(item.label)}</span>
    </div>
  `).join("");
}

function renderDatasets() {
  const target = document.getElementById("datasetList");
  if (!target) return;
  const datasets = state.summary.project_state.datasets || [];
  if (!datasets.length) {
    target.innerHTML = `<p>No configured datasets.</p>`;
    return;
  }
  target.innerHTML = `<div class="file-list">${datasets.map((dataset) => `
    <div class="file">
      <div>
        <strong>${escapeHtml(dataset.source)} / ${escapeHtml(dataset.name || dataset.path)}</strong><br>
        <code>${escapeHtml(dataset.resolved_path || dataset.path)}</code><br>
        <span class="muted">${escapeHtml(dataset.row_count_note || "")}${dataset.row_count !== null && dataset.row_count !== undefined ? ` / ${formatNumber(dataset.row_count)} rows` : ""}</span>
      </div>
      ${dataset.exists ? `<button onclick="previewTable('${escapeAttr(dataset.resolved_path || dataset.path)}','datasetPreview')">Preview</button>` : `<span class="status failed">missing</span>`}
    </div>
  `).join("")}</div>`;
}

function drawBars(id, chart) {
  const target = document.getElementById(id);
  if (!target) return;
  if (!chart.labels.length) {
    target.innerHTML = `<p class="muted">No data yet.</p>`;
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
      <button class="primary run-button" data-preset="${escapeAttr(id)}">Run</button>
    </section>
  `).join("");
  target.querySelectorAll(".run-button").forEach((button) => {
    button.addEventListener("click", () => startRun(button.dataset.preset));
  });
}

function renderExperiments() {
  const target = document.getElementById("experimentList");
  if (!target) return;
  const experiments = state.summary.experiments || [];
  if (!experiments.length) {
    target.innerHTML = `<p>No registry experiments configured.</p>`;
    return;
  }
  target.innerHTML = experiments.map((experiment) => `
    <section class="panel preset">
      <div>
        <h2>${escapeHtml(experiment.title)}</h2>
        <p>${escapeHtml(experiment.id)} / ${escapeHtml(experiment.runner)} / ${escapeHtml(experiment.status || "unknown")}</p>
        <code>${escapeHtml(experiment.agent_contract)}</code>
        <p class="muted">Outputs: ${escapeHtml((experiment.expected_outputs || []).join(", "))}</p>
        <div class="param-grid">${renderParameterInputs(experiment)}</div>
      </div>
      <button class="primary experiment-button" data-experiment="${escapeAttr(experiment.id)}">Run</button>
    </section>
  `).join("");
  target.querySelectorAll(".experiment-button").forEach((button) => {
    button.addEventListener("click", () => startExperiment(button.dataset.experiment));
  });
}

function renderParameterInputs(experiment) {
  const parameters = experiment.parameters || [];
  if (!parameters.length) return `<p class="muted">No configurable parameters.</p>`;
  return parameters.map((param) => `
    <label>
      <span>${escapeHtml(param.name)}</span>
      <input
        type="${param.type === "int" ? "number" : "text"}"
        data-param-experiment="${escapeAttr(experiment.id)}"
        data-param-name="${escapeAttr(param.name)}"
        value="${escapeAttr(param.default ?? "")}"
        ${param.min !== undefined ? `min="${escapeAttr(param.min)}"` : ""}
        ${param.max !== undefined ? `max="${escapeAttr(param.max)}"` : ""}
      />
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
      <p><strong>Backend:</strong> ${escapeHtml(method.backend)}</p>
      <p><strong>Stage:</strong> ${escapeHtml(method.stage || "unspecified")}</p>
      <p><strong>Inputs:</strong> ${escapeHtml((method.inputs || []).join(", "))}</p>
      <p><strong>Outputs:</strong> ${escapeHtml((method.outputs || []).join(", "))}</p>
      <p><strong>Quality gates:</strong> ${escapeHtml((method.quality_gates || []).join("; "))}</p>
      <p><strong>Used by:</strong> ${escapeHtml((method.experiments || []).join(", "))}</p>
      <p class="muted">${escapeHtml(method.limitations)}</p>
    </section>
  `).join("");
}

async function analyzeMethodSample() {
  const target = document.getElementById("methodSampleResult");
  const text = document.getElementById("methodSampleText").value;
  target.innerHTML = `<p class="muted">Analyzing sample...</p>`;
  try {
    const response = await fetch("/api/method-sample", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const payload = await response.json();
    if (!response.ok || payload.error) {
      target.innerHTML = `<p class="status failed">${escapeHtml(payload.error || "Method analysis failed.")}</p>`;
      return;
    }
    target.innerHTML = `
      <section class="method-card result-card">
        <h3>Normalized text</h3>
        <p>${escapeHtml(payload.normalized_text)}</p>
      </section>
      ${(payload.results || []).map((item) => `
        <section class="method-card result-card">
          <h3>${escapeHtml(item.method)}</h3>
          <p><strong>Label:</strong> ${escapeHtml(item.label)}</p>
          <p><strong>Confidence:</strong> ${escapeHtml(item.confidence)}</p>
          <pre>${escapeHtml(typeof item.evidence === "string" ? item.evidence : JSON.stringify(item.evidence, null, 2))}</pre>
        </section>
      `).join("")}
    `;
  } catch (error) {
    target.innerHTML = `<p class="status failed">Method analysis failed: ${escapeHtml(error)}</p>`;
  }
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

function renderRunManifests() {
  const target = document.getElementById("runManifestList");
  if (!target) return;
  const manifests = state.summary.run_manifests || [];
  if (!manifests.length) {
    target.innerHTML = `<p>No run manifests found.</p>`;
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
        <button data-manifest-open="${escapeAttr(manifest.path)}">Open</button>
        <button data-manifest-a="${escapeAttr(manifest.path)}">A</button>
        <button data-manifest-b="${escapeAttr(manifest.path)}">B</button>
      </div>
    </div>
  `).join("");
  target.querySelectorAll("[data-manifest-open]").forEach((button) => {
    button.addEventListener("click", () => previewReport(button.dataset.manifestOpen, "runLog"));
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
      <div class="readiness ready"><strong>mode</strong><span>${escapeHtml(safety.execution_model || "")}</span></div>
      <div class="readiness ready"><strong>read</strong><span>${escapeHtml((safety.allowed_read_roots || []).join(", "))}</span></div>
      <div class="readiness ready"><strong>write</strong><span>${escapeHtml((safety.allowed_write_roots || []).join(", "))}</span></div>
    </div>
    <h3>Forbidden actions</h3>
    <ul>${(safety.forbidden || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <h3>Review gates</h3>
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
    target.innerHTML = `<p class="muted">No differences in compared manifest summary fields.</p>`;
    return;
  }
  target.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Field</th><th>A</th><th>B</th></tr></thead>
    <tbody>${payload.differences.map((item) => `<tr><td>${escapeHtml(item.field)}</td><td>${escapeHtml(JSON.stringify(item.a))}</td><td>${escapeHtml(JSON.stringify(item.b))}</td></tr>`).join("")}</tbody></table></div>`;
}

async function startExperiment(experiment) {
  document.getElementById("runLog").textContent = `Starting ${experiment}...`;
  const params = collectExperimentParams(experiment);
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ experiment, params }),
    });
    const run = await response.json();
    if (!response.ok) {
      document.getElementById("runLog").textContent = run.error || "Failed to start experiment.";
      return;
    }
    state.selectedRun = run.id;
    await pollRuns(true);
  } catch (error) {
    document.getElementById("runLog").textContent = `Failed to start experiment: ${error}`;
  }
}

async function startRun(preset) {
  document.getElementById("runLog").textContent = `Starting ${preset}...`;
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preset }),
    });
    const run = await response.json();
    if (!response.ok) {
      document.getElementById("runLog").textContent = run.error || "Failed to start run.";
      return;
    }
    state.selectedRun = run.id;
    await pollRuns(true);
  } catch (error) {
    document.getElementById("runLog").textContent = `Failed to start run: ${error}`;
  }
}

async function pollRuns(force = false) {
  if (state.polling && !force) return;
  state.polling = true;
  const response = await fetch("/api/runs");
  const payload = await response.json();
  if (!state.selectedRun && payload.runs.length) state.selectedRun = payload.runs[0].id;
  renderRuns(payload.runs);
  if (state.selectedRun) {
    const log = await fetch(`/api/run-log?id=${encodeURIComponent(state.selectedRun)}`);
    document.getElementById("runLog").textContent = await log.text();
  }
  state.polling = false;
  if (payload.runs.some((run) => run.status === "running")) setTimeout(() => pollRuns(), 1500);
}

function renderRuns(runs) {
  const target = document.getElementById("runList");
  if (!target) return;
  if (!runs.length) {
    target.innerHTML = `<p>No runs yet.</p>`;
    return;
  }
  target.innerHTML = runs.slice(0, 12).map((run) => {
    const statusClass = run.status.startsWith("failed") ? "failed" : run.status;
    return `<div class="run-item">
      <div><strong>${escapeHtml(run.label)}</strong><br><code>${escapeHtml(run.id)}</code></div>
      <button class="status ${escapeAttr(statusClass)}" data-run="${escapeAttr(run.id)}">${escapeHtml(run.status)}</button>
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
    target.innerHTML = `<p>No files yet.</p>`;
    return;
  }
  target.innerHTML = `<div class="file-list">${files.map((file) => `
    <div class="file">
      <div><strong>${escapeHtml(file.name)}</strong><br><code>${escapeHtml(file.path)}</code></div>
      ${previewId === "evidencePreview" && (file.name.endsWith(".csv") || file.name.endsWith(".json")) ? `<button onclick="previewEvidence('${escapeAttr(file.path)}')">Browse</button>` : ""}
      ${previewId !== "evidencePreview" && file.name.endsWith(".csv") ? `<button onclick="previewTable('${escapeAttr(file.path)}','${previewId}')">Preview</button>` : ""}
      ${previewId !== "evidencePreview" && (file.name.endsWith(".md") || file.name.endsWith(".json")) ? `<button onclick="previewReport('${escapeAttr(file.path)}','${previewId}')">Open</button>` : ""}
      ${previewId === "reportPreview" && (file.name.endsWith(".md") || file.name.endsWith(".json") || file.name.endsWith(".csv")) ? `<button onclick="addReportToBundle('${escapeAttr(file.path)}')">Add</button>` : ""}
    </div>
  `).join("")}</div>`;
}

async function previewTable(path, targetId) {
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
    meta.textContent = `${payload.returned_rows} rows shown / ${payload.scanned_rows} rows scanned / ${formatBytes(payload.size)}`;
  }
  if (!payload.rows.length) {
    target.innerHTML = `<p class="muted">No matching rows.</p>`;
    return;
  }
  target.innerHTML = `<div class="table-wrap"><table><thead><tr>${payload.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
    <tbody>${payload.rows.map((row) => `<tr>${payload.columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

async function previewReport(path, targetId = "reportPreview") {
  const response = await fetch(`/api/report?path=${encodeURIComponent(path)}`);
  document.getElementById(targetId).textContent = await response.text();
}

async function previewEvidence(path) {
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
  meta.textContent = `${payload.returned_rows} rows shown / ${payload.total_rows} evidence rows`;
  if (!payload.rows.length) {
    target.innerHTML = `<p class="muted">No matching evidence.</p>`;
    return;
  }
  target.innerHTML = `<div class="table-wrap"><table><thead><tr>${payload.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
    <tbody>${payload.rows.map((row) => `<tr>${payload.columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
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
    target.innerHTML = `<p class="muted">No selected reports.</p>`;
    return;
  }
  target.innerHTML = state.selectedReports.map((path) => `
    <div class="selected-item">
      <code>${escapeHtml(path)}</code>
      <button onclick="removeReportFromBundle('${escapeAttr(path)}')">Remove</button>
    </div>
  `).join("");
}

async function buildReportBundle() {
  const status = document.getElementById("reportBundleStatus");
  status.textContent = "Building bundle...";
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
    status.textContent = payload.error || "Failed to build report bundle.";
    return;
  }
  status.textContent = `Bundle created: ${payload.path} (${payload.count} files)`;
  await previewReport(payload.path, "reportPreview");
}

function formatNumber(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
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

loadSummary().then(() => pollRuns(true));
