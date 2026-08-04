const $ = (id) => document.getElementById(id);

function loadCfg() {
  $("agentsUrl").value = localStorage.getItem("zyn_agents_url") || "http://localhost:8081";
  $("apiKey").value = localStorage.getItem("zyn_api_key") || "";
}

function saveCfg() {
  localStorage.setItem("zyn_agents_url", $("agentsUrl").value.trim());
  localStorage.setItem("zyn_api_key", $("apiKey").value.trim());
}

function base() {
  return ($("agentsUrl").value || "http://localhost:8081").replace(/\/$/, "");
}

function headers(json = true) {
  const h = {};
  if (json) h["Content-Type"] = "application/json";
  const key = $("apiKey").value.trim();
  if (key) h["Authorization"] = `Bearer ${key}`;
  return h;
}

async function api(path, opts = {}) {
  const r = await fetch(`${base()}${path}`, opts);
  const text = await r.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }
  if (!r.ok) throw new Error(typeof data === "string" ? data : JSON.stringify(data, null, 2));
  return data;
}

$("saveCfg").onclick = () => {
  saveCfg();
  alert("تم الحفظ");
};

$("registerBtn").onclick = async () => {
  try {
    const data = await api("/v1/register", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ email: $("email").value.trim() }),
    });
    $("regOut").textContent = JSON.stringify(data, null, 2);
    if (data.api_key) {
      $("apiKey").value = data.api_key;
      saveCfg();
    }
  } catch (e) {
    $("regOut").textContent = String(e.message || e);
  }
};

$("createAgent").onclick = async () => {
  try {
    const data = await api("/v1/agents", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({
        name: $("agentName").value.trim(),
        system_prompt: $("agentPrompt").value,
        model: $("agentModel").value.trim(),
      }),
    });
    $("agentsOut").textContent = JSON.stringify(data, null, 2);
    if (data.id) $("runAgentId").value = data.id;
  } catch (e) {
    $("agentsOut").textContent = String(e.message || e);
  }
};

$("listAgents").onclick = async () => {
  try {
    const data = await api("/v1/agents", { headers: headers(false) });
    $("agentsOut").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    $("agentsOut").textContent = String(e.message || e);
  }
};

$("runBtn").onclick = async () => {
  const id = $("runAgentId").value;
  try {
    const data = await api(`/v1/agents/${id}/runs`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ input_text: $("runInput").value }),
    });
    $("runOut").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    $("runOut").textContent = String(e.message || e);
  }
};

loadCfg();
