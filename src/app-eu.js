/* ============================================================
   BiCRS Atlas — EU NUTS-2 detail map.
   Tile-free thematic map (the NUTS-2 choropleth IS the basemap); works offline from
   file://. Clone of src/app-us.js for Europe: ~290 NUTS-2 regions (SVG renderer), CO2StoP
   storage formations + storage projects/hubs as the region-appropriate storage layers
   (Europe has no Class V/VI wells). Ranked pros/cons reconstructed client-side from
   window.EU_PATHWAY_PROFILE to keep the bundle small.
   ============================================================ */
(function () {
  "use strict";

  const PATH_META = {
    beccs:     { label: "BECCS (heat/electricity)",   color: "#15967f" },
    beccs_pp:  { label: "BECCS — pulp & paper",        color: "#2cc0a4" },
    wte_ccs:   { label: "WtE + CCS",                   color: "#3b7dd8" },
    injection: { label: "Biomass waste injection",     color: "#9b59d0" },
    bio_oil:   { label: "Bio-oil sequestration",       color: "#e08a2b" },
    burial:    { label: "Biomass burial",              color: "#b07d3a" },
    ad_ccs:    { label: "Anaerobic digestion + CCS",   color: "#6b8a9c" },
    biochar:   { label: "Biochar",                     color: "#8aa53f" },
  };

  const FAC_META = {
    pulp_paper: { label: "Pulp & paper",       color: "#e0b020" },
    wte:        { label: "Waste-to-energy",    color: "#c0556b" },
    bioenergy:  { label: "Bioenergy / power",  color: "#e8c64a" },
    biogas_ad:  { label: "Biogas / AD",        color: "#9aa84a" },
    ethanol:    { label: "Ethanol",            color: "#d9772b" },
  };

  const FEEDSTOCK_HINTS = {
    ag: "Recoverable crop residues (straw, stover), Mt oven-dry/yr. JRC ENSPRESO NUTS-2 distribution, scaled to country totals.",
    forestry: "Logging + processing residues, Mt oven-dry/yr (ENSPRESO forest + secondary wood residues).",
    msw_biogenic: "Biogenic fraction of municipal solid waste, Mt/yr — population-allocated. Only the biogenic share counts as CDR.",
    manure: "Animal manure dry-matter, Mt/yr (ENSPRESO biogas feedstock). Wet waste → injection / AD, not combustion.",
    wwtp: "Sewage sludge / biosolids dry solids, Mt/yr (population-allocated).",
  };
  const FEEDSTOCK_LABEL = {
    ag: "Agricultural residues", forestry: "Forestry residues",
    msw_biogenic: "MSW (biogenic)", manure: "Animal manure", wwtp: "Human / WWTP biosolids",
  };

  const GREENS = ["#dbeecf", "#a6d7a0", "#6fbf73", "#3da35a", "#1f7a45", "#0d5530"];
  const NODATA = "#2a3742";

  // ---- Data ----
  const FEED = window.EU_FEEDSTOCKS || [];
  const RECS = window.EU_RECOMMENDATIONS || [];
  const FACIL = window.EU_FACILITIES || [];
  const PROJECTS = window.EU_STORAGE_PROJECTS || [];
  const WWTPS = window.EU_WWTPS || [];
  const PROFILE = window.EU_PATHWAY_PROFILE || {};

  const feedById = index(FEED), recById = index(RECS);
  function index(arr) { const m = {}; arr.forEach(r => { m[r.id] = r; }); return m; }

  const state = { mode: "feedstock", feedstock: "ag", breaks: [], openRegion: null };

  // ---- Combined geometry (NUTS-2) ----
  const combined = { type: "FeatureCollection", features: [] };
  (window.GEO_EU_NUTS.features || []).forEach(f => {
    const p = f.properties;
    combined.features.push({
      type: "Feature", geometry: f.geometry,
      properties: { _id: p.id, _name: `${p.name} — ${p.country}` },
    });
  });

  // ---- Map init ----
  const map = L.map("map", {
    center: [54, 10], zoom: 4, minZoom: 3, maxZoom: 9,
    zoomControl: true, attributionControl: false,
  });
  L.control.attribution({ prefix: false })
    .addAttribution("Regions: Eurostat GISCO · Biomass: JRC ENSPRESO · Storage: CO2StoP · see Methodology")
    .addTo(map);

  // ~290 NUTS-2 polygons -> SVG choropleth is fast and keeps clicks crisp. Storage
  // formations (SVG, non-interactive) below point markers (SVG).
  map.createPane("choroPane"); map.getPane("choroPane").style.zIndex = 410;
  const choroRenderer = L.svg({ pane: "choroPane" });
  map.createPane("formPane"); map.getPane("formPane").style.zIndex = 430;
  const formRenderer = L.svg({ pane: "formPane" });
  map.createPane("ovPane"); map.getPane("ovPane").style.zIndex = 470;
  const ovRenderer = L.svg({ pane: "ovPane" });

  // ---- Choropleth value accessors ----
  function feedValue(rec, key) {
    if (!rec) return null;
    if (key === "msw_biogenic") return (rec.msw || 0) * (rec.biofrac || 0.5);
    const v = rec[key];
    return v != null ? v : null;
  }
  function quantileBreaks(values, nColors) {
    const v = values.filter(x => x != null && x > 0).sort((a, b) => a - b);
    if (!v.length) return [];
    const breaks = [];
    for (let i = 1; i < nColors; i++) {
      const idx = Math.min(v.length - 1, Math.floor((i / nColors) * v.length));
      breaks.push(v[idx]);
    }
    return breaks;
  }
  function colorForValue(val) {
    if (val == null || val <= 0) return null;
    const b = state.breaks;
    for (let i = 0; i < b.length; i++) if (val < b[i]) return GREENS[i];
    return GREENS[GREENS.length - 1];
  }
  function recomputeBreaks() {
    state.breaks = quantileBreaks(
      combined.features.map(f => feedValue(feedById[f.properties._id], state.feedstock)),
      GREENS.length);
  }

  function styleFeature(feature) {
    const id = feature.properties._id;
    let fill = NODATA, opacity = 0.4;
    if (state.mode === "feedstock") {
      const c = colorForValue(feedValue(feedById[id], state.feedstock));
      if (c) { fill = c; opacity = 0.92; }
    } else {
      const rec = recById[id];
      if (rec && !rec.low_supply && PATH_META[rec.recommended]) {
        fill = PATH_META[rec.recommended].color; opacity = 0.9;
      } else if (rec && rec.low_supply) { fill = NODATA; opacity = 0.5; }
    }
    return { fillColor: fill, fillOpacity: opacity, color: "#0e1419", weight: 0.5 };
  }

  const geoLayer = L.geoJSON(combined, {
    style: styleFeature, renderer: choroRenderer,
    onEachFeature: function (feature, layer) {
      layer.on({
        mouseover: e => { highlight(e.target); showHoverTip(e, feature); },
        mousemove: moveHoverTip,
        mouseout:  e => { unhighlight(e.target); hideHoverTip(); },
        click:     () => openDetail(feature.properties._id, feature.properties._name),
      });
    },
  }).addTo(map);

  let hoveredLayer = null;
  function highlight(layer) {
    if (hoveredLayer && hoveredLayer !== layer) geoLayer.resetStyle(hoveredLayer);
    hoveredLayer = layer;
    layer.setStyle({ weight: 1.8, color: "#eafffb" });
    layer.bringToFront();
  }
  function unhighlight(layer) {
    geoLayer.resetStyle(layer);
    if (hoveredLayer === layer) hoveredLayer = null;
  }
  function redrawChoropleth() {
    if (state.mode === "feedstock") recomputeBreaks();
    geoLayer.setStyle(styleFeature);
    renderLegend();
  }

  // ---- Hover tooltip ----
  const hovertip = document.getElementById("hovertip");
  function showHoverTip(e, feature) {
    const id = feature.properties._id, name = feature.properties._name;
    let sub;
    if (state.mode === "feedstock") {
      const v = feedValue(feedById[id], state.feedstock);
      sub = v == null ? "no data" : `<span class="ht-val">${fmt(v)} Mt/yr</span>`;
    } else {
      const rec = recById[id];
      sub = rec ? `<span class="ht-val">${PATH_META[rec.recommended].label}</span>`
        + (rec.low_supply ? ' <span class="lowsup">· low supply</span>' : "") : "no data";
    }
    hovertip.innerHTML = `<div class="ht-name">${name}</div>${sub}`;
    hovertip.classList.remove("hidden");
    moveHoverTip(e);
  }
  function moveHoverTip(e) {
    const p = e.originalEvent;
    hovertip.style.left = p.clientX + "px";
    hovertip.style.top = p.clientY + "px";
  }
  function hideHoverTip() { hovertip.classList.add("hidden"); }

  // ---- Overlays ----
  const facilityLayer = L.layerGroup();
  FACIL.forEach(f => {
    if (f.lat == null || f.lon == null) return;
    const co2 = (f.est_biogenic_co2_mtpa || {}).value || 0.1;
    const r = clamp(3, 3 + Math.sqrt(co2) * 5, 18);
    const meta = FAC_META[f.type] || { label: f.type, color: "#e0b020" };
    L.circleMarker([f.lat, f.lon], {
      radius: r, fillColor: meta.color, color: "#0e1419", weight: 1, fillOpacity: 0.85,
      renderer: ovRenderer,
    }).bindPopup(facilityPopup(f, meta), { maxWidth: 280 }).addTo(facilityLayer);
  });

  const wwtpLayer = L.layerGroup();
  WWTPS.forEach(w => {
    if (w.lat == null || w.lon == null) return;
    L.circleMarker([w.lat, w.lon], {
      radius: 2.5, fillColor: "#5bb0c7", color: "#0e1419", weight: 0.5, fillOpacity: 0.8,
      renderer: ovRenderer,
    }).bindPopup(`<b>${w.name}</b><br>Large WWTP${w.pe ? " · " + fmt(w.pe / 1000) + "k PE" : ""} · ${w.country}
      <div class="pop-src">Source: ${w.source}</div>`, { maxWidth: 260 }).addTo(wwtpLayer);
  });

  const projOpacity = s => s === "operational" ? 0.95 : s === "construction" ? 0.7 : 0.4;
  const projectLayer = L.layerGroup();
  PROJECTS.forEach(p => {
    if (p.lat == null || p.lon == null) return;
    const r = p.capacity_mtpa ? clamp(6, 6 + Math.sqrt(p.capacity_mtpa) * 3, 16) : 7;
    L.circleMarker([p.lat, p.lon], {
      radius: r, fillColor: "#46b3ff", color: "#eafffb", weight: 1.2,
      fillOpacity: projOpacity(p.status), renderer: ovRenderer,
    }).bindPopup(projectPopup(p), { maxWidth: 280 }).addTo(projectLayer);
  });

  // Storage formations: broad visual context, non-interactive so clicks fall through to the
  // region beneath. The detail panel already names the formation a region sits in/near.
  const formationLayer = L.geoJSON(window.GEO_EU_STORAGE, {
    renderer: formRenderer,
    interactive: false,
    style: { fillColor: "#7aa6ff", color: "#6f93c9", weight: 0.8, fillOpacity: 0.16, opacity: 0.45 },
  });

  function facilityPopup(f, meta) {
    const co2 = f.est_biogenic_co2_mtpa || {};
    return `<b>${f.name}</b><br>${meta.label}${f.capacity_note ? " · " + f.capacity_note : ""}<br>
      Biogenic CO₂: <b>${co2.value != null ? fmt(co2.value) + " Mtpa" : "n/a"}</b><br>
      Retrofit potential: <b>${cap1(f.retrofit_score)}</b> · ${f.country}
      ${f.operator ? "<br>Operator: " + f.operator : ""}
      <div class="pop-src">Source: ${f.source || "—"}</div>`;
  }
  function projectPopup(p) {
    return `<b>${p.name}</b><br>CO₂ storage project · ${cap1(p.status)}<br>
      ${p.storage_type ? "Type: " + p.storage_type + "<br>" : ""}
      ${p.capacity_mtpa ? "Capacity: <b>" + fmt(p.capacity_mtpa) + " Mtpa</b><br>" : ""}${p.country || ""}
      <div class="pop-src">Source: ${p.source || "—"}</div>`;
  }

  // ---- Detail panel ----
  const detail = document.getElementById("detail");
  const detailBody = document.getElementById("detail-body");

  function openDetail(id, name) {
    state.openRegion = { id: id, name: name };
    const rec = recById[id], feed = feedById[id];
    let html = `<div class="d-region">NUTS-2 region</div><div class="d-name">${name}</div>`;
    if (!rec && !feed) { html += `<p class="rationale">No data for this region.</p>`;
      detailBody.innerHTML = html; detail.classList.remove("hidden"); return; }

    if (state.mode === "feedstock") {
      if (feed) html += feedstockBarChart(feed) + feedSection(feed);
    } else {
      if (rec) html += recCard(rec) + rankedList(rec);
    }
    detailBody.innerHTML = html;
    detail.classList.remove("hidden");
  }

  function feedstockBarChart(feed) {
    const items = [
      ["Agricultural residues", (feed.ag || 0) * 1.47, "#6fbf73"],
      ["Forestry residues", (feed.forestry || 0) * 1.47, "#2f8f57"],
      ["MSW (biogenic)", (feed.msw || 0) * (feed.biofrac || 0.5) * 1.0, "#c0556b"],
      ["Animal manure", (feed.manure || 0) * 1.47, "#b07d3a"],
      ["Human / WWTP", (feed.wwtp || 0) * 1.47, "#9b59d0"],
    ].filter(x => x[1] > 0).sort((a, b) => b[1] - a[1]);
    if (!items.length) return `<p class="rationale">Negligible recoverable biomass.</p>`;
    const max = items[0][1], total = items.reduce((s, x) => s + x[1], 0);
    let html = `<div class="chart-card">
      <div class="chart-title">Biogenic CO₂ potential by feedstock</div>
      <div class="chart-sub">Carbon embodied in each waste stream · Mt CO₂/yr · actual CDR depends on pathway efficiency</div>`;
    items.forEach(([label, val, color]) => {
      const pct = Math.max(2, (val / max) * 100);
      html += `<div class="bar-row"><div class="bar-label">${label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
        <div class="bar-val">${fmt(val)}</div></div>`;
    });
    html += `<div class="chart-total">Total embodied biogenic CO₂: <b>${fmt(total)} Mt CO₂/yr</b></div></div>`;
    return html;
  }

  function feedSection(feed) {
    const rows = [
      ["Agricultural residues", feed.ag, "Mt odt/yr"],
      ["Forestry residues", feed.forestry, "Mt odt/yr"],
      ["MSW (total)", feed.msw, "Mt/yr"],
      ["Animal manure", feed.manure, "Mt odt/yr"],
      ["Human / WWTP", feed.wwtp, "Mt odt/yr"],
    ];
    let html = `<div class="d-sec-title">Feedstock supply</div><table class="feed">`;
    rows.forEach(([lab, v, unit]) => {
      if (v == null || v <= 0) return;
      html += `<tr><td class="lab">${lab}<div class="unc">${unit}</div></td>
        <td class="val">${fmt(v)}</td></tr>`;
    });
    html += `<tr><td class="lab">MSW biogenic fraction</td><td class="val">${Math.round((feed.biofrac || 0.5) * 100)}%</td></tr></table>`;
    html += `<div class="chips">
      <span class="chip">Dominant: ${labelFeed(feed.dominant_feedstock)}</span>
      <span class="chip">Nutrients: ${cap1(feed.nutrient_status)}</span></div>
      <p class="rationale" style="margin-top:10px">NUTS-2 tonnages disaggregate the country total
      (global tool) using JRC ENSPRESO regional biomass shares and population. See methodology.</p>`;
    return html;
  }

  function recCard(rec) {
    const meta = PATH_META[rec.recommended] || { label: rec.recommended_label, color: "#888" };
    const eff = rec.cdr_efficiency != null ? Math.round(rec.cdr_efficiency * 100) + "%" : "—";
    const cdr = rec.cdr_potential_mtpa != null ? fmt(rec.cdr_potential_mtpa) + " Mtpa" : "—";
    const sd = rec.storage_detail || {};
    const storage = `${cap1(rec.storage_access)}${rec.nearest_storage_km != null ? " · ~" + fmt(rec.nearest_storage_km) + " km" : ""}`;
    let html = `<div class="rec-card">
      <div class="rec-top"><span class="rec-pill" style="background:${meta.color}">RECOMMENDED</span>
        <h3>${rec.recommended_label}</h3></div>`;
    if (rec.low_supply) html += `<div class="caveat lowsup">Negligible recoverable biomass — recommendation indicative only.</div>`;
    html += `<div class="rec-meta">
        <div><div class="k">CDR efficiency</div><div class="v">${eff}</div></div>
        <div><div class="k">KPI score</div><div class="v">${rec.kpi_score}</div></div>
        <div><div class="k">Cost band</div><div class="v" style="font-size:12px">${rec.cost_band || "—"}</div></div>
        <div><div class="k">CDR potential</div><div class="v">${cdr}</div></div>
        <div><div class="k">Storage access</div><div class="v" style="font-size:12px">${storage}</div></div>
        <div><div class="k">Retrofit anchor</div><div class="v" style="font-size:11px">${rec.anchor_facility || "none mapped"}</div></div>
      </div>
      <p class="rationale">${rec.rationale || ""}</p>
      <div class="runner">Runner-up: <b>${rec.runner_up_label}</b></div>`;
    (rec.caveats || []).forEach(c => { html += `<div class="caveat">${c}</div>`; });
    (rec.flags || []).forEach(f => { html += `<div class="flag">${f}</div>`; });
    html += `</div>`;

    // Region-specific storage / density metrics
    html += `<div class="d-metrics">
      <div><div class="k">Storage formation</div><div class="v">${sd.in_formation ? "On-site: " + sd.in_formation : (sd.nearest_formation ? sd.nearest_formation + " (~" + sd.nearest_formation_km + " km)" : "—")}</div></div>
      <div><div class="k">Nearest project</div><div class="v">${sd.nearest_project ? sd.nearest_project + (sd.nearest_project_km != null ? " (~" + sd.nearest_project_km + " km)" : "") : "—"}</div></div>
      <div><div class="k">Feedstock density</div><div class="v">${cap1(rec.feedstock_density)} · ${fmt(rec.residue_density_tco2_km2)} tCO₂/km²</div></div>
      <div><div class="k">Dominant feedstock</div><div class="v">${labelFeed(rec.dominant_feedstock)}</div></div>
    </div>`;
    return html;
  }

  // Reconstruct ranked pros/cons client-side (mirrors engine_core.region_pros_cons).
  function regionProsCons(rec, key) {
    const prof = PROFILE[key];
    let pros = prof.pros.slice(), cons = prof.cons.slice();
    const sa = rec.storage_access, dens = rec.feedstock_density, nut = rec.nutrient_status;
    const central = key === "beccs" || key === "beccs_pp" || key === "wte_ccs";
    const distributed = key === "bio_oil" || key === "biochar" || key === "burial";
    if (prof.needs_storage) {
      if (sa === "good") pros.push("Proximate geologic storage here" + (rec.nearest_storage_km != null ? ` (~${rec.nearest_storage_km} km)` : ""));
      else if (sa === "moderate") cons.push("Geologic storage only moderately accessible — transport adds cost");
      else cons.push("Geologic storage is poor/absent here — a major constraint");
    }
    if (dens === "diffuse") {
      if (central) cons.push("Local biomass is diffuse — hauling to a central plant is costly");
      else if (distributed) pros.push("Suits the region's diffuse, distributed biomass");
    } else if (dens === "concentrated" && central) pros.push("Biomass is concentrated — supports a central facility");
    if (nut === "excess") {
      if (key === "bio_oil" || key === "biochar" || key === "ad_ccs") {
        pros = pros.filter(x => !/nutrient/i.test(x));
        cons.push("Returns nutrients to soils already in surplus here");
      } else if (key === "burial" || key === "injection") {
        pros.push("Removes carbon and nutrients from an over-fertilized landscape");
      }
    }
    if (key === "beccs_pp") {
      if (rec.has_pp_be && rec.anchor_facility) pros.push("Existing mill to retrofit: " + rec.anchor_facility);
      else cons.push("No existing pulp/bioenergy mill in-region to retrofit");
    }
    return [pros.slice(0, 4), cons.slice(0, 4)];
  }

  function rankedList(rec) {
    const rk = rec.ranked_keys || [];
    if (!rk.length) return "";
    const badgeClass = b => "rk-" + b.toLowerCase().replace(/[^a-z]+/g, "");
    let html = `<div class="d-sec-title">CDR options ranked — best to worst here</div>`;
    rk.forEach((item, i) => {
      const key = item.k, prof = PROFILE[key] || {};
      const color = (PATH_META[key] || {}).color || "#888";
      const [pros, cons] = regionProsCons(rec, key);
      html += `<div class="rank-item">
        <div class="rank-head">
          <span class="rank-num" style="background:${color}">${i + 1}</span>
          <span class="rank-name">${prof.label || key}</span>
          <span class="rank-badge ${badgeClass(item.b)}">${item.b}</span>
        </div>
        <div class="rank-meta">${Math.round((prof.eff || 0) * 100)}% CDR efficiency · ${prof.cost || ""}</div>
        <div class="rank-pc">
          <ul class="pc-pros">${pros.map(x => `<li>${x}</li>`).join("")}</ul>
          <ul class="pc-cons">${cons.map(x => `<li>${x}</li>`).join("")}</ul>
        </div></div>`;
    });
    return html;
  }

  function labelFeed(d) {
    return ({ ag_dry: "Dry ag residues", forestry_woody: "Woody forestry", msw: "Municipal waste",
      manure_wet: "Wet manure", mixed: "Mixed" })[d] || d || "—";
  }

  // Re-render the open detail panel after a mode/feedstock change (keep it in sync).
  function refreshDetail() {
    if (state.openRegion && !detail.classList.contains("hidden")) {
      openDetail(state.openRegion.id, state.openRegion.name);
    }
  }
  document.getElementById("detail-close").onclick = () => {
    detail.classList.add("hidden");
    state.openRegion = null;
  };

  // ---- Legend ----
  const legend = document.getElementById("legend");
  const legendTitle = document.getElementById("legend-title");
  function renderLegend() {
    if (state.mode === "feedstock") {
      legendTitle.textContent = FEEDSTOCK_LABEL[state.feedstock] + " (Mt/yr)";
      const b = state.breaks, ranges = [];
      let prev = 0;
      for (let i = 0; i < GREENS.length; i++) { const hi = i < b.length ? b[i] : null; ranges.push([prev, hi]); prev = hi; }
      let html = "";
      ranges.forEach((rg, i) => {
        const lab = rg[1] == null ? `≥ ${fmt(rg[0])}` : `${fmt(rg[0])} – ${fmt(rg[1])}`;
        html += `<div class="legend-row"><span class="box" style="background:${GREENS[i]}"></span>${lab}</div>`;
      });
      html += `<div class="legend-row"><span class="box" style="background:${NODATA}"></span>No / negligible data</div>`;
      html += `<div class="legend-note">Quantile classes across all NUTS-2 regions.</div>`;
      legend.innerHTML = html;
    } else {
      legendTitle.textContent = "Recommended pathway";
      const counts = {};
      RECS.forEach(r => { if (!r.low_supply) counts[r.recommended] = (counts[r.recommended] || 0) + 1; });
      let html = "";
      Object.keys(PATH_META).forEach(k => {
        if (!counts[k]) return;
        html += `<div class="legend-row"><span class="box" style="background:${PATH_META[k].color}"></span>
          ${PATH_META[k].label} <span style="color:var(--ink-3);margin-left:auto;font-family:var(--mono);font-size:10px">${counts[k]}</span></div>`;
      });
      html += `<div class="legend-row"><span class="box" style="background:${NODATA}"></span>Low / negligible supply</div>`;
      html += `<div class="legend-note">Best use of biomass per Frontier's KPI ranking, computed per NUTS-2 region (storage distance + feedstock density). Click a region for rationale.</div>`;
      legend.innerHTML = html;
    }
  }

  // ---- Controls ----
  const feedControls = document.getElementById("feedstock-controls");
  const feedSelect = document.getElementById("feedstock-select");
  const feedHint = document.getElementById("feedstock-hint");

  document.querySelectorAll(".seg-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".seg-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.mode = btn.dataset.mode;
      feedControls.style.display = state.mode === "feedstock" ? "" : "none";
      redrawChoropleth();
      refreshDetail();
    };
  });
  feedSelect.onchange = () => {
    state.feedstock = feedSelect.value;
    feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock] || "";
    redrawChoropleth();
    refreshDetail();
  };

  document.getElementById("ov-facilities").onchange = e => toggleLayer(facilityLayer, e.target.checked);
  document.getElementById("ov-wwtps").onchange = e => toggleLayer(wwtpLayer, e.target.checked);
  document.getElementById("ov-projects").onchange = e => toggleLayer(projectLayer, e.target.checked);
  document.getElementById("ov-formations").onchange = e => toggleLayer(formationLayer, e.target.checked);
  function toggleLayer(layer, on) { on ? layer.addTo(map) : map.removeLayer(layer); }

  // ---- Methodology modal ----
  const methodModal = document.getElementById("method-modal");
  document.getElementById("open-method").onclick = () => methodModal.classList.remove("hidden");
  document.getElementById("method-close").onclick = () => methodModal.classList.add("hidden");
  methodModal.onclick = e => { if (e.target === methodModal) methodModal.classList.add("hidden"); };
  document.getElementById("method-body").innerHTML = methodologyHTML();

  // ---- Stat: total NUTS-2 CDR potential (Mt) ----
  const totalCdr = RECS.reduce((s, r) => s + (r.cdr_potential_mtpa || 0), 0);
  document.getElementById("stat-cdr").textContent = fmt(totalCdr);

  // ---- Helpers ----
  function fmt(v) {
    if (v == null) return "—";
    if (v >= 1000) return (v / 1000).toFixed(1) + "k";
    if (v >= 100) return v.toFixed(0);
    if (v >= 1) return v.toFixed(1);
    if (v >= 0.1) return v.toFixed(2);
    return v.toFixed(3);
  }
  function cap1(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : "—"; }
  function clamp(lo, v, hi) { return Math.max(lo, Math.min(hi, v)); }

  function methodologyHTML() {
    return `
      <h2>Methodology &amp; sources — EU NUTS-2 detail</h2>
      <p>This map resolves the BiCRS Atlas to European NUTS-2 regions (EU-27 + UK + Norway):
      biomass feedstock supply, the geologic storage resource as actual formation shapes, biogenic
      point sources, CO₂ storage projects, and large WWTPs, with a per-region best-use recommendation.
      It uses the same decision framework as the global Atlas (shared engine), with inputs computed at
      NUTS-2 granularity.</p>

      <h3>Regional feedstock supply</h3>
      <p>"ENSPRESO NUTS-2 distribution, scaled to country totals." Each feedstock's within-country
      distribution comes from the JRC <b>ENSPRESO</b> NUTS-2 biomass database (agricultural residues,
      forest + secondary-wood residues, manure/biogas); MSW &amp; biosolids are allocated by NUTS-2
      population (Eurostat). Each region is then scaled so a country's regions sum to that country's
      total already in the global tool. Purpose-grown energy/biofuel crops are excluded. ENSPRESO is
      NUTS v2013; regions recoded since (mainly France) are remapped via ENSPRESO's own conversion
      table, with a small number falling back to population allocation.</p>

      <h3>CO₂ storage</h3>
      <p>Storage formations are drawn as <b>actual polygons</b> from the EU <b>CO2StoP</b> database
      (JRC) — assessed saline aquifers and hydrocarbon-field storage units. A region whose centroid
      falls inside a formation has storage on-site; otherwise distance is measured to the nearest
      formation boundary and the nearest storage project. Storage projects/hubs (the operational and
      planned named projects — Northern Lights, Porthos, Aramis, Greensand, Acorn, Ravenna, Endurance,
      HyNet, Sleipner, Snøhvit, …) are the European analog of the US wells layer. Much EU storage is
      offshore (North Sea), so inland regions legitimately read "poor".</p>

      <h3>Biogenic point sources &amp; WWTPs</h3>
      <p>Curated European biogenic-CO₂ point sources (pulp &amp; paper, waste-to-energy, bioenergy,
      biogas/AD), with biogenic-CO₂ estimates from capacity/throughput (EU ETS zero-rates sustainable
      biomass, so there is no clean reported biogenic column — these are estimates, the weakest layer).
      Large WWTPs (≥150,000 population-equivalent) from the EEA/EMODnet UWWTD (Waterbase) dataset.</p>

      <h3>Region recommendation engine</h3>
      <p>The shared rule set (CDR efficiency › emissions-avoiding co-product › co-benefits) with NUTS-2
      inputs: (1) <b>storage access</b> — inside-a-formation = on-site, else great-circle to the nearest
      formation boundary and nearest storage project, graded good &lt; 150 km, moderate &lt; 400 km;
      (2) <b>feedstock density</b> — residue density (tCO₂/km²) from ENSPRESO biomass / region area. In
      mature anaerobic-digestion countries (most of Europe), wet manure routes to AD+CCS, retrofitting
      existing biogas plants, rather than injection.</p>

      <h3>Caveats</h3>
      <p>Regional tonnages are disaggregated estimates, not measured inventories. CO2StoP outlines are
      the assessed storage resource (not a permit to inject). Biogenic point-source CO₂ is estimated,
      not reported. Distances are great-circle screening distances, not routed. This tool informs
      strategy; it does not substitute for project-level diligence.</p>`;
  }

  // ---- Deep-link hash: #mode=recommendation&feed=ag&ov=facilities,projects,formations&region=EU-DE21 ----
  function applyHash() {
    const h = (location.hash || "").replace(/^#/, "");
    if (!h) return;
    const p = {};
    h.split("&").forEach(kv => { const [k, v] = kv.split("="); if (k) p[k] = decodeURIComponent(v || ""); });
    if (p.mode === "recommendation" || p.mode === "feedstock") {
      const btn = document.querySelector(`.seg-btn[data-mode="${p.mode}"]`); if (btn) btn.click();
    }
    if (p.feed && FEEDSTOCK_LABEL[p.feed]) { feedSelect.value = p.feed; feedSelect.onchange(); }
    if (p.ov) p.ov.split(",").forEach(o => {
      const m = { facilities: "ov-facilities", wwtps: "ov-wwtps", projects: "ov-projects",
        formations: "ov-formations" };
      const el = document.getElementById(m[o]); if (el) { el.checked = true; el.onchange({ target: el }); }
    });
    if (p.region) { const r = recById[p.region] || feedById[p.region];
      if (r) openDetail(p.region, `${r.name} — ${r.country}`); }
  }

  // ---- Initial render ----
  feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock];
  redrawChoropleth();
  map.setView([54, 10], 4);
  applyHash();
})();
