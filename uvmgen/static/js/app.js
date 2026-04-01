// UVM Testbench Generator - Main Application

const API = "";

// ── State ────────────────────────────────────────────────────────────────────
let ports = [];
let tests = [{ name: "base_test", description: "Basic sanity test", num_transactions: 100, timeout_ns: 10000, has_reset_sequence: true }];
let generatedFiles = {};
let activeFile = null;
const sessionId = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);

// ── Initialization ───────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  renderPorts();
  renderTests();
  initAuth();
});

// ── Build config ─────────────────────────────────────────────────────────────
function buildConfig() {
  return {
    project_name: el("project_name").value.trim() || "my_dut",
    module_name: el("module_name").value.trim(),
    ports: ports.map(p => ({
      name: p.name, direction: p.direction,
      width: parseInt(p.width) || 1, signal_type: p.signal_type || "logic", description: p.description || "",
    })),
    protocol: {
      protocol: el("protocol_type").value,
      data_width: parseInt(el("data_width").value) || 32,
      addr_width: parseInt(el("addr_width").value) || 32,
      clock_freq_mhz: parseFloat(el("clock_freq").value) || 100,
    },
    agent: {
      is_active: el("agent_active").checked, has_driver: el("agent_driver").checked,
      has_monitor: el("agent_monitor").checked, has_sequencer: el("agent_sequencer").checked,
      has_coverage: el("agent_coverage").checked,
    },
    tests: tests,
    components: {
      interface: el("comp_interface").checked, sequence_item: el("comp_sequence_item").checked,
      sequences: el("comp_sequences").checked, driver: el("comp_driver").checked,
      monitor: el("comp_monitor").checked, sequencer: el("comp_sequencer").checked,
      agent: el("comp_agent").checked, scoreboard: el("comp_scoreboard").checked,
      coverage: el("comp_coverage").checked, env: el("comp_env").checked,
      test: el("comp_test").checked, top: el("comp_top").checked, package: el("comp_package").checked,
    },
  };
}

// ── Port Management ──────────────────────────────────────────────────────────
function addPort(name = "", direction = "input", width = 1, signal_type = "logic") {
  ports.push({ name, direction, width, signal_type, description: "" });
  renderPorts();
}
function removePort(idx) { ports.splice(idx, 1); renderPorts(); }
function updatePort(idx, field, value) { ports[idx][field] = value; }

function renderPorts() {
  const container = el("ports-container");
  const empty = el("ports-empty");
  if (ports.length === 0) { container.innerHTML = ""; empty.style.display = "block"; return; }
  empty.style.display = "none";
  container.innerHTML = ports.map((p, i) => `
    <div class="port-row">
      <input class="input flex-1" placeholder="name" value="${esc(p.name)}" onchange="updatePort(${i},'name',this.value)" />
      <select class="input w-24" onchange="updatePort(${i},'direction',this.value)">
        <option value="input" ${p.direction==="input"?"selected":""}>input</option>
        <option value="output" ${p.direction==="output"?"selected":""}>output</option>
        <option value="inout" ${p.direction==="inout"?"selected":""}>inout</option>
      </select>
      <input class="input w-16 text-center" type="number" min="1" value="${p.width}" onchange="updatePort(${i},'width',parseInt(this.value)||1)" />
      <button onclick="removePort(${i})" class="transition p-1" style="color:#9ca3af;" onmouseover="this.style.color='#f87171'" onmouseout="this.style.color='#9ca3af'" title="Remove">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>
  `).join("");
}

async function loadProtocolPorts() {
  const proto = el("protocol_type").value;
  if (proto === "custom") { toast("Select a protocol first", "error"); return; }
  try {
    const dw = parseInt(el("data_width").value) || 32;
    const aw = parseInt(el("addr_width").value) || 32;
    const res = await fetch(`${API}/api/protocol/${proto}/ports?data_width=${dw}&addr_width=${aw}`);
    const data = await res.json();
    ports = data.ports.map(p => ({ name: p.name, direction: p.direction, width: p.width, signal_type: p.signal_type || "logic", description: p.description || "" }));
    renderPorts();
    toast(`Loaded ${ports.length} ports from ${proto.toUpperCase()}`);
  } catch (e) { toast("Failed to load: " + e.message, "error"); }
}

function onProtocolChange() {
  const proto = el("protocol_type").value;
  el("data_width").value = (proto === "spi" || proto === "uart") ? 8 : 32;
}

// ── Test Management ──────────────────────────────────────────────────────────
function addTest() {
  tests.push({ name: `test_${tests.length}`, description: "", num_transactions: 100, timeout_ns: 10000, has_reset_sequence: true });
  renderTests();
}
function removeTest(idx) { if (tests.length <= 1) { toast("Need at least one test", "error"); return; } tests.splice(idx, 1); renderTests(); }
function updateTest(idx, field, value) { tests[idx][field] = value; }

function renderTests() {
  el("tests-container").innerHTML = tests.map((t, i) => `
    <div class="test-card">
      <div class="flex items-center justify-between">
        <span class="text-sm font-semibold" style="color:#a5b4fc;">Test #${i+1}</span>
        ${tests.length > 1 ? `<button onclick="removeTest(${i})" class="text-sm" style="color:#9ca3af;" onmouseover="this.style.color='#f87171'" onmouseout="this.style.color='#9ca3af'">Remove</button>` : ""}
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div><label class="label">Name</label><input class="input" value="${esc(t.name)}" onchange="updateTest(${i},'name',this.value)" /></div>
        <div><label class="label">Transactions</label><input class="input" type="number" min="1" value="${t.num_transactions}" onchange="updateTest(${i},'num_transactions',parseInt(this.value)||100)" /></div>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div><label class="label">Timeout (ns)</label><input class="input" type="number" min="1" value="${t.timeout_ns}" onchange="updateTest(${i},'timeout_ns',parseInt(this.value)||10000)" /></div>
        <div class="flex items-end pb-1"><label class="checkbox-label"><input type="checkbox" class="checkbox" ${t.has_reset_sequence?"checked":""} onchange="updateTest(${i},'has_reset_sequence',this.checked)" /> Reset seq</label></div>
      </div>
    </div>
  `).join("");
}

// ── Generation ───────────────────────────────────────────────────────────────
async function generatePreview() {
  const config = buildConfig();
  try {
    const res = await fetch(`${API}/api/generate`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(config) });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Generation failed"); }
    const data = await res.json();
    generatedFiles = data.files;
    renderFileTabs();
    const first = Object.keys(generatedFiles)[0];
    if (first) showFile(first);
    toast(`Generated ${Object.keys(generatedFiles).length} files`);
    logGeneration(config);
  } catch (e) { toast("Error: " + e.message, "error"); }
}

function logGeneration(config) {
  try {
    const sb = getSbClient();
    if (!sb) return;
    sb.auth.getUser().then(r => {
      const u = r.data?.user;
      sb.rpc('log_generation', {
        p_session_id: sessionId,
        p_user_id: u?.id || null,
        p_user_email: u?.email || "",
        p_user_name: u?.user_metadata?.full_name || "",
        p_project_name: config.project_name,
        p_protocol: config.protocol.protocol,
        p_file_count: Object.keys(generatedFiles).length,
        p_config_json: config,
        p_is_guest: !u,
      });
    });
  } catch (_) {}
}

async function downloadZip() {
  if (!isLoggedIn()) {
    showAuthModal("login");
    toast("Please sign in to download ZIP files", "error");
    return;
  }

  const config = buildConfig();
  try {
    const res = await fetch(`${API}/api/generate/zip`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(config) });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `${config.project_name}_uvm_tb.zip`; a.click();
    URL.revokeObjectURL(url);

    const sb = getSbClient();
    if (sb && isLoggedIn()) {
      sb.auth.getUser().then(r => {
        if (r.data?.user) {
          const u = r.data.user;
          sb.from("download_log").insert({
            user_id: u.id,
            user_email: u.email || "",
            user_name: u.user_metadata?.full_name || "",
            project_name: config.project_name,
            protocol: config.protocol.protocol,
            file_count: Object.keys(generatedFiles).length || 13,
            config_json: config,
          });
        }
      });
    }
    toast("ZIP downloaded!");
  } catch (e) { toast("Error: " + e.message, "error"); }
}

// ── File Tabs & Preview ──────────────────────────────────────────────────────
function renderFileTabs() {
  const container = el("file-tabs");
  const names = Object.keys(generatedFiles);
  const svFiles = names.filter(f => f.endsWith(".sv"));
  const utilFiles = names.filter(f => !f.endsWith(".sv"));
  const tabHtml = (fname) => {
    const shortName = fname.replace(/\.sv$/, "");
    const icon = getFileIcon(fname);
    return `<button class="file-tab ${fname === activeFile ? 'active' : ''}" onclick="showFile('${esc(fname)}')">${icon} ${shortName}</button>`;
  };
  container.innerHTML =
    svFiles.map(tabHtml).join("") +
    (utilFiles.length ? '<span class="text-gray-600 px-1">|</span>' : '') +
    utilFiles.map(tabHtml).join("");
}

function showFile(fname) {
  activeFile = fname;
  renderFileTabs();
  const content = generatedFiles[fname] || "";
  const lang = fname.endsWith(".sv") ? "verilog" : fname.endsWith(".sh") ? "bash" : "plaintext";
  let highlighted;
  try { highlighted = hljs.highlight(content, { language: lang }).value; }
  catch { highlighted = esc(content); }
  el("code-preview").innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <span class="text-base font-semibold" style="color:#e5e7eb;">${esc(fname)}</span>
      <button onclick="copyToClipboard('${esc(fname)}')" class="btn-sm btn-secondary" style="display:inline-flex;align-items:center;gap:6px;">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
        Copy
      </button>
    </div>
    <pre><code class="hljs language-${lang}">${highlighted}</code></pre>
  `;
}

function getFileIcon(fname) {
  if (fname === "file.list")         return '<span class="text-sky-400">FL</span>';
  if (fname === "README.txt")        return '<span class="text-lime-400">RM</span>';
  if (fname === "run.sh")            return '<span class="text-orange-300">SH</span>';
  if (fname.includes("_if."))        return '<span class="text-blue-400">IF</span>';
  if (fname.includes("_driver"))     return '<span class="text-green-400">DR</span>';
  if (fname.includes("_monitor"))    return '<span class="text-yellow-400">MN</span>';
  if (fname.includes("_sequencer"))  return '<span class="text-purple-400">SQ</span>';
  if (fname.includes("_agent"))      return '<span class="text-orange-400">AG</span>';
  if (fname.includes("_scoreboard")) return '<span class="text-red-400">SB</span>';
  if (fname.includes("_coverage"))   return '<span class="text-cyan-400">CV</span>';
  if (fname.includes("_env"))        return '<span class="text-emerald-400">EN</span>';
  if (fname.includes("_test"))       return '<span class="text-rose-400">TS</span>';
  if (fname.includes("_tb_top"))     return '<span class="text-amber-400">TB</span>';
  if (fname.includes("_pkg"))        return '<span class="text-teal-400">PK</span>';
  if (fname.includes("_seq"))        return '<span class="text-violet-400">SE</span>';
  return '<span class="text-gray-400">SV</span>';
}

function copyToClipboard(fname) {
  const content = generatedFiles[fname]; if (!content) return;
  navigator.clipboard.writeText(content).then(() => toast("Copied to clipboard!"), () => toast("Failed to copy", "error"));
}

// ── Example ──────────────────────────────────────────────────────────────────
function loadExample() {
  el("project_name").value = "axi_slave"; el("module_name").value = "";
  el("protocol_type").value = "axi4_lite"; el("data_width").value = 32; el("addr_width").value = 32; el("clock_freq").value = 100;
  tests = [
    { name: "sanity_test", description: "Basic read/write", num_transactions: 50, timeout_ns: 5000, has_reset_sequence: true },
    { name: "stress_test", description: "High throughput", num_transactions: 500, timeout_ns: 50000, has_reset_sequence: true },
    { name: "error_test", description: "Error injection", num_transactions: 100, timeout_ns: 10000, has_reset_sequence: true },
  ];
  renderTests();
  loadProtocolPorts();
  toast("AXI4-Lite example loaded!");
}

// ── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, type = "success") {
  const existing = document.querySelector(".toast"); if (existing) existing.remove();
  const div = document.createElement("div"); div.className = `toast ${type}`;
  div.innerHTML = `
    ${type === "success"
      ? '<svg class="w-5 h-5 text-green-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
      : '<svg class="w-5 h-5 text-red-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'}
    <span>${esc(msg)}</span>`;
  document.body.appendChild(div);
  requestAnimationFrame(() => div.classList.add("show"));
  setTimeout(() => { div.classList.remove("show"); setTimeout(() => div.remove(), 300); }, 3000);
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function el(id) { return document.getElementById(id); }
function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;"); }
