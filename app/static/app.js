const state = {
  routes: [],
  gear: [],
  selectedRouteId: null,
};

const els = {
  status: document.querySelector("#status"),
  refresh: document.querySelector("#refresh"),
  routeCount: document.querySelector("#route-count"),
  routes: document.querySelector("#routes"),
  gearCount: document.querySelector("#gear-count"),
  gear: document.querySelector("#gear"),
  selectedRoute: document.querySelector("#selected-route"),
  recommendation: document.querySelector("#recommendation"),
  routeForm: document.querySelector("#route-form"),
  gpxForm: document.querySelector("#gpx-form"),
  gpxFile: document.querySelector("#gpx-file"),
};

function fmtNumber(value, suffix) {
  if (value === null || value === undefined || value === "") return "";
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}${suffix}`;
}

function routeMeta(route) {
  return [
    fmtNumber(route.distance_km, " km"),
    fmtNumber(route.ascent_m, " m ascent"),
    fmtNumber(route.high_point_m, " m high"),
    route.exposure,
  ].filter(Boolean).join(" / ");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      detail = await response.text() || detail;
    }
    throw new Error(detail);
  }
  return response.json();
}

function renderRoutes() {
  els.routeCount.textContent = `${state.routes.length} route${state.routes.length === 1 ? "" : "s"}`;
  if (state.routes.length === 0) {
    els.routes.innerHTML = '<div class="empty-state">No saved routes yet.</div>';
    return;
  }

  els.routes.innerHTML = state.routes.map((route) => `
    <article class="route-card">
      <div>
        <h3>${escapeHtml(route.name)}</h3>
        <p class="meta">${escapeHtml(routeMeta(route))}</p>
      </div>
      <button class="secondary" type="button" data-route-id="${route.id}">Recommend</button>
    </article>
  `).join("");
}

function renderGear() {
  els.gearCount.textContent = `${state.gear.length} item${state.gear.length === 1 ? "" : "s"}`;
  if (state.gear.length === 0) {
    els.gear.innerHTML = '<div class="empty-state">No gear items found in Obsidian.</div>';
    return;
  }

  els.gear.innerHTML = state.gear.map((item) => `
    <article class="gear-card">
      <h3>${escapeHtml(item.name)}</h3>
      <p class="meta">${escapeHtml([item.category, item.type, item.role].filter(Boolean).join(" / "))}</p>
      ${item.capabilities ? `<p class="notes">${escapeHtml(item.capabilities)}</p>` : ""}
    </article>
  `).join("");
}

function renderRecommendation(data) {
  els.recommendation.className = "";
  els.recommendation.innerHTML = `
    <div class="recommendation-summary">
      <strong>${escapeHtml(data.summary || "Loadout ready")}</strong>
      <span class="meta">Confidence: ${escapeHtml(data.confidence)}</span>
    </div>
    <div class="rec-list">
      ${data.items.map((item) => `
        <article class="rec-card">
          <span class="bucket ${escapeHtml(item.bucket)}">${escapeHtml(item.bucket.replace("_", " "))}</span>
          <h3>${escapeHtml(item.gear_item.name)}</h3>
          ${item.reason ? `<p class="notes">${escapeHtml(item.reason)}</p>` : ""}
          ${item.cue ? `<p class="meta">${escapeHtml(item.cue)}</p>` : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function showRecommendationMessage(message, isError = false) {
  els.recommendation.className = isError ? "error-state" : "empty-state";
  els.recommendation.textContent = message;
}

async function loadData() {
  els.status.textContent = "Refreshing...";
  const [health, routes, gear] = await Promise.all([
    api("/health"),
    api("/routes"),
    api("/loadout/gear"),
  ]);

  state.routes = routes;
  state.gear = gear;
  els.status.textContent = `Online, version ${health.version}`;
  renderRoutes();
  renderGear();
}

async function recommend(routeId) {
  state.selectedRouteId = routeId;
  const route = state.routes.find((item) => item.id === routeId);
  els.selectedRoute.textContent = route ? route.name : "Route selected";
  showRecommendationMessage("Building recommendation...");
  try {
    const data = await api(`/loadout/recommend/${routeId}`);
    renderRecommendation(data);
  } catch (error) {
    showRecommendationMessage(error.message, true);
  }
}

els.refresh.addEventListener("click", () => {
  loadData().catch((error) => {
    els.status.textContent = error.message;
  });
});

els.routes.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-route-id]");
  if (button) recommend(Number(button.dataset.routeId));
});

els.routeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = Object.fromEntries([...form.entries()].map(([key, value]) => [key, value === "" ? null : value]));
  try {
    await api("/routes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    event.currentTarget.reset();
    await loadData();
  } catch (error) {
    els.status.textContent = error.message;
  }
});

els.gpxForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!els.gpxFile.files.length) return;
  const form = new FormData();
  form.append("file", els.gpxFile.files[0]);
  try {
    const route = await api("/routes/import-gpx", {
      method: "POST",
      body: form,
    });
    els.gpxFile.value = "";
    await loadData();
    await recommend(route.id);
  } catch (error) {
    els.status.textContent = error.message;
  }
});

loadData().catch((error) => {
  els.status.textContent = error.message;
  els.routes.innerHTML = '<div class="error-state">Routes could not be loaded.</div>';
  els.gear.innerHTML = '<div class="error-state">Gear could not be loaded.</div>';
});
