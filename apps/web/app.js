const GATEWAY = (window.ZYNTRA_GATEWAY_URL || "http://localhost:8080");
const AGENTS = (window.ZYNTRA_AGENTS_URL || "http://localhost:8081");

async function ping(url) {
  try {
    const r = await fetch(url, { method: "GET" });
    if (!r.ok) return `خطأ ${r.status}`;
    const j = await r.json();
    return j.status === "ok" ? "✅ يعمل" : JSON.stringify(j);
  } catch {
    return "⚠️ غير متصل";
  }
}

async function refresh() {
  const g = document.querySelector('[data-svc="gateway"]');
  const a = document.querySelector('[data-svc="agents"]');
  if (g) g.textContent = "…";
  if (a) a.textContent = "…";
  if (g) g.textContent = await ping(`${GATEWAY}/health`);
  if (a) a.textContent = await ping(`${AGENTS}/health`);
}

document.getElementById("refresh")?.addEventListener("click", refresh);
refresh();
