/* ============================================================
   BiCRS Atlas — application logic
   Tile-free thematic map (the choropleth IS the basemap), so the
   page works offline by double-clicking index.html (no server).
   ============================================================ */
(function () {
  "use strict";

  // ---- Pathway metadata (keys MUST match build_recommendations.py) ----
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
    pulp_paper: { label: "Pulp & paper", color: "#e0b020" },
    ethanol:    { label: "Ethanol",      color: "#d9772b" },
    wte:        { label: "Waste-to-energy", color: "#c0556b" },
    bioenergy:  { label: "Bioenergy / power", color: "#e8c64a" },
    biogas_ad:  { label: "Biogas / AD",  color: "#9aa84a" },
  };

  const STORAGE_TYPE = {
    saline:      "Saline aquifer",
    depleted_og: "Depleted oil & gas",
    basalt:      "Basalt (mineralization)",
    eor:         "Enhanced oil recovery",
  };

  const FEEDSTOCK_HINTS = {
    ag_residues_odt_mt: "Recoverable crop residues (straw, stover, bagasse), Mt oven-dry/yr. ~40% sustainable removal cap applied.",
    forestry_residues_odt_mt: "Logging + processing residues, Mt oven-dry/yr.",
    msw_biogenic_mt: "Biogenic fraction of municipal solid waste (total × biogenic %), Mt/yr — only the biogenic share counts as CDR.",
    animal_manure_odt_mt: "Animal manure available as feedstock, Mt dry-matter/yr. Wet waste → injection / AD, not combustion.",
    human_wwtp_odt_mt: "Sewage sludge / biosolids dry solids, Mt/yr.",
  };

  const FEEDSTOCK_LABEL = {
    ag_residues_odt_mt: "Agricultural residues",
    forestry_residues_odt_mt: "Forestry residues",
    msw_biogenic_mt: "MSW (biogenic)",
    animal_manure_odt_mt: "Animal manure",
    human_wwtp_odt_mt: "Human / WWTP biosolids",
  };

  // Sequential green ramp for feedstock choropleth (light -> dark)
  const GREENS = ["#dbeecf", "#a6d7a0", "#6fbf73", "#3da35a", "#1f7a45", "#0d5530"];

  // ---- Data ----
  const FEED = window.DATA_FEEDSTOCKS || [];
  const STORAGE = window.DATA_STORAGE || [];
  const FACIL = window.DATA_FACILITIES || [];
  const RECS = window.DATA_RECOMMENDATIONS || [];

  const feedById = index(FEED);
  const recById = index(RECS);
  function index(arr) { const m = {}; arr.forEach(r => { m[r.id] = r; }); return m; }

  // ---- State ----
  const state = {
    mode: "feedstock",
    feedstock: "ag_residues_odt_mt",
    breaks: [],
  };

  // ---- Build combined geometry: countries (minus USA) + US states ----
  const combined = { type: "FeatureCollection", features: [] };
  (window.GEO_COUNTRIES.features || []).forEach(f => {
    if (f.properties.iso_a3 === "USA") return; // draw US at state resolution
    combined.features.push(tag(f, f.properties.iso_a3, f.properties.name));
  });
  (window.GEO_US_STATES.features || []).forEach(f => {
    combined.features.push(tag(f, f.properties.id, f.properties.name));
  });
  function tag(f, id, name) {
    return { type: "Feature", geometry: f.geometry, properties: { _id: id, _name: name } };
  }

  // ---- Map init (no tile layer) ----
  const map = L.map("map", {
    center: [25, 12],
    zoom: 2,
    minZoom: 2,
    maxZoom: 7,
    worldCopyJump: true,
    zoomControl: true,
    attributionControl: false,
  });
  L.control.attribution({ prefix: false })
    .addAttribution("Geometry: Natural Earth · Data: see Methodology")
    .addTo(map);

  // ---- Choropleth value accessors ----
  function feedValue(rec, key) {
    if (!rec) return null;
    if (key === "msw_biogenic_mt") {
      const t = rec.msw_total_mt && rec.msw_total_mt.value;
      const fr = rec.msw_biogenic_frac && rec.msw_biogenic_frac.value;
      if (t == null || fr == null) return null;
      return t * fr;
    }
    const o = rec[key];
    return o && o.value != null ? o.value : null;
  }

  function quantileBreaks(values, nColors) {
    const v = values.filter(x => x != null && x > 0).sort((a, b) => a - b);
    if (!v.length) return [];
    const breaks = [];
    for (let i = 1; i < nColors; i++) {
      const q = i / nColors;
      const idx = Math.min(v.length - 1, Math.floor(q * v.length));
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
    const vals = combined.features.map(f => feedValue(feedById[f.properties._id], state.feedstock));
    state.breaks = quantileBreaks(vals, GREENS.length);
  }

  // ---- Style function ----
  function styleFeature(feature) {
    const id = feature.properties._id;
    let fill = "#2a3742";      // land, no data
    let opacity = 0.35;
    if (state.mode === "feedstock") {
      const c = colorForValue(feedValue(feedById[id], state.feedstock));
      if (c) { fill = c; opacity = 0.92; }
    } else {
      const rec = recById[id];
      if (rec && PATH_META[rec.recommended]) { fill = PATH_META[rec.recommended].color; opacity = 0.9; }
    }
    return { fillColor: fill, fillOpacity: opacity, color: "#0e1419", weight: 0.6 };
  }

  // ---- Choropleth layer ----
  let geoLayer = L.geoJSON(combined, {
    style: styleFeature,
    onEachFeature: function (feature, layer) {
      layer.on({
        mouseover: function (e) { highlight(e.target); showHoverTip(e, feature); },
        mousemove: function (e) { moveHoverTip(e); },
        mouseout:  function (e) { unhighlight(e.target); hideHoverTip(); },
        click:     function ()  { openDetail(feature.properties._id, feature.properties._name); },
      });
    },
  }).addTo(map);

  function highlight(layer) {
    layer.setStyle({ weight: 1.8, color: "#eafffb" });
    layer.bringToFront();
  }
  function unhighlight(layer) { geoLayer.resetStyle(layer); }

  function redrawChoropleth() {
    if (state.mode === "feedstock") recomputeBreaks();
    geoLayer.setStyle(styleFeature);
    renderLegend();
  }

  // ---- Hover tooltip ----
  const hovertip = document.getElementById("hovertip");
  function showHoverTip(e, feature) {
    const id = feature.properties._id, name = feature.properties._name;
    let sub = "";
    if (state.mode === "feedstock") {
      const v = feedValue(feedById[id], state.feedstock);
      sub = v == null ? "no data" : `<span class="ht-val">${fmt(v)} Mt/yr</span>`;
    } else {
      const rec = recById[id];
      sub = rec ? `<span class="ht-val">${PATH_META[rec.recommended].label}</span>` : "no data";
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

  // ---- Overlays: facilities, storage sites, basins ----
  const facilityLayer = L.layerGroup();
  FACIL.forEach(f => {
    if (f.lat == null || f.lon == null) return;
    const co2 = f.est_biogenic_co2_mtpa && f.est_biogenic_co2_mtpa.value;
    const r = clamp(4, 4 + Math.sqrt(co2 || 0.3) * 3.2, 20);
    const meta = FAC_META[f.type] || { label: f.type, color: "#e0b020" };
    L.circleMarker([f.lat, f.lon], {
      radius: r, fillColor: meta.color, color: "#0e1419", weight: 1, fillOpacity: 0.85,
    }).bindPopup(facilityPopup(f, meta), { maxWidth: 280 }).addTo(facilityLayer);
  });

  const siteLayer = L.layerGroup();
  STORAGE.filter(s => s.kind === "site").forEach(s => {
    if (s.lat == null || s.lon == null) return;
    const cap = s.capacity_mtpa || 0.5;
    const r = clamp(4, 4 + Math.sqrt(cap) * 4, 18);
    const op = s.status === "operational" ? 0.9 : s.status === "construction" ? 0.6 : 0.35;
    L.circleMarker([s.lat, s.lon], {
      radius: r, fillColor: "#46b3ff", color: "#eafffb", weight: 1.2, fillOpacity: op,
    }).bindPopup(sitePopup(s), { maxWidth: 280 }).addTo(siteLayer);
  });

  const basinLayer = L.layerGroup();
  STORAGE.filter(s => s.kind === "basin").forEach(s => {
    if (s.lat == null || s.lon == null) return;
    const cap = s.capacity_gt || 1;
    const r = clamp(8, Math.sqrt(cap) * 1.5, 40);
    const confOp = s.confidence === "high" ? 0.32 : s.confidence === "medium" ? 0.2 : 0.1;
    const confLine = s.confidence === "high" ? 0.9 : s.confidence === "medium" ? 0.6 : 0.3;
    L.circleMarker([s.lat, s.lon], {
      radius: r, fillColor: "#7aa6ff", color: "#6f93c9", weight: 1,
      fillOpacity: confOp, opacity: confLine,
    }).bindPopup(basinPopup(s), { maxWidth: 280 }).addTo(basinLayer);
  });

  function facilityPopup(f, meta) {
    const co2 = f.est_biogenic_co2_mtpa || {};
    const flags = (f.notes || "");
    return `<b>${f.name}</b><br>${meta.label}${f.capacity_note ? " · " + f.capacity_note : ""}<br>
      Biogenic CO₂: <b>${co2.value != null ? fmt(co2.value) + " Mtpa" : "n/a"}</b>
      ${rangeTxt(co2)}<br>Retrofit potential: <b>${cap1(f.retrofit_score)}</b>
      ${f.operator ? "<br>Operator: " + f.operator : ""}
      ${flags ? `<div class="pop-src">${flags}</div>` : ""}
      <div class="pop-src">Source: ${f.source || "—"}</div>`;
  }
  function sitePopup(s) {
    return `<b>${s.name}</b><br>CO₂ storage project · ${cap1(s.status)}<br>
      Type: ${STORAGE_TYPE[s.storage_type] || s.storage_type}<br>
      Capacity: <b>${s.capacity_mtpa != null ? fmt(s.capacity_mtpa) + " Mtpa" : "n/a"}</b>
      <div class="pop-src">Source: ${s.source || "—"}</div>`;
  }
  function basinPopup(s) {
    return `<b>${s.name}</b><br>Basin storage potential<br>
      Type: ${STORAGE_TYPE[s.storage_type] || s.storage_type}<br>
      Capacity: <b>${s.capacity_gt != null ? fmt(s.capacity_gt) + " Gt" : "n/a"}</b> ·
      confidence: <b>${cap1(s.confidence)}</b>
      ${s.notes ? `<div class="pop-src">${s.notes}</div>` : ""}
      <div class="pop-src">Source: ${s.source || "—"}</div>`;
  }

  // ---- Detail panel ----
  const detail = document.getElementById("detail");
  const detailBody = document.getElementById("detail-body");

  function openDetail(id, name) {
    const rec = recById[id];
    const feed = feedById[id];
    if (!rec && !feed) {
      detailBody.innerHTML = `<div class="d-region">Region</div><div class="d-name">${name}</div>
        <p class="rationale">No BiCRS data compiled for this region yet. Coverage spans major
        biomass-producing countries plus US states; the long tail of small economies is not yet populated.</p>`;
      detail.classList.remove("hidden");
      return;
    }
    let html = `<div class="d-region">${feed && feed.level === "subnational" ? "US state" : "Country"}</div>
      <div class="d-name">${name}</div>`;

    if (rec) html += recCard(rec);
    if (feed) html += feedSection(feed);

    detailBody.innerHTML = html;
    detail.classList.remove("hidden");
  }

  function recCard(rec) {
    const meta = PATH_META[rec.recommended] || { label: rec.recommended_label, color: "#888" };
    const eff = rec.cdr_efficiency != null ? Math.round(rec.cdr_efficiency * 100) + "%" : "—";
    const cdr = rec.cdr_potential_mtpa != null ? fmt(rec.cdr_potential_mtpa) + " Mtpa" : "—";
    const storage = `${cap1(rec.storage_access)}${rec.nearest_storage_km != null ? " · ~" + fmt(rec.nearest_storage_km) + " km" : ""}`;
    let html = `<div class="rec-card">
      <div class="rec-top">
        <span class="rec-pill" style="background:${meta.color}">RECOMMENDED</span>
        <h3>${rec.recommended_label}</h3>
      </div>
      <div class="rec-meta">
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
    return html;
  }

  function feedSection(feed) {
    const rows = [
      ["Agricultural residues", feed.ag_residues_odt_mt, "Mt odt/yr"],
      ["Forestry residues", feed.forestry_residues_odt_mt, "Mt odt/yr"],
      ["MSW (total)", feed.msw_total_mt, "Mt/yr"],
      ["Animal manure", feed.animal_manure_odt_mt, "Mt odt/yr"],
      ["Human / WWTP", feed.human_wwtp_odt_mt, "Mt odt/yr"],
    ];
    let html = `<div class="d-sec-title">Feedstock supply &amp; sources</div><table class="feed">`;
    rows.forEach(([lab, obj, unit]) => {
      if (!obj || obj.value == null) return;
      html += `<tr><td class="lab">${lab}<div class="unc">${rangeTxt(obj)} ${unit}</div></td>
        <td class="val">${fmt(obj.value)}</td></tr>`;
      if (obj.source) html += `<tr><td colspan="2" class="src">↳ ${obj.source}${obj.notes ? " — " + obj.notes : ""}</td></tr>`;
    });
    // MSW biogenic fraction
    if (feed.msw_biogenic_frac && feed.msw_biogenic_frac.value != null) {
      html += `<tr><td class="lab">MSW biogenic fraction</td><td class="val">${Math.round(feed.msw_biogenic_frac.value * 100)}%</td></tr>`;
      if (feed.msw_biogenic_frac.source) html += `<tr><td colspan="2" class="src">↳ ${feed.msw_biogenic_frac.source}</td></tr>`;
    }
    html += `</table>`;
    html += `<div class="chips">
      <span class="chip">Dominant: ${labelFeed(feed.dominant_feedstock)}</span>
      <span class="chip">Density: ${cap1(feed.feedstock_density)}</span>
      <span class="chip">Nutrients: ${cap1(feed.nutrient_status)}</span></div>`;
    if (feed.notes) html += `<p class="rationale" style="margin-top:12px">${feed.notes}</p>`;
    return html;
  }

  function labelFeed(d) {
    return ({ ag_dry: "Dry ag residues", forestry_woody: "Woody forestry", msw: "Municipal waste",
      manure_wet: "Wet manure", mixed: "Mixed" })[d] || d || "—";
  }

  document.getElementById("detail-close").onclick = () => detail.classList.add("hidden");

  // ---- Legend ----
  const legend = document.getElementById("legend");
  const legendTitle = document.getElementById("legend-title");
  function renderLegend() {
    if (state.mode === "feedstock") {
      legendTitle.textContent = FEEDSTOCK_LABEL[state.feedstock] + " (Mt/yr)";
      const b = state.breaks;
      let html = "";
      const ranges = [];
      let prev = 0;
      for (let i = 0; i < GREENS.length; i++) {
        const hi = i < b.length ? b[i] : null;
        ranges.push([prev, hi]);
        prev = hi;
      }
      ranges.forEach((rg, i) => {
        const lab = rg[1] == null ? `≥ ${fmt(rg[0])}` : `${fmt(rg[0])} – ${fmt(rg[1])}`;
        html += `<div class="legend-row"><span class="box" style="background:${GREENS[i]}"></span>${lab}</div>`;
      });
      html += `<div class="legend-row"><span class="box" style="background:#2a3742"></span>No data</div>`;
      html += `<div class="legend-note">Quantile classes across all mapped regions. US shown at state resolution.</div>`;
      legend.innerHTML = html;
    } else {
      legendTitle.textContent = "Recommended pathway";
      const counts = {};
      RECS.forEach(r => { counts[r.recommended] = (counts[r.recommended] || 0) + 1; });
      let html = "";
      Object.keys(PATH_META).forEach(k => {
        if (!counts[k]) return;
        html += `<div class="legend-row"><span class="box" style="background:${PATH_META[k].color}"></span>
          ${PATH_META[k].label} <span style="color:var(--ink-3);margin-left:auto;font-family:var(--mono);font-size:10px">${counts[k]}</span></div>`;
      });
      html += `<div class="legend-row"><span class="box" style="background:#2a3742"></span>No data</div>`;
      html += `<div class="legend-note">Best use of biomass per Frontier's KPI ranking (CDR efficiency › emissions-avoiding co-product › co-benefits). Click a region for rationale.</div>`;
      legend.innerHTML = html;
    }
  }

  // ---- Controls wiring ----
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
    };
  });

  feedSelect.onchange = () => {
    state.feedstock = feedSelect.value;
    feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock] || "";
    redrawChoropleth();
  };

  document.getElementById("ov-facilities").onchange = e => toggleLayer(facilityLayer, e.target.checked);
  document.getElementById("ov-sites").onchange = e => toggleLayer(siteLayer, e.target.checked);
  document.getElementById("ov-basins").onchange = e => toggleLayer(basinLayer, e.target.checked);
  function toggleLayer(layer, on) { on ? layer.addTo(map) : map.removeLayer(layer); }

  // ---- Methodology modal ----
  const methodModal = document.getElementById("method-modal");
  document.getElementById("open-method").onclick = () => methodModal.classList.remove("hidden");
  document.getElementById("method-close").onclick = () => methodModal.classList.add("hidden");
  methodModal.onclick = e => { if (e.target === methodModal) methodModal.classList.add("hidden"); };
  document.getElementById("method-body").innerHTML = methodologyHTML();

  // ---- Global stat ----
  const totalCdr = RECS.reduce((s, r) => s + (r.cdr_potential_mtpa || 0), 0);
  document.getElementById("stat-cdr").textContent = (totalCdr / 1000).toFixed(1);

  // ---- Helpers ----
  function fmt(v) {
    if (v == null) return "—";
    if (v >= 1000) return (v / 1000).toFixed(1) + "k";
    if (v >= 100) return v.toFixed(0);
    if (v >= 10) return v.toFixed(1);
    if (v >= 1) return v.toFixed(1);
    return v.toFixed(2);
  }
  function rangeTxt(o) {
    if (!o || o.low == null || o.high == null) return "";
    return `(${fmt(o.low)}–${fmt(o.high)})`;
  }
  function cap1(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : "—"; }
  function clamp(lo, v, hi) { return Math.max(lo, Math.min(hi, v)); }

  function methodologyHTML() {
    return `
      <h2>Methodology &amp; sources</h2>
      <p>The BiCRS Atlas overlays biomass feedstock supply with CO₂ storage options and a
      best-use-of-biomass recommendation, grounded in Frontier's BiCRS purchasing POV. It is an
      internal strategy tool: every estimate carries an uncertainty range and a cited source,
      surfaced in each region's detail panel.</p>

      <h3>Feedstock supply</h3>
      <p>Recoverable biomass tonnages (Mt oven-dry/yr) by country, plus US states. Agricultural
      residues from FAOSTAT / USDA / DOE Billion-Ton crop production × residue ratios with a ~40%
      sustainable-removal cap; forestry residues from FAO FRA / DOE Billion-Ton / JRC-S2BIOM; MSW
      from World Bank <i>What a Waste 2.0</i> with regional biogenic fractions (US ≈ 61%, EU ≈ 50%);
      manure &amp; biosolids from IEA biogas outlook and FAO livestock. Country totals sum to
      ~2.9 Gt odt/yr of ag+forestry residues, consistent with the thesis range of 2.8–4.0 Gt.</p>

      <h3>CO₂ storage</h3>
      <p>Operational and planned storage projects (Global CCS Institute) plus basin-level theoretical
      capacity (US DOE NATCARB/NETL, EU CO2StoP, CO2CRC, regional atlases), graded by confidence.
      Proximity to viable storage is the key factor distinguishing geologic pathways (BECCS, injection)
      from storage-independent ones (bio-oil, burial, biochar).</p>

      <h3>Retrofit-candidate facilities</h3>
      <p>Existing biogenic-CO₂ point sources — pulp &amp; paper mills, waste-to-energy plants,
      bioenergy stations, ethanol plants, biogas/AD — that could be retrofitted with capture, including
      the BiCRS projects named in the thesis (Stockholm Exergi, Ørsted, CO280, Celsio, Drax, ADM, etc.).</p>

      <h3>Best-use recommendation engine</h3>
      <p>A transparent rule set encoding Frontier's KPI ranking — <b>CDR efficiency › emissions-avoiding
      co-product › other co-benefits</b> — modulated by feedstock moisture/density, storage proximity,
      nutrient status, and retrofit availability:</p>
      <ul>
        <li>Wet wastes (manure, biosolids) → <b>injection</b> (near storage) or <b>AD+CCS</b> — never combustion.</li>
        <li>Concentrated woody/dry residues near storage with a retrofit anchor → <b>BECCS</b> (top-preferred: ~80% efficiency + energy).</li>
        <li>Diffuse ag residues far from storage → <b>bio-oil</b> (Charm roving model) or <b>biochar</b>.</li>
        <li>No viable storage + excess nutrients → <b>biomass burial</b> (durability still being validated).</li>
        <li>Concentrated municipal waste → <b>WtE + CCS</b>.</li>
      </ul>
      <p><b>Frontier exclusions</b> (flagged, never recommended): purpose-grown energy crops,
      RNG+CCS, and corn-ethanol+CCS. National recommendations for large, heterogeneous countries
      are rollups — the optimal pathway is local, so US cells are shown at state resolution.</p>

      <h3>Caveats</h3>
      <p>Tonnages are modelled estimates, not measured inventories; ranges reflect cross-source
      spread. Country-level analysis cannot capture sub-national feedstock/storage mismatch (e.g.
      interior vs. coastal China). Storage basin capacities are theoretical and require site appraisal.
      This tool informs strategy; it does not substitute for project-level diligence.</p>
    `;
  }

  // ---- Optional deep-link via URL hash: #mode=recommendation&feed=forestry_residues_odt_mt&ov=facilities,sites,basins ----
  function applyHash() {
    const h = (location.hash || "").replace(/^#/, "");
    if (!h) return;
    const p = {};
    h.split("&").forEach(kv => { const [k, v] = kv.split("="); if (k) p[k] = decodeURIComponent(v || ""); });
    if (p.mode === "recommendation" || p.mode === "feedstock") {
      const btn = document.querySelector(`.seg-btn[data-mode="${p.mode}"]`);
      if (btn) btn.click();
    }
    if (p.feed && FEEDSTOCK_LABEL[p.feed]) { feedSelect.value = p.feed; feedSelect.onchange(); }
    if (p.ov) {
      p.ov.split(",").forEach(o => {
        const map_ = { facilities: "ov-facilities", sites: "ov-sites", basins: "ov-basins" };
        const el = document.getElementById(map_[o]);
        if (el) { el.checked = true; el.onchange({ target: el }); }
      });
    }
    if (p.region) {
      const r = feedById[p.region] || recById[p.region];
      if (r) openDetail(p.region, r.name);
    }
  }

  // ---- Initial render ----
  feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock];
  redrawChoropleth();
  try { map.fitBounds(geoLayer.getBounds(), { padding: [10, 10] }); } catch (e) {}
  applyHash();
})();
