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
  gpxLabel: document.querySelector("#gpx-label"),
  gearSearch: document.querySelector("#gear-search"),
  gearCategory: document.querySelector("#gear-category"),
  loadoutRouteName: document.querySelector("#loadout-route-name"),
  loadoutRouteMeta: document.querySelector("#loadout-route-meta"),
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
    els.routes.innerHTML = '<div class="empty-state">No saved routes yet. Import a GPX or add a route to get started.</div>';
    return;
  }

  els.routes.innerHTML = state.routes.map((route) => `
    <article class="route-item ${route.id === state.selectedRouteId ? "selected" : ""}">
      <div>
        <h3>${escapeHtml(route.name)}</h3>
        <p class="meta">${escapeHtml(routeMeta(route).replaceAll(" / ", " · "))}</p>
      </div>
      <button type="button" data-route-id="${route.id}">${route.id === state.selectedRouteId ? "Selected" : "Build loadout"}</button>
    </article>
  `).join("");
}

function renderGear() {
  const query = els.gearSearch.value.trim().toLowerCase();
  const category = els.gearCategory.value;
  const visibleGear = state.gear.filter((item) => {
    const haystack = [item.name, item.category, item.type, item.role, item.capabilities].join(" ").toLowerCase();
    return (!query || haystack.includes(query)) && (!category || item.category === category);
  });

  els.gearCount.textContent = `${state.gear.length} item${state.gear.length === 1 ? "" : "s"}`;
  if (state.gear.length === 0) {
    els.gear.innerHTML = '<div class="empty-state">No gear items found in Obsidian.</div>';
    return;
  }
  if (visibleGear.length === 0) {
    els.gear.innerHTML = '<div class="empty-state">No gear matches this filter.</div>';
    return;
  }

  els.gear.innerHTML = visibleGear.map((item) => `
    <article class="gear-card">
      <span class="category">${escapeHtml(item.category || item.type || "Gear")}</span>
      <h3>${escapeHtml(item.name)}</h3>
      <p class="meta">${escapeHtml([item.type, item.role].filter(Boolean).join(" · "))}</p>
      ${item.capabilities ? `<p class="notes">${escapeHtml(item.capabilities)}</p>` : ""}
    </article>
  `).join("");
}

function renderGearCategories() {
  const selected = els.gearCategory.value;
  const categories = [...new Set(state.gear.map((item) => item.category).filter(Boolean))].sort();
  els.gearCategory.innerHTML = '<option value="">All categories</option>' + categories.map((category) => (
    `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`
  )).join("");
  els.gearCategory.value = categories.includes(selected) ? selected : "";
}

function renderRecommendation(data) {
  els.recommendation.className = "recommendation-result";
  els.recommendation.innerHTML = `
    <div class="recommendation-summary">
      <span class="recommendation-label">Recommendation</span>
      <h2>${escapeHtml(data.summary || "Your loadout is ready.")}</h2>
      <p class="meta">Review the reasons and conditional cues before heading out.</p>
      <span class="confidence">${escapeHtml(data.confidence)} confidence</span>
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
  els.recommendation.className = isError ? "error-state" : "recommendation-empty";
  els.recommendation.textContent = message;
}

function setServiceStatus(message, stateName = "") {
  els.status.textContent = message;
  els.status.parentElement.classList.toggle("online", stateName === "online");
  els.status.parentElement.classList.toggle("error", stateName === "error");
}

function showScreen(name) {
  document.querySelectorAll(".screen").forEach((screen) => {
    const active = screen.id === `screen-${name}`;
    screen.classList.toggle("active", active);
    screen.hidden = !active;
  });
  document.querySelectorAll("[data-go]").forEach((control) => {
    const active = control.dataset.go === name && (control.classList.contains("nav-item") || control.closest(".mobile-nav"));
    control.classList.toggle("active", active);
    if (control.classList.contains("nav-item")) {
      if (active) control.setAttribute("aria-current", "page");
      else control.removeAttribute("aria-current");
    }
  });
  window.location.hash = name;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadData() {
  setServiceStatus("Refreshing…");
  const [health, routes, gear] = await Promise.all([
    api("/health"),
    api("/routes"),
    api("/loadout/gear"),
  ]);

  state.routes = routes;
  state.gear = gear;
  setServiceStatus(`Online · v${health.version}`, "online");
  renderGearCategories();
  renderRoutes();
  renderGear();
}

async function recommend(routeId) {
  state.selectedRouteId = routeId;
  const route = state.routes.find((item) => item.id === routeId);
  els.selectedRoute.textContent = route ? route.name : "Route selected";
  els.loadoutRouteName.textContent = route ? route.name : "Route selected";
  els.loadoutRouteMeta.textContent = route ? routeMeta(route).replaceAll(" / ", " · ") : "";
  renderRoutes();
  showScreen("loadout");
  showRecommendationMessage("Building your recommendation…");
  try {
    const data = await api(`/loadout/recommend/${routeId}`);
    renderRecommendation(data);
  } catch (error) {
    showRecommendationMessage(error.message, true);
  }
}

els.refresh.addEventListener("click", () => {
  loadData().catch((error) => {
    setServiceStatus(error.message, "error");
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
    setServiceStatus(error.message, "error");
  }
});

els.gpxFile.addEventListener("change", () => {
  els.gpxLabel.textContent = els.gpxFile.files[0]?.name || "Choose a route file";
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
    els.gpxLabel.textContent = "Choose a route file";
    await loadData();
    await recommend(route.id);
  } catch (error) {
    setServiceStatus(error.message, "error");
  }
});

document.addEventListener("click", (event) => {
  const control = event.target.closest("[data-go]");
  if (control) {
    event.preventDefault();
    showScreen(control.dataset.go);
  }
});

els.gearSearch.addEventListener("input", renderGear);
els.gearCategory.addEventListener("change", renderGear);

loadData().catch((error) => {
  setServiceStatus(error.message, "error");
  els.routes.innerHTML = '<div class="error-state">Routes could not be loaded.</div>';
  els.gear.innerHTML = '<div class="error-state">Gear could not be loaded.</div>';
});

showScreen(window.location.hash === "#loadout" ? "loadout" : "plan");
