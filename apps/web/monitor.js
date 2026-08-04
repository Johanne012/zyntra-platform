const $ = (id) => document.getElementById(id);

async function refresh() {
  const base = ($("gw").value || "http://localhost:8080").replace(/\/$/, "");
  const key = $("key").value.trim();
  const headers = {};
  if (key) headers["Authorization"] = `Bearer ${key}`;
  try {
    const r = await fetch(`${base}/v1/stats`, { headers });
    const text = await r.text();
    if (!r.ok) throw new Error(text || r.status);
    const data = JSON.parse(text);
    $("meta").textContent =
      `uptime ${data.uptime_seconds}s · إجمالي الطلبات ${data.total_requests} · تكلفة ~$${data.total_cost_usd}`;
    const body = $("tbody");
    body.innerHTML = "";
    const providers = data.providers || {};
    for (const [name, p] of Object.entries(providers)) {
      const lat = p.latency_ms || {};
      const tr = document.createElement("tr");
      const status = p.in_cooldown
        ? `<span class="bad">cooldown ${p.cooldown_remaining_sec}s</span>`
        : `<span class="ok">جاهز</span>`;
      tr.innerHTML = `
        <td>${name}</td>
        <td>${p.requests}</td>
        <td>${p.success_rate_pct ?? "—"}</td>
        <td>${lat.avg ?? "—"}</td>
        <td>${lat.p95 ?? "—"}</td>
        <td>${p.cost_usd}</td>
        <td>${status}</td>`;
      body.appendChild(tr);
    }
    if (!Object.keys(providers).length) {
      body.innerHTML = "<tr><td colspan='7'>لا بيانات بعد — نفّذ طلب chat أولاً</td></tr>";
    }
  } catch (e) {
    $("meta").textContent = String(e.message || e);
    $("tbody").innerHTML = "";
  }
}

$("refresh").onclick = refresh;
refresh();
setInterval(refresh, 15000);
