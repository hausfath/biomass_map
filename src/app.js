/* ============================================================
   BiCRS Atlas — unified application logic.
   Tile-free thematic map (the choropleth IS the basemap); works offline by
   double-clicking index.html (no server). One engine drives three SCOPES —
   Global (countries + admin-1), United States (counties), Europe (NUTS-2) —
   selected by the scope switcher. Each scope's records are normalized to one
   common shape on load, so all render code is written once and never branches
   on scope. US/EU data bundles are lazy-loaded on first switch.
   ============================================================ */
(function () {
  "use strict";

  // ---- Shared constants ----
  const PATH_META = {
    beccs:     { label: "BECCS (heat/electricity)",   color: "#15967f" },
    beccs_pp:  { label: "BECCS — pulp & paper",        color: "#2cc0a4" },
    wte_ccs:   { label: "WtE + CCS",                   color: "#3b7dd8" },
    injection: { label: "Biomass waste injection",     color: "#9b59d0" },
    bio_oil:   { label: "Bio-oil (pyrolysis)",         color: "#e08a2b" },
    bio_oil_htl: { label: "Bio-oil (HTL)",             color: "#e0b56b" },
    burial:    { label: "Biomass burial",              color: "#b07d3a" },
    ad_ccs:    { label: "Anaerobic digestion + CCS",   color: "#6b8a9c" },
    biochar:   { label: "Biochar",                     color: "#8aa53f" },
  };
  const FAC_META = {
    pulp_paper: { label: "Pulp & paper",       color: "#e0b020" },
    ethanol:    { label: "Ethanol",            color: "#d9772b" },
    wte:        { label: "Waste-to-energy",    color: "#c0556b" },
    bioenergy:  { label: "Bioenergy / power",  color: "#e8c64a" },
    biogas_ad:  { label: "Biogas / AD",        color: "#9aa84a" },
    landfill:   { label: "Landfill gas",       color: "#8a7d5a" },
  };
  const STORAGE_TYPE = {
    saline: "Saline aquifer", depleted_og: "Depleted oil & gas",
    basalt: "Basalt (mineralization)", eor: "Enhanced oil recovery",
  };
  const GREENS = ["#dbeecf", "#a6d7a0", "#6fbf73", "#3da35a", "#1f7a45", "#0d5530"];
  const NODATA = "#2a3742";

  const FEEDSTOCK_HINTS = {
    ag: "Recoverable crop residues (straw, stover, bagasse), Mt oven-dry/yr (~40% sustainable removal cap).",
    forestry: "Logging + processing residues, Mt oven-dry/yr.",
    msw_biogenic: "Biogenic fraction of municipal solid waste, Mt/yr — only the biogenic share counts as CDR.",
    manure: "Animal manure dry-matter, Mt/yr. Wet waste → injection / AD, not combustion.",
    wwtp: "Sewage sludge / biosolids dry solids, Mt/yr.",
  };
  const FEEDSTOCK_LABEL = {
    ag: "Agricultural residues", forestry: "Forestry residues",
    msw_biogenic: "MSW (biogenic)", manure: "Animal manure", wwtp: "Human / WWTP biosolids",
  };

  // ---- Generic helpers ----
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
  function num(o) { return (o && o.value != null) ? o.value : 0; }
  function rangeTxt(o) {
    if (!o || o.low == null || o.high == null) return "";
    return `(${fmt(o.low)}–${fmt(o.high)})`;
  }
  function labelFeed(d) {
    return ({ ag_dry: "Dry ag residues", forestry_woody: "Woody forestry", msw: "Municipal waste",
      manure_wet: "Wet manure", mixed: "Mixed" })[d] || d || "—";
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
  function colorForValue(val, breaks) {
    if (val == null || val <= 0) return null;
    for (let i = 0; i < breaks.length; i++) if (val < breaks[i]) return GREENS[i];
    return GREENS[GREENS.length - 1];
  }
  function feedValue(feed, key) {
    if (!feed) return null;
    if (key === "msw_biogenic") return (feed.msw || 0) * (feed.biofrac || 0.5);
    const v = feed[key];
    return v != null ? v : null;
  }

  // ---- Ranked pros/cons reconstruction (US/EU; mirrors engine_core.region_pros_cons) ----
  const PAYLOAD_OF = { beccs: "co2", beccs_pp: "co2", wte_ccs: "co2", ad_ccs: "co2", bio_oil: "bio_oil", bio_oil_htl: "bio_oil_htl", injection: "slurry" };
  const TRANSPORT_CAP = 100;
  function regionProsCons(rec, key, profile) {
    const prof = profile[key];
    let pros = prof.pros.slice(), cons = prof.cons.slice();
    const sa = rec.storage_access, dens = rec.feedstock_density, nut = rec.nutrient_status;
    // transport-cost note (storage-dependent pathways, where a per-payload delivered cost is known)
    const tbp = rec.transport_by_payload, pay = PAYLOAD_OF[key];
    const tc = (tbp && pay) ? tbp[pay] : null;
    if (tc != null) {
      if (tc > TRANSPORT_CAP) cons.unshift(`Transport to the nearest operating well ~$${fmt(tc)}/tCO₂ — exceeds the $${TRANSPORT_CAP}/tCO₂ viability cap, so this pathway is not viable here`);
      else if (tc >= 66) cons.push(`Transport to the nearest operating well is costly (~$${fmt(tc)}/tCO₂)`);
    }
    const central = key === "beccs" || key === "beccs_pp" || key === "wte_ccs";
    const distributed = key === "bio_oil" || key === "bio_oil_htl" || key === "biochar" || key === "burial";
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
      if (key === "bio_oil" || key === "bio_oil_htl" || key === "biochar" || key === "ad_ccs") {
        pros = pros.filter(x => !/nutrient/i.test(x));
        cons.push("Returns nutrients to soils already in surplus here");
      } else if (key === "burial" || key === "injection") {
        pros.push("Removes carbon and nutrients from an over-fertilized landscape");
      }
    }
    // Retrofit-only pathways: mirror engine_core.region_pros_cons (avail = {pp,wte,ad}).
    const av = rec.avail || { pp: true, wte: true, ad: true };
    if (key === "beccs_pp") {
      if (av.pp && rec.anchor_facility) pros.push("Existing mill to retrofit: " + rec.anchor_facility);
      else if (av.pp) pros.push("Existing pulp/bioenergy mill within procurement range to retrofit");
      else cons.push("No existing pulp & paper mill within range to retrofit");
    }
    if (key === "wte_ccs") {
      if (av.wte && rec.anchor_facility) pros.push("Existing WtE plant to retrofit: " + rec.anchor_facility);
      else if (!av.wte) cons.push("No existing waste-to-energy plant within range to retrofit");
    }
    if (key === "ad_ccs") {
      if (av.ad) pros.push("Existing anaerobic-digestion capacity within range to retrofit");
      else cons.push("No existing anaerobic-digestion capacity within range to retrofit");
    }
    return [pros.slice(0, 4), cons.slice(0, 4)];
  }

  // Build a normalized `ranked` list from slim ranked_keys + a PROFILE (US/EU).
  function reconstructRanked(rec, profile) {
    return (rec.ranked_keys || []).map(item => {
      const k = item.k, prof = profile[k] || {};
      const [pros, cons] = regionProsCons(rec, k, profile);
      return { key: k, label: prof.label || k, badge: item.b,
               cdr_efficiency: prof.eff, cost_band: prof.cost, pros: pros, cons: cons };
    });
  }

  // ============================================================
  // SCOPE CONFIGS — only the divergent bits live here.
  // ============================================================
  const SUBNAT_LABEL = { USA: "US state", CAN: "Canadian province", IND: "Indian state", CHN: "Chinese province" };

  const SCOPES = {
    global: {
      label: "Global",
      hint: "Countries worldwide, with US/Canada/India/China at state-province resolution.",
      scripts: [],  // preloaded in index.html
      view: { center: [25, 12], zoom: 2, minZoom: 2, maxZoom: 8 },
      fitBounds: true,
      attribution: "Geometry: Natural Earth · Data: see Methodology",
      choroRenderer: "svg",
      lowSupplyAware: false,
      statFooter: recs => ({
        value: (recs.reduce((s, r) => s + (r.superseded_by_subnational ? 0 : (r.cdr_potential_mtpa || 0)), 0) / 1000).toFixed(1),
        label: "Gt CO₂/yr global CDR potential",
      }),
      legendNote: {
        feedstock: "Quantile classes across all mapped regions. US/CA/IN/CN at state-province resolution.",
        recommendation: "Best use of biomass per Frontier's KPI ranking (CDR efficiency › emissions-avoiding co-product › co-benefits). Click a region for rationale.",
      },
      buildGeometry: function () {
        const SUB = new Set(["USA", "CAN", "IND", "CHN"]);
        const fc = { type: "FeatureCollection", features: [] };
        (window.GEO_COUNTRIES.features || []).forEach(f => {
          if (SUB.has(f.properties.iso_a3)) return;
          fc.features.push({ type: "Feature", geometry: f.geometry,
            properties: { _id: f.properties.iso_a3, _name: f.properties.name } });
        });
        (window.GEO_SUBNATIONAL.features || []).forEach(f => {
          fc.features.push({ type: "Feature", geometry: f.geometry,
            properties: { _id: f.properties.id, _name: f.properties.name } });
        });
        return fc;
      },
      loadData: function () {
        const feedById = {}, recById = {};
        (window.DATA_FEEDSTOCKS || []).forEach(r => {
          const kind = r.level === "subnational" ? (SUBNAT_LABEL[r.parent] || "Subnational region") : "Country";
          feedById[r.id] = {
            _id: r.id, _name: r.name, regionKind: kind,
            ag: num(r.ag_residues_odt_mt), forestry: num(r.forestry_residues_odt_mt),
            msw: num(r.msw_total_mt), manure: num(r.animal_manure_odt_mt), wwtp: num(r.human_wwtp_odt_mt),
            biofrac: num(r.msw_biogenic_frac) || 0.5,
            nutrient_status: r.nutrient_status, dominant_feedstock: r.dominant_feedstock,
            _raw: r,
          };
        });
        (window.DATA_RECOMMENDATIONS || []).forEach(r => { recById[r.id] = r; }); // ranked already inline
        return { feedById: feedById, recById: recById };
      },
      feedSection: function (feed) {  // rich: cited tonnages + uncertainty
        const r = feed._raw;
        const rows = [
          ["Agricultural residues", r.ag_residues_odt_mt, "Mt odt/yr"],
          ["Forestry residues", r.forestry_residues_odt_mt, "Mt odt/yr"],
          ["MSW (total)", r.msw_total_mt, "Mt/yr"],
          ["Animal manure", r.animal_manure_odt_mt, "Mt odt/yr"],
          ["Human / WWTP", r.human_wwtp_odt_mt, "Mt odt/yr"],
        ];
        let html = `<div class="d-sec-title">Feedstock supply &amp; sources</div><table class="feed">`;
        rows.forEach(([lab, obj, unit]) => {
          if (!obj || obj.value == null) return;
          html += `<tr><td class="lab">${lab}<div class="unc">${rangeTxt(obj)} ${unit}</div></td>
            <td class="val">${fmt(obj.value)}</td></tr>`;
          if (obj.source) html += `<tr><td colspan="2" class="src">↳ ${obj.source}${obj.notes ? " — " + obj.notes : ""}</td></tr>`;
        });
        if (r.msw_biogenic_frac && r.msw_biogenic_frac.value != null) {
          html += `<tr><td class="lab">MSW biogenic fraction</td><td class="val">${Math.round(r.msw_biogenic_frac.value * 100)}%</td></tr>`;
          if (r.msw_biogenic_frac.source) html += `<tr><td colspan="2" class="src">↳ ${r.msw_biogenic_frac.source}</td></tr>`;
        }
        html += `</table><div class="chips">
          <span class="chip">Dominant: ${labelFeed(r.dominant_feedstock)}</span>
          <span class="chip">Density: ${cap1(r.feedstock_density)}</span>
          <span class="chip">Nutrients: ${cap1(r.nutrient_status)}</span></div>`;
        if (r.notes) html += `<p class="rationale" style="margin-top:12px">${r.notes}</p>`;
        return html;
      },
      storageDetailRows: null,
      overlays: [
        { id: "facilities", label: "Retrofit-candidate facilities", swatch: "sw-fac",
          build: r => facilityCircleLayer(window.DATA_FACILITIES || [], r.ov) },
        { id: "sites", label: "CO₂ storage — projects", swatch: "sw-site",
          build: r => storageSiteLayer((window.DATA_STORAGE || []).filter(s => s.kind === "site"), r.ov) },
        { id: "basins", label: "CO₂ storage — basin potential", swatch: "sw-basin",
          build: r => storageBasinCircleLayer((window.DATA_STORAGE || []).filter(s => s.kind === "basin"), r.mid) },
      ],
      methodologyHTML: () => GLOBAL_METHODOLOGY,
    },

    na: {
      label: "North America",
      hint: "US counties + Canada census divisions (~3,440 regions). Storage basins, wells / CCS projects, point sources.",
      scripts: ["../data/geo/geometry_us_counties.js", "../data/geo/geometry_us_basins.js", "data_bundle_us.js",
                "../data/geo/geometry_ca_cd.js", "../data/geo/geometry_ca_basins.js", "data_bundle_ca.js"],
      view: { center: [50, -96], zoom: 3, minZoom: 2, maxZoom: 11 },
      fitBounds: false,
      attribution: "US: Census + NATCARB · Canada: StatCan + curated · see Methodology",
      choroRenderer: "svg",  // SVG handles the ~3,440 simplified regions fine and keeps
                             // clicks/hover consistent with the other scopes (no canvas quirks)
      lowSupplyAware: true,
      statFooter: recs => ({ value: fmt(recs.reduce((s, r) => s + (r.cdr_potential_mtpa || 0), 0)),
        label: "Mt CO₂/yr North America CDR potential" }),
      legendNote: {
        feedstock: "Quantile classes across all US counties + Canadian census divisions.",
        recommendation: "Best use per Frontier's KPI ranking, computed per county / census division (storage distance + feedstock density). Click a region for rationale.",
      },
      buildGeometry: function () {
        const fc = { type: "FeatureCollection", features: [] };
        (window.GEO_US_COUNTIES.features || []).forEach(f => {
          const p = f.properties;
          fc.features.push({ type: "Feature", geometry: f.geometry,
            properties: { _id: p.id, _name: `${p.name}, ${p.state}` } });
        });
        (window.GEO_CA_CD.features || []).forEach(f => {
          const p = f.properties;
          fc.features.push({ type: "Feature", geometry: f.geometry,
            properties: { _id: p.id, _name: `${p.name}, ${p.prov}` } });
        });
        return fc;
      },
      loadData: function () {
        const profile = window.US_PATHWAY_PROFILE || window.CA_PATHWAY_PROFILE || {};
        const feedById = {}, recById = {};
        (window.US_FEEDSTOCKS || []).forEach(r => {
          feedById[r.id] = {
            _id: r.id, _name: `${r.name}, ${r.state}`, regionKind: "US county — " + r.state,
            ag: r.ag, forestry: r.forestry, msw: r.msw, manure: r.manure, wwtp: r.wwtp,
            biofrac: r.biofrac || 0.61, nutrient_status: r.nutrient_status, dominant_feedstock: r.dominant_feedstock,
          };
        });
        (window.CA_FEEDSTOCKS || []).forEach(r => {
          feedById[r.id] = {
            _id: r.id, _name: `${r.name}, ${r.prov}`, regionKind: "Census division — " + r.prov,
            ag: r.ag, forestry: r.forestry, msw: r.msw, manure: r.manure, wwtp: r.wwtp,
            biofrac: r.biofrac || 0.55, nutrient_status: r.nutrient_status, dominant_feedstock: r.dominant_feedstock,
          };
        });
        (window.US_RECOMMENDATIONS || []).forEach(r => {
          recById[r.id] = Object.assign({}, r, { ranked: reconstructRanked(r, profile) });
        });
        (window.CA_RECOMMENDATIONS || []).forEach(r => {
          recById[r.id] = Object.assign({}, r, { ranked: reconstructRanked(r, profile) });
        });
        return { feedById: feedById, recById: recById };
      },
      feedSection: slimFeedSection,
      transportLookup: id => (window.US_TRANSPORT || {})[id] || (window.CA_TRANSPORT || {})[id] || null,
      storageDetailRows: function (rec) {
        const sd = rec.storage_detail || {};
        return [
          { k: "Storage basin", v: sd.in_basin ? "Overlaps " + sd.in_basin + " (theoretical)"
              : (sd.nearest_basin ? `${sd.nearest_basin} (~${sd.nearest_basin_km} km)` : "—") },
          { k: "Nearest well / project", v: sd.nearest_well ? `${sd.nearest_well}${sd.nearest_well_km != null ? ` (~${sd.nearest_well_km} km)` : ""}` : "—" },
          { k: "Feedstock density", v: `${cap1(rec.feedstock_density)} · ${fmt(rec.residue_density_tco2_km2)} tCO₂/km²` },
          { k: "Supply within 80 km", v: `${fmt(rec.haul_supply_mtco2)} Mt CO₂/yr` },
        ];
      },
      overlays: [
        { id: "facilities", label: "Biogenic point sources (GHGRP / curated)", swatch: "sw-fac",
          build: r => facilityCircleLayer([...(window.US_FACILITIES || []), ...(window.CA_FACILITIES || [])], r.ov) },
        { id: "wwtps", label: "Large WWTPs", swatch: "sw-wwtp",
          build: r => wwtpLayer([...(window.US_WWTPS || []), ...(window.CA_WWTPS || [])], r.ov, w => `${w.state || w.prov || ""}`) },
        { id: "wells6", label: "CO₂ storage wells / projects", swatch: "sw-well6",
          build: r => wellLayer([...((window.US_WELLS || []).filter(w => w.well_class !== "V")), ...(window.CA_WELLS || [])], r.ov, "#46b3ff") },
        { id: "wells5", label: "Class V injection (US — biomass / bio-oil)", swatch: "sw-well5",
          build: r => wellLayer((window.US_WELLS || []).filter(w => w.well_class === "V"), r.ov, "#c97be0") },
        { id: "basins", label: "Storage basins (NATCARB · WCSB / Williston)", swatch: "sw-form",
          build: r => polygonLayer({ type: "FeatureCollection",
            features: [...(window.GEO_US_BASINS.features || []), ...(window.GEO_CA_BASINS.features || [])] },
            r.mid, "NATCARB (US) · curated (Canada)") },
      ],
      methodologyHTML: () => US_METHODOLOGY + CA_METHODOLOGY,
    },

    eu: {
      label: "Europe",
      hint: "~290 NUTS-2 regions (EU-27 + UK + Norway). Storage formations (CO2StoP), projects, point sources.",
      scripts: ["../data/geo/geometry_eu_nuts.js", "../data/geo/geometry_eu_storage.js", "data_bundle_eu.js"],
      view: { center: [54, 10], zoom: 4, minZoom: 3, maxZoom: 9 },
      fitBounds: false,
      attribution: "Regions: Eurostat GISCO · Biomass: JRC ENSPRESO · Storage: CO2StoP · see Methodology",
      choroRenderer: "svg",
      lowSupplyAware: true,
      statFooter: recs => ({ value: fmt(recs.reduce((s, r) => s + (r.cdr_potential_mtpa || 0), 0)),
        label: "Mt CO₂/yr EU NUTS-2 CDR potential" }),
      legendNote: {
        feedstock: "Quantile classes across all NUTS-2 regions.",
        recommendation: "Best use per Frontier's KPI ranking, computed per NUTS-2 region (storage distance + feedstock density). Click a region for rationale.",
      },
      buildGeometry: function () {
        const fc = { type: "FeatureCollection", features: [] };
        (window.GEO_EU_NUTS.features || []).forEach(f => {
          const p = f.properties;
          fc.features.push({ type: "Feature", geometry: f.geometry,
            properties: { _id: p.id, _name: `${p.name} — ${p.country}` } });
        });
        return fc;
      },
      loadData: function () {
        const profile = window.EU_PATHWAY_PROFILE || {};
        const feedById = {}, recById = {};
        (window.EU_FEEDSTOCKS || []).forEach(r => {
          feedById[r.id] = {
            _id: r.id, _name: `${r.name} — ${r.country}`, regionKind: "NUTS-2 region — " + r.country,
            ag: r.ag, forestry: r.forestry, msw: r.msw, manure: r.manure, wwtp: r.wwtp,
            biofrac: r.biofrac || 0.5, nutrient_status: r.nutrient_status, dominant_feedstock: r.dominant_feedstock,
          };
        });
        (window.EU_RECOMMENDATIONS || []).forEach(r => {
          recById[r.id] = Object.assign({}, r, { ranked: reconstructRanked(r, profile) });
        });
        return { feedById: feedById, recById: recById };
      },
      feedSection: slimFeedSection,
      transportLookup: id => (window.EU_TRANSPORT || {})[id] || null,
      storageDetailRows: function (rec) {
        const sd = rec.storage_detail || {};
        return [
          { k: "Storage formation", v: sd.in_formation ? "Overlaps " + sd.in_formation + " (theoretical)"
              : (sd.nearest_formation ? `${sd.nearest_formation} (~${sd.nearest_formation_km} km)` : "—") },
          { k: "Nearest project", v: sd.nearest_project ? `${sd.nearest_project}${sd.nearest_project_km != null ? ` (~${sd.nearest_project_km} km)` : ""}` : "—" },
          { k: "Feedstock density", v: `${cap1(rec.feedstock_density)} · ${fmt(rec.residue_density_tco2_km2)} tCO₂/km²` },
          { k: "Dominant feedstock", v: labelFeed(rec.dominant_feedstock) },
        ];
      },
      overlays: [
        { id: "facilities", label: "Biogenic point sources", swatch: "sw-fac",
          build: r => facilityCircleLayer(window.EU_FACILITIES || [], r.ov) },
        { id: "wwtps", label: "Large WWTPs (≥150k PE)", swatch: "sw-wwtp",
          build: r => wwtpLayer(window.EU_WWTPS || [], r.ov,
            w => `${w.pe ? fmt(w.pe / 1000) + "k PE · " : ""}${w.country}`) },
        { id: "projects", label: "CO₂ storage projects / hubs", swatch: "sw-proj",
          build: r => storageProjectLayer(window.EU_STORAGE_PROJECTS || [], r.ov) },
        { id: "formations", label: "CO₂ storage formations (CO2StoP)", swatch: "sw-form",
          build: r => polygonLayer(window.GEO_EU_STORAGE, r.mid, "CO2StoP (JRC)") },
      ],
      methodologyHTML: () => EU_METHODOLOGY,
    },
  };

  // Slim feedstock detail (US/EU): flat values, no per-field sources.
  function slimFeedSection(feed) {
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
      html += `<tr><td class="lab">${lab}<div class="unc">${unit}</div></td><td class="val">${fmt(v)}</td></tr>`;
    });
    html += `<tr><td class="lab">MSW biogenic fraction</td><td class="val">${Math.round((feed.biofrac || 0.5) * 100)}%</td></tr></table>`;
    html += `<div class="chips">
      <span class="chip">Dominant: ${labelFeed(feed.dominant_feedstock)}</span>
      <span class="chip">Nutrients: ${cap1(feed.nutrient_status)}</span></div>
      <p class="rationale" style="margin-top:10px">Regional tonnages disaggregate the parent total
      (see Methodology); choropleth values are per-region.</p>`;
    return html;
  }

  // ============================================================
  // Map + persistent panes/renderers (created once)
  // ============================================================
  const map = L.map("map", {
    center: [25, 12], zoom: 2, minZoom: 2, maxZoom: 8,
    worldCopyJump: true, zoomControl: true, attributionControl: false,
  });
  let attribCtl = L.control.attribution({ prefix: false }).addTo(map);
  let attribText = "";

  map.createPane("choroPane"); map.getPane("choroPane").style.zIndex = 410;
  map.createPane("midPane");   map.getPane("midPane").style.zIndex = 450;
  map.createPane("ovPane");    map.getPane("ovPane").style.zIndex = 470;
  const midRenderer = L.svg({ pane: "midPane" });
  const ovRenderer = L.svg({ pane: "ovPane" });

  // ---- Overlay layer builders (shared; used by scope configs) ----
  function facilityCircleLayer(list, rnd) {
    const lg = L.layerGroup();
    list.forEach(f => {
      if (f.lat == null || f.lon == null) return;
      const co2 = (f.est_biogenic_co2_mtpa || {}).value;
      const r = clamp(3, 3 + Math.sqrt(co2 || 0.3) * 3.2, 20);
      const meta = FAC_META[f.type] || { label: f.type, color: "#e0b020" };
      L.circleMarker([f.lat, f.lon], { radius: r, fillColor: meta.color, color: "#0e1419",
        weight: 1, fillOpacity: 0.85, renderer: rnd })
        .bindPopup(facilityPopup(f, meta), { maxWidth: 280 }).addTo(lg);
    });
    return lg;
  }
  function storageSiteLayer(list, rnd) {
    const lg = L.layerGroup();
    list.forEach(s => {
      if (s.lat == null || s.lon == null) return;
      const r = clamp(4, 4 + Math.sqrt(s.capacity_mtpa || 0.5) * 4, 18);
      const op = s.status === "operational" ? 0.9 : s.status === "construction" ? 0.6 : 0.35;
      L.circleMarker([s.lat, s.lon], { radius: r, fillColor: "#46b3ff", color: "#eafffb",
        weight: 1.2, fillOpacity: op, renderer: rnd })
        .bindPopup(sitePopup(s), { maxWidth: 280 }).addTo(lg);
    });
    return lg;
  }
  function storageProjectLayer(list, rnd) {
    const lg = L.layerGroup();
    list.forEach(p => {
      if (p.lat == null || p.lon == null) return;
      const r = p.capacity_mtpa ? clamp(6, 6 + Math.sqrt(p.capacity_mtpa) * 3, 16) : 7;
      const op = p.status === "operational" ? 0.95 : p.status === "construction" ? 0.7 : 0.4;
      L.circleMarker([p.lat, p.lon], { radius: r, fillColor: "#46b3ff", color: "#eafffb",
        weight: 1.2, fillOpacity: op, renderer: rnd })
        .bindPopup(projectPopup(p), { maxWidth: 280 }).addTo(lg);
    });
    return lg;
  }
  function storageBasinCircleLayer(list, rnd) {
    const lg = L.layerGroup();
    list.forEach(s => {
      if (s.lat == null || s.lon == null) return;
      const r = clamp(8, Math.sqrt(s.capacity_gt || 1) * 1.5, 40);
      const confOp = s.confidence === "high" ? 0.32 : s.confidence === "medium" ? 0.2 : 0.1;
      const confLine = s.confidence === "high" ? 0.9 : s.confidence === "medium" ? 0.6 : 0.3;
      L.circleMarker([s.lat, s.lon], { radius: r, fillColor: "#7aa6ff", color: "#6f93c9",
        weight: 1, fillOpacity: confOp, opacity: confLine, renderer: rnd })
        .bindPopup(basinPopup(s), { maxWidth: 280 }).addTo(lg);
    });
    return lg;
  }
  function wwtpLayer(list, rnd, subFn) {
    const lg = L.layerGroup();
    list.forEach(w => {
      if (w.lat == null || w.lon == null) return;
      L.circleMarker([w.lat, w.lon], { radius: 2.5, fillColor: "#5bb0c7", color: "#0e1419",
        weight: 0.5, fillOpacity: 0.8, renderer: rnd })
        .bindPopup(`<b>${w.name}</b><br>Large WWTP · ${subFn(w)}
          <div class="pop-src">Source: ${w.source || "—"}</div>`, { maxWidth: 260 }).addTo(lg);
    });
    return lg;
  }
  function wellLayer(list, rnd, color) {
    const lg = L.layerGroup();
    list.forEach(w => {
      if (w.lat == null || w.lon == null) return;
      const op = w.status === "operational" ? 0.95 : w.status === "issued" ? 0.85
        : w.status === "draft" ? 0.55 : 0.35;
      const r = w.co2_mtpa ? clamp(5, 5 + Math.sqrt(w.co2_mtpa) * 4, 16) : 6;
      L.circleMarker([w.lat, w.lon], { radius: r, fillColor: color, color: "#eafffb",
        weight: 1.2, fillOpacity: op, renderer: rnd })
        .bindPopup(wellPopup(w), { maxWidth: 280 }).addTo(lg);
    });
    return lg;
  }
  function polygonLayer(fc, rnd, sourceLabel) {  // non-interactive storage polygons (click-through)
    return L.geoJSON(fc, { renderer: rnd, interactive: false,
      style: { fillColor: "#7aa6ff", color: "#6f93c9", weight: 0.9, fillOpacity: 0.16, opacity: 0.5 } });
  }

  function facilityPopup(f, meta) {
    const co2 = f.est_biogenic_co2_mtpa || {};
    return `<b>${f.name}</b><br>${meta.label}${f.capacity_note ? " · " + f.capacity_note : ""}<br>
      Biogenic CO₂: <b>${co2.value != null ? fmt(co2.value) + " Mtpa" : "n/a"}</b> ${rangeTxt(co2)}<br>
      Retrofit potential: <b>${cap1(f.retrofit_score)}</b>${f.country || f.state ? " · " + (f.state || f.country) : ""}
      ${f.operator ? "<br>Operator: " + f.operator : ""}
      ${f.notes ? `<div class="pop-src">${f.notes}</div>` : ""}
      <div class="pop-src">Source: ${f.source || "—"}</div>`;
  }
  function sitePopup(s) {
    return `<b>${s.name}</b><br>CO₂ storage project · ${cap1(s.status)}<br>
      Type: ${STORAGE_TYPE[s.storage_type] || s.storage_type}<br>
      Capacity: <b>${s.capacity_mtpa != null ? fmt(s.capacity_mtpa) + " Mtpa" : "n/a"}</b>
      <div class="pop-src">Source: ${s.source || "—"}</div>`;
  }
  function projectPopup(p) {
    return `<b>${p.name}</b><br>CO₂ storage project · ${cap1(p.status)}<br>
      ${p.storage_type ? "Type: " + (STORAGE_TYPE[p.storage_type] || p.storage_type) + "<br>" : ""}
      ${p.capacity_mtpa ? "Capacity: <b>" + fmt(p.capacity_mtpa) + " Mtpa</b><br>" : ""}${p.country || ""}
      <div class="pop-src">Source: ${p.source || "—"}</div>`;
  }
  function basinPopup(s) {
    return `<b>${s.name}</b><br>Basin storage potential<br>
      Type: ${STORAGE_TYPE[s.storage_type] || s.storage_type}<br>
      Capacity: <b>${s.capacity_gt != null ? fmt(s.capacity_gt) + " Gt" : "n/a"}</b> · confidence: <b>${cap1(s.confidence)}</b>
      ${s.notes ? `<div class="pop-src">${s.notes}</div>` : ""}
      <div class="pop-src">Source: ${s.source || "—"}</div>`;
  }
  function wellPopup(w) {
    const cls = w.well_class === "V" ? "Class V (biomass / bio-oil injection)"
      : w.well_class === "VI/RR" ? "Geologic sequestration (Subpart RR)"
      : w.well_class === "VI" ? "Class VI (CO₂ storage)"
      : "CO₂ storage project / hub";  // Canada: curated CCS projects (no US well classes)
    return `<b>${w.name}</b><br>${cls} · ${cap1(w.status)}<br>
      ${w.operator ? "Operator: " + w.operator + "<br>" : ""}
      ${w.co2_mtpa ? "CO₂: <b>" + fmt(w.co2_mtpa) + " Mtpa</b><br>" : ""}${w.state || w.prov || ""}
      <div class="pop-src">Source: ${w.source || "—"}</div>`;
  }

  // ============================================================
  // Active-scope state + shared rendering
  // ============================================================
  const state = { scope: "global", mode: "feedstock", feedstock: "ag", breaks: [], openRegion: null, showRoute: false };
  let combined = null, feedById = {}, recById = {};
  let geoLayer = null, choroRenderer = null;
  let activeOverlays = [];  // [{id, layer, checkbox}]
  const routeGroup = L.featureGroup();   // multimodal transport route (featureGroup → has getBounds)
  const ROUTE_MODE = {                 // colour + label per transport mode
    truck: { color: "#e0843b", label: "Truck" },
    rail: { color: "#8a6fd4", label: "Rail" },
    ship: { color: "#46b3ff", label: "Ship (coastal)" },
    barge: { color: "#3fb6a8", label: "Barge (river)" },
  };

  const dom = {
    hovertip: document.getElementById("hovertip"),
    detail: document.getElementById("detail"),
    detailBody: document.getElementById("detail-body"),
    legend: document.getElementById("legend"),
    legendTitle: document.getElementById("legend-title"),
    overlayList: document.getElementById("overlay-list"),
    feedControls: document.getElementById("feedstock-controls"),
    feedSelect: document.getElementById("feedstock-select"),
    feedHint: document.getElementById("feedstock-hint"),
    scopeHint: document.getElementById("scope-hint"),
    statCdr: document.getElementById("stat-cdr"),
    statLabel: document.getElementById("stat-label"),
  };

  function styleFeature(feature) {
    const id = feature.properties._id;
    let fill = NODATA, opacity = 0.38;
    if (state.mode === "feedstock") {
      const c = colorForValue(feedValue(feedById[id], state.feedstock), state.breaks);
      if (c) { fill = c; opacity = 0.92; }
    } else {
      const rec = recById[id];
      if (rec && !rec.low_supply && !rec.no_option && PATH_META[rec.recommended]) { fill = PATH_META[rec.recommended].color; opacity = 0.9; }
      else if (rec && (rec.low_supply || rec.no_option)) { fill = NODATA; opacity = 0.5; }
    }
    return { fillColor: fill, fillOpacity: opacity, color: "#0e1419", weight: 0.5 };
  }
  function recomputeBreaks() {
    state.breaks = quantileBreaks(
      combined.features.map(f => feedValue(feedById[f.properties._id], state.feedstock)), GREENS.length);
  }
  function redrawChoropleth() {
    if (state.mode === "feedstock") recomputeBreaks();
    if (geoLayer) geoLayer.setStyle(styleFeature);
    renderLegend();
  }

  let hoveredLayer = null;
  function highlight(layer) {
    if (hoveredLayer && hoveredLayer !== layer && geoLayer) geoLayer.resetStyle(hoveredLayer);
    hoveredLayer = layer;
    layer.setStyle({ weight: 1.8, color: "#eafffb" });
  }
  function unhighlight(layer) {
    if (geoLayer) geoLayer.resetStyle(layer);
    if (hoveredLayer === layer) hoveredLayer = null;
  }
  function showHoverTip(e, feature) {
    const id = feature.properties._id, name = feature.properties._name;
    let sub;
    if (state.mode === "feedstock") {
      const v = feedValue(feedById[id], state.feedstock);
      sub = v == null ? "no data" : `<span class="ht-val">${fmt(v)} Mt/yr</span>`;
    } else {
      const rec = recById[id];
      if (!rec) sub = "no data";
      else if (rec.no_option) sub = `<span class="ht-val lowsup">No viable BiCRS pathway</span>`;
      else sub = `<span class="ht-val">${PATH_META[rec.recommended].label}</span>`
        + (rec.low_supply ? ' <span class="lowsup">· low supply</span>' : "");
    }
    dom.hovertip.innerHTML = `<div class="ht-name">${name}</div>${sub}`;
    dom.hovertip.classList.remove("hidden");
    moveHoverTip(e);
  }
  function moveHoverTip(e) {
    dom.hovertip.style.left = e.originalEvent.clientX + "px";
    dom.hovertip.style.top = e.originalEvent.clientY + "px";
  }
  function hideHoverTip() { dom.hovertip.classList.add("hidden"); }

  // ---- Detail panel (shared) ----
  // ---- Multimodal transport route (to_do item 4) ----
  function transportFor(sc, id) {
    return (sc.transportLookup && id) ? sc.transportLookup(id) : null;
  }

  function redrawRoute() {
    routeGroup.clearLayers();
    const sc = SCOPES[state.scope];
    if (!state.showRoute || !state.openRegion) { return; }
    const t = transportFor(sc, state.openRegion.id);
    if (!t || !t.legs || !t.legs.length) return;
    t.legs.forEach(leg => {
      const m = ROUTE_MODE[leg.mode] || { color: "#aaa", label: leg.mode };
      // ship/barge legs follow real water geometry (leg.path); truck/rail are straight from→to
      const line = (leg.path && leg.path.length > 1) ? leg.path : [leg.from, leg.to];
      // dark casing underneath so the coloured line is legible over any choropleth colour
      L.polyline(line, { color: "#0e1419", weight: 7, opacity: 0.55,
        renderer: ovRenderer }).addTo(routeGroup);
      L.polyline(line, {
        color: m.color, weight: 4, opacity: 0.95, renderer: ovRenderer,
        dashArray: (leg.mode === "ship" || leg.mode === "barge") ? "8 5" : null,
      }).bindTooltip(`${m.label}: ${leg.km} km`, { sticky: true }).addTo(routeGroup);
      if (leg.to_name) {   // transfer / destination node marker
        L.circleMarker(leg.to, { radius: 4, fillColor: m.color, color: "#0e1419",
          weight: 1, fillOpacity: 1, renderer: ovRenderer })
          .bindTooltip(leg.to_name, { direction: "top" }).addTo(routeGroup);
      }
    });
    if (!map.hasLayer(routeGroup)) routeGroup.addTo(map);
  }

  function transportSummaryHTML(sc, id) {
    const t = transportFor(sc, id);
    if (!t) return "";
    const modes = (t.modes || []).map(m => (ROUTE_MODE[m] || { label: m }).label).join(" → ");
    const bp = t.by_payload || {};
    const row = (lbl, v) => `<div><div class="k">${lbl}</div><div class="v">${v == null ? "—" : "$" + fmt(v) + "/tCO₂"}</div></div>`;
    return `<div class="chart-card">
      <div class="chart-title">Transport to storage <span class="hint" style="font-weight:400">(screening, v1)</span></div>
      <div class="chart-sub">Least-cost route to nearest operating well: <b>${t.dest_well || "—"}</b> · ${modes || "—"} · ${fmt(t.total_km)} km. Delivered cost by what's moved (carbon-density-weighted):</div>
      <div class="d-metrics">
        ${row("Captured CO₂ (BECCS/WtE/AD)", bp.co2)}
        ${row("Bio-oil (densified)", bp.bio_oil)}
        ${row("Wet biomass slurry (injection)", bp.slurry)}
      </div>
      <div class="chart-sub" style="margin-top:6px">Toggle <b>CO₂ transport route</b> in Map layers to draw the path. Great-circle screening, not yet network-routed.</div>
    </div>`;
  }

  function openDetail(id, name) {
    state.openRegion = { id: id, name: name };
    const rec = recById[id], feed = feedById[id];
    const sc = SCOPES[state.scope];
    if (!rec && !feed) {
      dom.detailBody.innerHTML = `<div class="d-region">Region</div><div class="d-name">${name}</div>
        <p class="rationale">No BiCRS data compiled for this region in the ${sc.label} scope.</p>`;
      dom.detail.classList.remove("hidden");
      return;
    }
    const regionKind = (feed && feed.regionKind) || "Region";
    let html = `<div class="d-region">${regionKind}</div><div class="d-name">${name}</div>`;
    if (state.mode === "feedstock") {
      if (feed) html += feedstockBarChart(feed) + sc.feedSection(feed);
      else if (rec) html += recCard(rec, sc);
    } else {
      if (rec) html += recCard(rec, sc) + rankedList(rec);
      else if (feed) html += sc.feedSection(feed);
    }
    html += transportSummaryHTML(sc, id);
    dom.detailBody.innerHTML = html;
    dom.detail.classList.remove("hidden");
    redrawRoute();
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

  function recCard(rec, sc) {
    if (rec.no_option) {   // no good BiCRS pathway — distinct muted card, no KPI grid
      let h = `<div class="rec-card">
        <div class="rec-top"><span class="rec-pill" style="background:#3a4350">NO VIABLE PATHWAY</span>
          <h3>No good BiCRS option here</h3></div>
        <p class="rationale">${rec.rationale || ""}</p>`;
      (rec.caveats || []).forEach(c => { h += `<div class="caveat">${c}</div>`; });
      h += `</div>`;
      if (sc.storageDetailRows) {
        const rows = sc.storageDetailRows(rec);
        h += `<div class="d-metrics">` + rows.map(r =>
          `<div><div class="k">${r.k}</div><div class="v">${r.v}</div></div>`).join("") + `</div>`;
      }
      return h;
    }
    const meta = PATH_META[rec.recommended] || { label: rec.recommended_label, color: "#888" };
    const eff = rec.cdr_efficiency != null ? Math.round(rec.cdr_efficiency * 100) + "%" : "—";
    const cdr = rec.cdr_potential_mtpa != null ? fmt(rec.cdr_potential_mtpa) + " Mtpa" : "—";
    // routed transport distance (from the transport model) + delivered storage-transport cost,
    // shown only for storage-dependent pathways (burial/biochar are stored locally — no transport).
    const usesTransport = !!PAYLOAD_OF[rec.recommended];
    const t = (sc.transportLookup && rec.id) ? sc.transportLookup(rec.id) : null;
    const distKm = (t && t.total_km != null) ? t.total_km : rec.nearest_storage_km;
    const storage = cap1(rec.storage_access) + (usesTransport && distKm != null ? " · ~" + fmt(distKm) + " km" : "");
    const storageCost = rec.transport_usd_per_tco2 != null ? "$" + fmt(rec.transport_usd_per_tco2) + "/tCO₂"
      : (usesTransport ? "—" : "none (stored locally)");
    let html = `<div class="rec-card">
      <div class="rec-top"><span class="rec-pill" style="background:${meta.color}">RECOMMENDED</span>
        <h3>${rec.recommended_label}</h3></div>`;
    if (rec.low_supply) html += `<div class="caveat lowsup">Negligible recoverable biomass — recommendation indicative only.</div>`;
    html += `<div class="rec-meta">
        <div><div class="k">CDR efficiency</div><div class="v">${eff}</div></div>
        <div><div class="k">CDR potential</div><div class="v">${cdr}</div></div>
        <div><div class="k">Pathway cost</div><div class="v" style="font-size:12px">${rec.cost_band || "—"}</div></div>
        <div><div class="k">Storage transport</div><div class="v" style="font-size:12px">${storageCost}</div></div>
        <div><div class="k">Storage access</div><div class="v" style="font-size:12px">${storage}</div></div>
        <div><div class="k">Retrofit anchor</div><div class="v" style="font-size:11px">${rec.anchor_facility || "none mapped"}</div></div>
      </div>
      <p class="rationale">${rec.rationale || ""}</p>
      <div class="runner">Runner-up: <b>${rec.runner_up_label}</b></div>`;
    (rec.caveats || []).forEach(c => { html += `<div class="caveat">${c}</div>`; });
    (rec.flags || []).forEach(f => { html += `<div class="flag">${f}</div>`; });
    html += `</div>`;
    if (sc.storageDetailRows) {
      const rows = sc.storageDetailRows(rec);
      html += `<div class="d-metrics">` + rows.map(r =>
        `<div><div class="k">${r.k}</div><div class="v">${r.v}</div></div>`).join("") + `</div>`;
    }
    return html;
  }

  function rankedList(rec) {
    if (!rec.ranked || !rec.ranked.length) return "";
    const badgeClass = b => "rk-" + b.toLowerCase().replace(/[^a-z]+/g, "");
    let html = `<div class="d-sec-title">CDR options ranked — best to worst here</div>`;
    rec.ranked.forEach((p, i) => {
      const color = (PATH_META[p.key] || {}).color || "#888";
      const pros = (p.pros || []).map(x => `<li>${x}</li>`).join("");
      const cons = (p.cons || []).map(x => `<li>${x}</li>`).join("");
      html += `<div class="rank-item">
        <div class="rank-head">
          <span class="rank-num" style="background:${color}">${i + 1}</span>
          <span class="rank-name">${p.label}</span>
          <span class="rank-badge ${badgeClass(p.badge)}">${p.badge}</span>
        </div>
        <div class="rank-meta">${Math.round((p.cdr_efficiency || 0) * 100)}% CDR efficiency · ${p.cost_band || ""}</div>
        <div class="rank-pc"><ul class="pc-pros">${pros}</ul><ul class="pc-cons">${cons}</ul></div>
      </div>`;
    });
    return html;
  }

  function refreshDetail() {
    if (state.openRegion && !dom.detail.classList.contains("hidden")) {
      openDetail(state.openRegion.id, state.openRegion.name);
    }
  }
  function closeDetail() { dom.detail.classList.add("hidden"); state.openRegion = null; redrawRoute(); }
  document.getElementById("detail-close").onclick = closeDetail;

  // ---- Legend (shared; scope supplies notes + low-supply awareness) ----
  function renderLegend() {
    const sc = SCOPES[state.scope];
    if (state.mode === "feedstock") {
      dom.legendTitle.textContent = FEEDSTOCK_LABEL[state.feedstock] + " (Mt/yr)";
      const b = state.breaks, ranges = [];
      let prev = 0;
      for (let i = 0; i < GREENS.length; i++) { const hi = i < b.length ? b[i] : null; ranges.push([prev, hi]); prev = hi; }
      let html = "";
      ranges.forEach((rg, i) => {
        const lab = rg[1] == null ? `≥ ${fmt(rg[0])}` : `${fmt(rg[0])} – ${fmt(rg[1])}`;
        html += `<div class="legend-row"><span class="box" style="background:${GREENS[i]}"></span>${lab}</div>`;
      });
      html += `<div class="legend-row"><span class="box" style="background:${NODATA}"></span>No / negligible data</div>`;
      html += `<div class="legend-note">${sc.legendNote.feedstock}</div>`;
      dom.legend.innerHTML = html;
    } else {
      dom.legendTitle.textContent = "Recommended pathway";
      const counts = {};
      let nNone = 0;
      Object.values(recById).forEach(r => {
        if (r.no_option) { nNone++; return; }
        if (sc.lowSupplyAware && r.low_supply) return;
        counts[r.recommended] = (counts[r.recommended] || 0) + 1;
      });
      let html = "";
      Object.keys(PATH_META).forEach(k => {
        if (!counts[k]) return;
        html += `<div class="legend-row"><span class="box" style="background:${PATH_META[k].color}"></span>
          ${PATH_META[k].label} <span style="color:var(--ink-3);margin-left:auto;font-family:var(--mono);font-size:10px">${counts[k]}</span></div>`;
      });
      const greyLabel = nNone ? "No viable pathway" + (sc.lowSupplyAware ? " / low supply" : "") : (sc.lowSupplyAware ? "Low / negligible supply" : "No data");
      html += `<div class="legend-row"><span class="box" style="background:${NODATA}"></span>${greyLabel}${nNone ? ` <span style="color:var(--ink-3);margin-left:auto;font-family:var(--mono);font-size:10px">${nNone}</span>` : ""}</div>`;
      html += `<div class="legend-note">${sc.legendNote.recommendation}</div>`;
      dom.legend.innerHTML = html;
    }
  }

  // ---- Overlay checkbox list (rebuilt per scope) ----
  function buildOverlays(sc) {
    activeOverlays.forEach(o => { if (map.hasLayer(o.layer)) map.removeLayer(o.layer); });
    activeOverlays = [];
    dom.overlayList.innerHTML = "";
    sc.overlays.forEach(def => {
      const layer = def.build({ ov: ovRenderer, mid: midRenderer });
      const lbl = document.createElement("label");
      lbl.className = "chk";
      lbl.innerHTML = `<input type="checkbox" data-ov="${def.id}" /> <span class="sw ${def.swatch}"></span> ${def.label}`;
      const cb = lbl.querySelector("input");
      cb.onchange = e => { e.target.checked ? layer.addTo(map) : map.removeLayer(layer); };
      dom.overlayList.appendChild(lbl);
      activeOverlays.push({ id: def.id, layer: layer, checkbox: cb });
    });
    // Region-dependent transport-route toggle (only where a transport model exists for the scope).
    routeGroup.clearLayers();
    state.showRoute = false;
    if (sc.transportLookup) {
      const lbl = document.createElement("label");
      lbl.className = "chk";
      lbl.innerHTML = `<input type="checkbox" data-ov="route" /> ` +
        `<span class="sw" style="background:linear-gradient(90deg,#e0843b 0 25%,#8a6fd4 25% 50%,#46b3ff 50% 75%,#3fb6a8 75%)"></span> ` +
        `CO₂ transport route <span class="hint" style="font-weight:400">(selected region)</span>`;
      lbl.querySelector("input").onchange = e => {
        state.showRoute = e.target.checked;
        redrawRoute();
        if (state.showRoute && routeGroup.getLayers().length) {
          try { map.fitBounds(routeGroup.getBounds(), { padding: [40, 40], maxZoom: 7 }); } catch (_) {}
        }
      };
      dom.overlayList.appendChild(lbl);
    }
  }

  // ============================================================
  // Scope switching (with lazy script loading)
  // ============================================================
  const loaded = { global: true };  // global preloaded in index.html
  function loadScope(id) {
    return new Promise((resolve, reject) => {
      if (loaded[id]) return resolve();
      const queue = SCOPES[id].scripts.slice();
      (function next() {
        if (!queue.length) { loaded[id] = true; return resolve(); }
        const s = document.createElement("script");
        s.src = queue.shift();
        s.onload = next;
        s.onerror = () => reject(new Error("Failed to load " + s.src));
        document.body.appendChild(s);
      })();
    });
  }

  function setAttribution(text) {
    if (attribText) attribCtl.removeAttribution(attribText);
    attribText = text;
    attribCtl.addAttribution(text);
  }

  let switching = false;
  function setScope(id, opts) {
    opts = opts || {};
    if (switching) return Promise.resolve();
    const sc = SCOPES[id];
    if (!sc) return Promise.resolve();
    switching = true;
    document.querySelectorAll("#scope-seg .seg-btn").forEach(b =>
      b.classList.toggle("active", b.dataset.scope === id));
    dom.scopeHint.textContent = sc.hint;

    return loadScope(id).then(() => {
      state.scope = id;
      closeDetail();
      hideHoverTip();

      // teardown — remove the layer AND its renderer so no stale renderer element
      // lingers in choroPane (which would break the next scope's hit-detection).
      if (geoLayer) { map.removeLayer(geoLayer); geoLayer = null; }
      if (choroRenderer) { map.removeLayer(choroRenderer); choroRenderer = null; }
      hoveredLayer = null;

      // data + geometry
      combined = sc.buildGeometry();
      const data = sc.loadData();
      feedById = data.feedById; recById = data.recById;

      // choropleth with the scope's renderer
      choroRenderer = sc.choroRenderer === "canvas"
        ? L.canvas({ pane: "choroPane" }) : L.svg({ pane: "choroPane" });
      geoLayer = L.geoJSON(combined, {
        style: styleFeature, renderer: choroRenderer,
        onEachFeature: function (feature, layer) {
          layer.on({
            mouseover: e => { highlight(e.target); showHoverTip(e, feature); },
            mousemove: moveHoverTip,
            mouseout: e => { unhighlight(e.target); hideHoverTip(); },
            click: () => openDetail(feature.properties._id, feature.properties._name),
          });
        },
      }).addTo(map);

      buildOverlays(sc);
      setAttribution(sc.attribution);
      document.getElementById("method-body").innerHTML = sc.methodologyHTML();
      const stat = sc.statFooter(Object.values(recById));
      dom.statCdr.textContent = stat.value;
      dom.statLabel.textContent = stat.label;

      map.setMinZoom(sc.view.minZoom); map.setMaxZoom(sc.view.maxZoom);
      if (!opts.keepView) {
        if (sc.fitBounds) { try { map.fitBounds(geoLayer.getBounds(), { padding: [10, 10] }); } catch (e) { map.setView(sc.view.center, sc.view.zoom); } }
        else map.setView(sc.view.center, sc.view.zoom);
      }
      redrawChoropleth();
      switching = false;
    }).catch(err => {
      switching = false;
      dom.overlayList.innerHTML = `<p class="hint" style="color:#e6a0a0">Could not load ${sc.label} data (${err.message}). If viewing offline, ensure the data files are present.</p>`;
    });
  }

  // ============================================================
  // Controls wiring
  // ============================================================
  document.querySelectorAll("#scope-seg .seg-btn").forEach(btn => {
    btn.onclick = () => { if (btn.dataset.scope !== state.scope) setScope(btn.dataset.scope); };
  });
  document.querySelectorAll("#mode-seg .seg-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll("#mode-seg .seg-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.mode = btn.dataset.mode;
      dom.feedControls.style.display = state.mode === "feedstock" ? "" : "none";
      redrawChoropleth();
      refreshDetail();
    };
  });
  dom.feedSelect.onchange = () => {
    state.feedstock = dom.feedSelect.value;
    dom.feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock] || "";
    redrawChoropleth();
    refreshDetail();
  };

  const methodModal = document.getElementById("method-modal");
  document.getElementById("open-method").onclick = () => methodModal.classList.remove("hidden");
  document.getElementById("method-close").onclick = () => methodModal.classList.add("hidden");
  methodModal.onclick = e => { if (e.target === methodModal) methodModal.classList.add("hidden"); };

  // ---- Deep-link hash: #scope=us&mode=recommendation&feed=ag&ov=facilities,wells6&region=US-06037 ----
  function applyHash() {
    const h = (location.hash || "").replace(/^#/, "");
    const p = {};
    h.split("&").forEach(kv => { const [k, v] = kv.split("="); if (k) p[k] = decodeURIComponent(v || ""); });
    // `us` and `ca` are now the combined North America scope; alias old deep links.
    if (p.scope === "us" || p.scope === "ca") p.scope = "na";
    const scope = (p.scope && SCOPES[p.scope]) ? p.scope : "global";
    setScope(scope).then(() => {
      if (p.mode === "recommendation" || p.mode === "feedstock") {
        const btn = document.querySelector(`#mode-seg .seg-btn[data-mode="${p.mode}"]`);
        if (btn) btn.click();
      }
      if (p.feed && FEEDSTOCK_LABEL[p.feed]) { dom.feedSelect.value = p.feed; dom.feedSelect.onchange(); }
      if (p.ov) p.ov.split(",").forEach(oid => {
        const o = activeOverlays.find(x => x.id === oid);
        if (o) { o.checkbox.checked = true; o.layer.addTo(map); }
      });
      if (p.region) {
        const r = feedById[p.region] || recById[p.region];
        if (r) openDetail(p.region, (feedById[p.region] && feedById[p.region]._name) || r.name || p.region);
      }
    });
  }

  // ============================================================
  // Methodology texts (per scope)
  // ============================================================
  const GLOBAL_METHODOLOGY = `
    <h2>Methodology &amp; sources — Global</h2>
    <p>The BiCRS Atlas overlays biomass feedstock supply with CO₂ storage options and a best-use-of-biomass
    recommendation, grounded in Frontier's BiCRS purchasing POV. Use the <b>Region scope</b> switcher for
    finer detail: <b>US</b> (county), <b>Canada</b> (census division) and <b>Europe</b> (NUTS-2). Every estimate carries an
    uncertainty range and a cited source, surfaced in each region's detail panel.</p>
    <h3>Feedstock supply</h3>
    <p>Recoverable biomass tonnages (Mt oven-dry/yr) by country, plus US/CA/IN/CN at admin-1. Ag residues
    from FAOSTAT / USDA / DOE Billion-Ton × residue ratios (~40% removal cap); forestry from FAO FRA /
    Billion-Ton / JRC; MSW from World Bank <i>What a Waste 2.0</i> with regional biogenic fractions;
    manure &amp; biosolids from IEA biogas + FAO livestock.</p>
    <h3>CO₂ storage</h3>
    <p>Operational/planned storage projects (Global CCS Institute) plus basin-level capacity (NATCARB,
    CO2StoP, regional atlases), graded by confidence. Proximity distinguishes geologic pathways (BECCS,
    injection) from storage-independent ones (bio-oil, burial, biochar).</p>
    <h3>Best-use recommendation engine</h3>
    <p>A transparent rule set encoding Frontier's KPI ranking — <b>CDR efficiency › emissions-avoiding
    co-product › other co-benefits</b> — modulated by feedstock moisture/density, storage proximity,
    nutrient status, and retrofit availability. Wet wastes → injection or AD+CCS (AD+CCS preferred where
    digesters already exist, e.g. Europe); concentrated woody/dry residues near storage → BECCS; dry
    residues near storage → injection, far → bio-oil; no storage + excess nutrients → burial; concentrated
    MSW → WtE+CCS. <b>Excluded</b> (flagged): purpose-grown energy crops, corn-ethanol+CCS.</p>
    <h3>Caveats</h3>
    <p>Tonnages are modelled estimates, not measured inventories. Storage capacities are theoretical and
    require site appraisal. This tool informs strategy; it does not substitute for project-level diligence.</p>`;

  const US_METHODOLOGY = `
    <h2>Methodology &amp; sources — US county scope</h2>
    <p>Resolves the Atlas to ~3,140 US counties, sharing the global decision engine with inputs computed
    at county granularity.</p>
    <h3>County feedstocks</h3>
    <p>"DOE Billion-Ton state totals, spatially disaggregated to counties." Within-state distribution from
    USDA Census of Agriculture 2022 (crop production × residue ratios for ag; livestock for manure),
    Census population (MSW &amp; biosolids), and county woodland area (forestry), then scaled so each
    state's counties sum to that state's Billion-Ton total. Forestry's county split is a woodland-area
    proxy (weakest layer); ag and manure are highest-confidence.</p>
    <h3>CO₂ storage</h3>
    <p>Storage basins are <b>actual polygons</b> (NETL NATCARB assessed saline formations); a county inside
    a formation has storage on-site, else distance is to the nearest formation boundary / well. Wells:
    operational geologic sequestration (EPA GHGRP Subpart RR), Class VI permits (issued/draft/pending),
    curated Class V biomass-injection / bio-oil (Vaulted, Charm).</p>
    <h3>Point sources &amp; WWTPs</h3>
    <p>Facility-level biogenic CO₂ from EPA GHGRP 2023 (pulp &amp; paper, bioenergy, WtE, landfill gas,
    ethanol); large WWTPs are NPDES "major" POTWs (≥1 MGD) from EPA FRS.</p>
    <h3>County engine</h3>
    <p>Storage access: in-basin = on-site, else distance graded good &lt;100 km / moderate &lt;300 km.
    Density: residue tCO₂/km² + an 80 km haul-radius supply sum. Counties below a minimum recoverable
    supply are flagged "low supply". Distances are great-circle screening, not routed.</p>`;

  const EU_METHODOLOGY = `
    <h2>Methodology &amp; sources — EU NUTS-2 scope</h2>
    <p>Resolves the Atlas to ~290 NUTS-2 regions (EU-27 + UK + Norway), sharing the global decision engine
    with NUTS-2 inputs.</p>
    <h3>Regional feedstocks</h3>
    <p>"JRC ENSPRESO NUTS-2 distribution, scaled to country totals." Within-country distribution from the
    JRC ENSPRESO biomass database (ag residues, forest + secondary-wood residues, manure/biogas); MSW &amp;
    biosolids allocated by NUTS-2 population (Eurostat). Each region is scaled so a country's regions sum
    to that country's total in the global tool. Purpose-grown energy/biofuel crops excluded.</p>
    <h3>CO₂ storage</h3>
    <p>Storage formations are <b>actual polygons</b> from the EU CO2StoP database (JRC) — assessed saline
    aquifer / hydrocarbon-field storage units. Storage projects/hubs (Northern Lights, Porthos, Aramis,
    Greensand, Acorn, Ravenna, Endurance, HyNet, Sleipner, Snøhvit, …) are the European analog of the US
    wells layer. Much EU storage is offshore, so inland regions read "poor" legitimately.</p>
    <h3>Point sources &amp; WWTPs</h3>
    <p>Curated European biogenic-CO₂ facilities (pulp &amp; paper, WtE, bioenergy, biogas/AD) with
    biogenic-CO₂ estimated from capacity (EU ETS zero-rates sustainable biomass — the weakest layer);
    large WWTPs (≥150,000 PE) from the EEA/EMODnet UWWTD.</p>
    <h3>NUTS-2 engine</h3>
    <p>Storage access: in-formation = on-site, else distance graded good &lt;150 km / moderate &lt;400 km
    (wider than US, for offshore-dominant storage). Density: residue tCO₂/km². Manure → AD+CCS in mature-AD
    countries (most of Europe). Distances are great-circle screening, not routed.</p>`;

  const CA_METHODOLOGY = `
    <h2>Methodology &amp; sources — Canada census-division scope</h2>
    <p>Resolves the Atlas to ~290 census divisions (CDs, the Canadian county-equivalent), sharing the
    global decision engine with CD-level inputs.</p>
    <h3>CD feedstocks</h3>
    <p>"Province totals, spatially disaggregated to census divisions." Within-province distribution from the
    StatCan 2021 Census of Agriculture (residue-crop area for ag; cattle/pigs/poultry for manure) and 2021
    Census population (MSW &amp; biosolids), with forestry allocated by CD land area, then scaled so each
    province's CDs sum exactly to that province's total in the global tool. Forestry's CD split is a
    land-area proxy (weakest layer — no CD-level timberland inventory); ag and manure are highest-confidence.</p>
    <h3>CO₂ storage</h3>
    <p>Canada has no NATCARB/CO2StoP-style open polygon atlas, so basins are <b>curated</b> simplified extents
    of the storage fairways that actually host or are appraised for CO₂ — chiefly the Western Canada
    Sedimentary Basin (AB/SK/NE-BC/SW-MB) and the Williston Basin. A CD inside a basin has storage on-site,
    else distance is to the nearest basin boundary / CCS project. The "wells" layer is curated Canadian CCS
    projects &amp; hubs (Quest, ACTL, Aquistore, Boundary Dam, Weyburn, Polaris/Atlas, Pathways, Wabamun, …).</p>
    <h3>Point sources &amp; WWTPs</h3>
    <p>Curated Canadian biogenic-CO₂ facilities (pulp &amp; paper, WtE, fuel-ethanol, biomass energy,
    biogas/AD), seeded from the global tool — ECCC GHGRP does not publish a clean biogenic-CO₂ column;
    large WWTPs are major urban water-resource-recovery plants. Biogenic CO₂ is capacity-estimated (weakest
    layer, like the EU).</p>
    <h3>CD engine</h3>
    <p>Storage access: in-basin = on-site, else distance graded good &lt;100 km / moderate &lt;300 km. Canada's
    appraised storage is concentrated in the prairie WCSB, so biomass-rich but storage-distant BC, Ontario,
    Québec and the Atlantic legitimately read "poor" → bio-oil / biochar / burial, while the prairies enable
    injection / BECCS / AD+CCS. Distances are great-circle screening, not routed.</p>`;

  // ============================================================
  // Init
  // ============================================================
  dom.feedHint.textContent = FEEDSTOCK_HINTS[state.feedstock];
  applyHash();
})();
