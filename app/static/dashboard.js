const statusBadge = document.getElementById("statusBadge");
const requestsTotal = document.getElementById("requestsTotal");
const errorsTotal = document.getElementById("errorsTotal");
const rateLimitedTotal = document.getElementById("rateLimitedTotal");
const latencyP95 = document.getElementById("latencyP95");
const latencyAvg = document.getElementById("latencyAvg");
const uptime = document.getElementById("uptime");
const authRequired = document.getElementById("authRequired");
const openapiEnabled = document.getElementById("openapiEnabled");
const rateLimit = document.getElementById("rateLimit");
const rateLimitValue = document.getElementById("rateLimitValue");
const rateLimitBackend = document.getElementById("rateLimitBackend");
const lastUpdated = document.getElementById("lastUpdated");
const auditPreview = document.getElementById("auditPreview");

const dashboardKey = window.__DASHBOARD_KEY__ || "";
const statsUrl = dashboardKey
  ? `/stats?dashboard_key=${encodeURIComponent(dashboardKey)}`
  : "/stats";

function setStatus(ok) {
  statusBadge.textContent = ok ? "Connected" : "Disconnected";
  statusBadge.style.color = ok ? "#22d3ee" : "#f87171";
  statusBadge.style.borderColor = ok ? "rgba(34, 211, 238, 0.4)" : "rgba(248, 113, 113, 0.4)";
}

function fmtSeconds(seconds) {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}m ${remainder}s`;
}

async function refresh() {
  try {
    const response = await fetch(statsUrl, { headers: { "Accept": "application/json" } });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    requestsTotal.textContent = data.requests_total;
    errorsTotal.textContent = data.errors_total;
    rateLimitedTotal.textContent = data.rate_limited_total;
    latencyP95.textContent = `${data.latency_p95_ms} ms`;
    latencyAvg.textContent = `Avg ${data.latency_avg_ms} ms`;
    uptime.textContent = `Uptime ${fmtSeconds(data.uptime_seconds)}`;

    authRequired.textContent = data.auth_required ? "Auth required" : "Auth disabled";
    openapiEnabled.textContent = data.openapi_validation ? "OpenAPI validation" : "Validation off";
    rateLimit.textContent = data.rate_limit.requests > 0 ? "Rate limit on" : "Rate limit off";
    rateLimitValue.textContent = `${data.rate_limit.requests} / ${data.rate_limit.window_seconds}s`;
    rateLimitBackend.textContent = data.rate_limit.backend;

    auditPreview.textContent = `Audit events are streaming via OTLP. Last refresh: ${new Date().toLocaleTimeString()}.`;
    lastUpdated.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
    setStatus(true);
  } catch (error) {
    setStatus(false);
    auditPreview.textContent = `Unable to fetch stats: ${error.message}`;
  }
}

refresh();
setInterval(refresh, 5000);
