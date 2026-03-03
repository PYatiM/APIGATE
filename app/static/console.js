const tokenInput = document.getElementById("tokenInput");
const dashboardKeyInput = document.getElementById("dashboardKeyInput");
const accessHint = document.getElementById("accessHint");
const saveAccess = document.getElementById("saveAccess");
const tokenHelper = document.getElementById("tokenHelper");

const healthBadge = document.getElementById("healthBadge");
const requestsValue = document.getElementById("requestsValue");
const errorsValue = document.getElementById("errorsValue");
const rateLimitedValue = document.getElementById("rateLimitedValue");
const latencyValue = document.getElementById("latencyValue");
const statsHint = document.getElementById("statsHint");
const refreshStats = document.getElementById("refreshStats");

const requestForm = document.getElementById("requestForm");
const methodInput = document.getElementById("methodInput");
const pathInput = document.getElementById("pathInput");
const contentTypeInput = document.getElementById("contentTypeInput");
const bodyInput = document.getElementById("bodyInput");
const responseMeta = document.getElementById("responseMeta");
const responseOutput = document.getElementById("responseOutput");
const clearResponse = document.getElementById("clearResponse");

const dashboardLink = document.getElementById("dashboardLink");
const quickCalls = document.getElementById("quickCalls");

const TOKEN_KEY = "gateway_console_token";
const DASHBOARD_KEY = "gateway_console_dashboard_key";

function getSavedToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function getSavedDashboardKey() {
  return localStorage.getItem(DASHBOARD_KEY) || "";
}

function setSavedToken(value) {
  localStorage.setItem(TOKEN_KEY, value);
}

function setSavedDashboardKey(value) {
  localStorage.setItem(DASHBOARD_KEY, value);
}

function normalizePath(path) {
  if (!path) return "/";
  return path.startsWith("/") ? path : `/${path}`;
}

function updateDashboardLink() {
  const key = getSavedDashboardKey();
  dashboardLink.href = key
    ? `/dashboard?dashboard_key=${encodeURIComponent(key)}`
    : "/dashboard";
}

function setHealth(ok, label) {
  healthBadge.textContent = label;
  healthBadge.classList.remove("ok", "bad");
  healthBadge.classList.add(ok ? "ok" : "bad");
}

function fmtLatency(value) {
  if (value === undefined || value === null) {
    return "-";
  }
  return `${value} ms`;
}

function getStatsUrl() {
  const key = getSavedDashboardKey();
  return key ? `/stats?dashboard_key=${encodeURIComponent(key)}` : "/stats";
}

async function refreshHealth() {
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    setHealth(true, `Healthy � ${new Date(data.time).toLocaleTimeString()}`);
  } catch (error) {
    setHealth(false, `Unhealthy � ${error.message}`);
  }
}

async function refreshSnapshot() {
  try {
    const res = await fetch(getStatsUrl(), {
      headers: { Accept: "application/json" },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status} ${text}`);
    }

    const stats = await res.json();
    requestsValue.textContent = `${stats.requests_total}`;
    errorsValue.textContent = `${stats.errors_total}`;
    rateLimitedValue.textContent = `${stats.rate_limited_total}`;
    latencyValue.textContent = fmtLatency(stats.latency_p95_ms);
    statsHint.textContent = `Updated at ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    statsHint.textContent = `Stats unavailable: ${error.message}`;
  }
}

function renderResponseBody(response, bodyText) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      return JSON.stringify(JSON.parse(bodyText), null, 2);
    } catch {
      return bodyText;
    }
  }
  return bodyText;
}

async function sendRequest(event) {
  event.preventDefault();

  const method = methodInput.value;
  let path = normalizePath(pathInput.value.trim());
  const dashboardKey = getSavedDashboardKey();

  if (path === "/dashboard" && dashboardKey && !path.includes("?")) {
    path = `${path}?dashboard_key=${encodeURIComponent(dashboardKey)}`;
  }

  if (path === "/stats" && dashboardKey && !path.includes("?")) {
    path = `${path}?dashboard_key=${encodeURIComponent(dashboardKey)}`;
  }

  const headers = { Accept: "application/json, text/plain;q=0.9, */*;q=0.8" };
  const token = getSavedToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const options = { method, headers };
  const supportsBody = !["GET", "DELETE"].includes(method);
  if (supportsBody) {
    const body = bodyInput.value.trim();
    if (body) {
      headers["Content-Type"] = contentTypeInput.value;
      options.body = body;
    }
  }

  const startedAt = performance.now();

  try {
    const response = await fetch(path, options);
    const elapsed = Math.round(performance.now() - startedAt);
    const raw = await response.text();

    responseMeta.textContent = `${method} ${path} � ${response.status} ${response.statusText} � ${elapsed} ms`;
    responseOutput.textContent = renderResponseBody(response, raw);
  } catch (error) {
    responseMeta.textContent = `${method} ${path} � Request failed`;
    responseOutput.textContent = String(error);
  }
}

function applyQuickCall(event) {
  const button = event.target.closest("button[data-method][data-path]");
  if (!button) return;

  methodInput.value = button.dataset.method;
  pathInput.value = button.dataset.path;

  if (button.dataset.path === "/auth/token") {
    contentTypeInput.value = "application/json";
    bodyInput.value = JSON.stringify({ username: "dev-user" }, null, 2);
  }

  if (button.dataset.path === "/v1/orders") {
    contentTypeInput.value = "application/json";
    bodyInput.value = JSON.stringify(
      {
        customer_id: "customer-1",
        items: [{ sku: "item-001", quantity: 1 }],
        note: "sample order",
      },
      null,
      2,
    );
  }
}

async function requestDevToken() {
  try {
    const response = await fetch("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ username: "dev-user" }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status} ${text}`);
    }

    const data = await response.json();
    const token = data.access_token || "";
    tokenInput.value = token;
    setSavedToken(token);
    accessHint.textContent = "Dev token fetched and saved to local storage.";
  } catch (error) {
    accessHint.textContent = `Unable to fetch dev token: ${error.message}`;
  }
}

function saveAccessData() {
  const token = tokenInput.value.trim();
  const dashboardKey = dashboardKeyInput.value.trim();

  setSavedToken(token);
  setSavedDashboardKey(dashboardKey);
  updateDashboardLink();

  accessHint.textContent = "Access data saved. Use API Runner or quick links now.";
}

function clearResponseView() {
  responseMeta.textContent = "No request sent yet.";
  responseOutput.textContent = "Response will appear here.";
}

function bootstrap() {
  tokenInput.value = getSavedToken();
  dashboardKeyInput.value = getSavedDashboardKey();
  updateDashboardLink();

  saveAccess.addEventListener("click", saveAccessData);
  tokenHelper.addEventListener("click", requestDevToken);
  refreshStats.addEventListener("click", refreshSnapshot);
  requestForm.addEventListener("submit", sendRequest);
  clearResponse.addEventListener("click", clearResponseView);
  quickCalls.addEventListener("click", applyQuickCall);

  refreshHealth();
  refreshSnapshot();
}

bootstrap();
