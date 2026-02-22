/**
 * EJE VISUAL — VR Museo Premium Futurista (ALL FEATURES)
 * - Rooms by category (corridor zones) + teleport pads
 * - Pop-out selection (frame pops + central pop plane)
 * - Category ambience color shift
 * - Dedicated follow spotlight
 * - 3D ticker headlines (local via Google News RSS)
 * - Reels poster gallery (vertical frames)
 * - Procedural ambient audio (hum) + whoosh on category change
 * - Auto tour mode (toggle)
 *
 * Requires: A-Frame 1.5.0, assets/sfx.js
 */

const MANIFEST_URL = "assets/portfolio.manifest.json";

const CATS = [
  { key: "all",    label: "TODO",   color: "#00FFD0", z:  6.2 },
  { key: "redes",  label: "REDES",  color: "#00E5FF", z: -6.0 },
  { key: "promo",  label: "PROMO",  color: "#FF2BD6", z: -18.0 },
  { key: "marca",  label: "MARCA",  color: "#FFD166", z: -30.0 },
  { key: "web",    label: "WEB",    color: "#3A86FF", z: -42.0 },
  { key: "musica", label: "MÚSICA", color: "#25D366", z: -54.0 },
];

let current = "all";
let itemsAll = [];
let selectedFrame = null;
let selectedRestore = null;

// ===== Helpers
const $ = (id)=> document.getElementById(id);
const catInfo = (k)=> CATS.find(c=>c.key===k) || CATS[0];

function safeSetText(id, val){
  const el = $(id);
  if(el) el.setAttribute("value", val);
}

function setEmissive(el, color, dur=1000){
  if(!el) return;
  el.setAttribute("animation__em", `property: material.emissive; to: ${color}; dur: ${dur}; easing: easeInOutSine;`);
}

function setLightColor(el, color, dur=1100){
  if(!el) return;
  el.setAttribute("animation__col", `property: light.color; to: ${color}; dur: ${dur}; easing: easeInOutSine;`);
}

function setLightIntensity(el, val, dur=900){
  if(!el) return;
  el.setAttribute("animation__int", `property: light.intensity; to: ${val}; dur: ${dur}; easing: easeInOutSine;`);
}

function lerp(a,b,t){ return a + (b-a)*t; }

// ===== Procedural audio (ambient + whoosh)
let audioCtx = null;
let humGain = null;
let humOsc1 = null;
let humOsc2 = null;
let audioEnabled = false;

function getAudio(){
  if(audioCtx) return audioCtx;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  return audioCtx;
}

function startHum(){
  if(audioEnabled) return;
  audioEnabled = true;
  const ctx = getAudio();

  humGain = ctx.createGain();
  humGain.gain.value = 0.0;
  humGain.connect(ctx.destination);

  humOsc1 = ctx.createOscillator();
  humOsc1.type = "sine";
  humOsc1.frequency.value = 55;

  humOsc2 = ctx.createOscillator();
  humOsc2.type = "triangle";
  humOsc2.frequency.value = 110;

  const g1 = ctx.createGain(); g1.gain.value = 0.015;
  const g2 = ctx.createGain(); g2.gain.value = 0.010;

  humOsc1.connect(g1); g1.connect(humGain);
  humOsc2.connect(g2); g2.connect(humGain);

  const t = ctx.currentTime;
  humGain.gain.linearRampToValueAtTime(0.022, t + 1.2);

  humOsc1.start();
  humOsc2.start();

  // subtle drift
  setInterval(()=>{
    if(!audioCtx) return;
    humOsc1.frequency.value = 55 + (Math.random()*1.2-0.6);
    humOsc2.frequency.value = 110 + (Math.random()*1.8-0.9);
  }, 1800);
}

function whoosh(){
  try{
    const ctx = getAudio();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sawtooth";
    o.frequency.value = 240;
    g.gain.value = 0.0001;
    o.connect(g); g.connect(ctx.destination);
    const t = ctx.currentTime;
    o.frequency.exponentialRampToValueAtTime(820, t + 0.14);
    g.gain.exponentialRampToValueAtTime(0.028, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
    o.start(t);
    o.stop(t + 0.22);
  }catch(e){}
}

// Arm audio after first user interaction (browser policy)
window.addEventListener("pointerdown", ()=>{
  try{ getAudio().resume(); }catch(e){}
  startHum();
},{ once:true });

// ===== Local headlines fetch (Google News RSS)
async function tryFetchText(url){
  // Direct
  try{
    const r = await fetch(url, { cache:'no-store' });
    if(r.ok) return await r.text();
  }catch(e){}
  // allorigins
  try{
    const proxy = "https://api.allorigins.win/raw?url=" + encodeURIComponent(url);
    const r2 = await fetch(proxy, { cache:'no-store' });
    if(r2.ok) return await r2.text();
  }catch(e){}
  // jina.ai
  try{
    const prox3 = "https://r.jina.ai/https://" + url.replace(/^https?:\/\//,'');
    const r3 = await fetch(prox3, { cache:'no-store' });
    if(r3.ok) return await r3.text();
  }catch(e){}
  throw new Error("No fetch");
}

async function getLocation(){
  try{
    const r = await fetch("https://ipapi.co/json/", { cache: "no-store" });
    if(!r.ok) throw new Error("ipapi");
    const j = await r.json();
    return {
      city: j.city || "",
      region: j.region || j.region_code || "",
      country: j.country_code || "US"
    };
  }catch(e){
    // fallback
    return { city: "", region: "", country: "US" };
  }
}

function editionFor(country, lang){
  const gl = (country || "US").toUpperCase();
  const hl = lang === "es" ? "es-419" : "en-US";
  const ceidLang = lang === "es" ? "es-419" : "en";
  return { gl, hl, ceid: `${gl}:${ceidLang}` };
}

function parseRSS(xmlText){
  const doc = new DOMParser().parseFromString(xmlText, "text/xml");
  return Array.from(doc.querySelectorAll("item")).slice(0, 10).map(it=>{
    const title = (it.querySelector("title")?.textContent || "").trim();
    const pub = (it.querySelector("pubDate")?.textContent || "").trim();
    return { title, pub };
  }).filter(x=>x.title);
}

async function loadHeadlines(){
  const navLang = (navigator.language || "en").toLowerCase();
  const lang = navLang.startsWith("es") ? "es" : "en";
  const loc = await getLocation();
  const { gl, hl, ceid } = editionFor(loc.country, lang);
  const city = (loc.city || "").trim();
  const region = (loc.region || "").trim();

  const query = city
    ? (lang === "es" ? `${city} ${region} noticias when:3d` : `${city} ${region} news when:3d`)
    : (lang === "es" ? `noticias locales when:3d` : `local news when:3d`);

  const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=${encodeURIComponent(hl)}&gl=${encodeURIComponent(gl)}&ceid=${encodeURIComponent(ceid)}`;

  try{
    const xml = await tryFetchText(url);
    const items = parseRSS(xml);
    const text = items.map(x=>x.title).slice(0, 8).join("  •  ");
    safeSetText("newsText", text || "Headlines no disponibles.");
    safeSetText("newsTag", city ? city.toUpperCase() : gl);
  }catch(e){
    safeSetText("newsText", "Headlines no disponibles.");
    safeSetText("newsTag", "LOCAL");
  }
}

// ===== Build the museum rooms
async function loadManifest(){
  const r = await fetch(MANIFEST_URL, { cache: "no-store" });
  if(!r.ok) throw new Error("manifest missing");
  const j = await r.json();
  return Array.isArray(j) ? j : (j.items || []);
}

function clearContainer(el){
  if(!el) return;
  while(el.firstChild) el.removeChild(el.firstChild);
}

function makeFrame(parent, {src, title, tag, x, y, z, rotY, accent}){
  const g = document.createElement("a-entity");
  g.setAttribute("position", `${x} ${y} ${z}`);
  g.setAttribute("rotation", `0 ${rotY} 0`);

  const frame = document.createElement("a-box");
  frame.setAttribute("depth", "0.08");
  frame.setAttribute("height", "1.72");
  frame.setAttribute("width", "2.22");
  frame.setAttribute("material", "color:#0d0d0d; metalness:0.28; roughness:0.55; emissive:#050505; emissiveIntensity:0.22;");
  g.appendChild(frame);

  const led = document.createElement("a-plane");
  led.setAttribute("width", "2.24");
  led.setAttribute("height", "1.74");
  led.setAttribute("position", "0 0 0.041");
  led.setAttribute("material", `color:#0f0f0f; emissive:${accent}; emissiveIntensity:0.28; opacity: 1; transparent:false;`);
  led.setAttribute("animation__spin", "property: rotation; dur: 28000; loop: true; to: 0 0 360; easing: linear;");
  g.appendChild(led);

  const plate = document.createElement("a-box");
  plate.setAttribute("depth", "0.04");
  plate.setAttribute("height", "1.58");
  plate.setAttribute("width", "2.08");
  plate.setAttribute("position", "0 0 0.045");
  plate.setAttribute("material", "color:#0a0a0a; metalness:0.06; roughness:0.95;");
  g.appendChild(plate);

  const img = document.createElement("a-plane");
  img.setAttribute("width", "1.98");
  img.setAttribute("height", "1.24");
  img.setAttribute("position", "0 0.14 0.070");
  img.setAttribute("material", `src: url(${src}); color: #fff; metalness:0; roughness:1;`);
  g.appendChild(img);

  // Premium plaque (brushed metal feel)
  const plaque = document.createElement("a-entity");
  plaque.setAttribute("position", "0 -0.74 0.073");

  const plaqueBg = document.createElement("a-plane");
  plaqueBg.setAttribute("width", "2.08");
  plaqueBg.setAttribute("height", "0.23");
  plaqueBg.setAttribute("material", "color:#111; metalness:0.65; roughness:0.35; emissive:#111; emissiveIntensity:0.10;");
  plaque.appendChild(plaqueBg);

  const t = document.createElement("a-text");
  t.setAttribute("value", title || "Proyecto");
  t.setAttribute("position", "-1.00 -0.07 0.01");
  t.setAttribute("width", "2.4");
  t.setAttribute("color", "#f2f2f2");
  t.setAttribute("font", "https://cdn.aframe.io/fonts/DejaVu-sdf.fnt");
  t.setAttribute("baseline", "center");
  t.setAttribute("wrap-count", "30");
  plaque.appendChild(t);

  const tagTx = document.createElement("a-text");
  tagTx.setAttribute("value", (tag || "PORTFOLIO").toUpperCase());
  tagTx.setAttribute("position", "0.62 -0.07 0.01");
  tagTx.setAttribute("width", "1.1");
  tagTx.setAttribute("color", "#b0b0b0");
  tagTx.setAttribute("font", "https://cdn.aframe.io/fonts/DejaVu-sdf.fnt");
  tagTx.setAttribute("baseline", "center");
  tagTx.setAttribute("wrap-count", "10");
  plaque.appendChild(tagTx);

  g.appendChild(plaque);

  g.classList.add("clickable");

  // Hover LED
  g.addEventListener("mouseenter", ()=>{
    led.setAttribute("animation__int", "property: material.emissiveIntensity; dur: 520; to: 0.92; easing: easeOutQuad;");
  });
  g.addEventListener("mouseleave", ()=>{
    led.setAttribute("animation__int", "property: material.emissiveIntensity; dur: 900; to: 0.28; easing: easeInOutSine;");
  });

  // Click: pop-out + spotlight focus
  g.addEventListener("click", ()=>{
    focusOnFrame(g, {src, title, accent});
    if(window.EV_SFX && window.EV_SFX.click) window.EV_SFX.click();
  });

  parent.appendChild(g);
  return g;
}

function makeReel(parent, {src, title, x, y, z, rotY, accent}){
  // Vertical poster frame (9:16)
  const g = document.createElement("a-entity");
  g.setAttribute("position", `${x} ${y} ${z}`);
  g.setAttribute("rotation", `0 ${rotY} 0`);
  g.classList.add("clickable");

  const frame = document.createElement("a-box");
  frame.setAttribute("depth","0.06");
  frame.setAttribute("height","1.90");
  frame.setAttribute("width","1.10");
  frame.setAttribute("material","color:#0d0d0d; metalness:0.22; roughness:0.6; emissive:#050505; emissiveIntensity:0.18;");
  g.appendChild(frame);

  const led = document.createElement("a-plane");
  led.setAttribute("width","1.12");
  led.setAttribute("height","1.92");
  led.setAttribute("position","0 0 0.032");
  led.setAttribute("material", `color:#0f0f0f; emissive:${accent}; emissiveIntensity:0.22; transparent:false;`);
  led.setAttribute("animation__spin","property: rotation; dur: 34000; loop: true; to: 0 0 360; easing: linear;");
  g.appendChild(led);

  const img = document.createElement("a-plane");
  img.setAttribute("width","1.02");
  img.setAttribute("height","1.72");
  img.setAttribute("position","0 0 0.050");
  img.setAttribute("material", `src: url(${src}); color:#fff; metalness:0; roughness:1;`);
  g.appendChild(img);

  g.addEventListener("mouseenter", ()=> led.setAttribute("animation__int", "property: material.emissiveIntensity; dur: 520; to: 0.80; easing: easeOutQuad;"));
  g.addEventListener("mouseleave", ()=> led.setAttribute("animation__int", "property: material.emissiveIntensity; dur: 900; to: 0.22; easing: easeInOutSine;"));
  g.addEventListener("click", ()=> focusOnFrame(g, {src, title, accent}));

  parent.appendChild(g);
  return g;
}

// ===== Spotlight follow
let focusTarget = null;
let followSpot = null;

function ensureSpotSystem(){
  focusTarget = $("focusTarget");
  followSpot = $("followSpot");
}

function setTargetWorldPosition(obj3D){
  if(!focusTarget || !obj3D) return;
  // Get world position
  const v = new THREE.Vector3();
  obj3D.getWorldPosition(v);
  focusTarget.object3D.position.copy(v);
}

function aimSpot(){
  if(!followSpot || !focusTarget) return;
  const s = followSpot.object3D;
  const t = focusTarget.object3D.position;
  s.lookAt(t);
}

function focusOnFrame(frameEntity, {src, title, accent}){
  ensureSpotSystem();

  // restore previous frame
  if(selectedFrame && selectedRestore){
    selectedFrame.object3D.position.copy(selectedRestore.pos);
    selectedFrame.object3D.rotation.copy(selectedRestore.rot);
    selectedFrame.object3D.scale.copy(selectedRestore.scale);
  }

  selectedFrame = frameEntity;
  selectedRestore = {
    pos: frameEntity.object3D.position.clone(),
    rot: frameEntity.object3D.rotation.clone(),
    scale: frameEntity.object3D.scale.clone()
  };

  // Pop-out effect: push slightly out from wall, scale up a bit
  const dir = new THREE.Vector3(0,0,1);
  frameEntity.object3D.localToWorld(dir.set(0,0,1));
  // simpler: move along local z
  frameEntity.setAttribute("animation__popPos", "property: position; dur: 650; to: 0 0 0;"); // dummy to clear
  const p = selectedRestore.pos;
  const toPos = `${p.x} ${p.y} ${p.z + 0.22}`;
  frameEntity.setAttribute("animation__popPos", `property: position; dur: 650; easing: easeOutQuad; to: ${toPos};`);
  frameEntity.setAttribute("animation__popScale", "property: scale; dur: 650; easing: easeOutQuad; to: 1.06 1.06 1.06;");

  // Central preview pop plane
  const pop = $("popPlane");
  const popT = $("popTitle");
  if(pop){
    pop.setAttribute("visible", "true");
    pop.setAttribute("material", `src: url(${src}); color:#fff; metalness:0; roughness:1;`);
    pop.setAttribute("animation__in", "property: scale; dur: 520; easing: easeOutQuad; from: 0.85 0.85 0.85; to: 1 1 1;");
  }
  if(popT){
    popT.setAttribute("value", title || "Proyecto");
  }

  // Update main preview too
  const pv = $("previewPlane");
  if(pv){
    pv.setAttribute("material", `src: url(${src}); color:#fff; metalness:0; roughness:1;`);
  }
  safeSetText("previewTitle", title || "Proyecto");
  safeSetText("hint", "Seleccionado. Cambia categoría o teletranspórtate por el museo.");

  // Move spotlight target to selected frame
  setTargetWorldPosition(frameEntity.object3D);
  setLightIntensity($("followSpot"), 1.15, 650);

  // small accent flash
  const ceiling = $("ceilingRing");
  if(ceiling) ceiling.setAttribute("animation__flash", `property: material.emissiveIntensity; dur: 420; dir: alternate; loop: 1; to: 0.85; easing: easeInOutSine;`);

  // subtle whoosh
  whoosh();
}

// Tick: keep spotlight aimed
function tick(){
  aimSpot();
  requestAnimationFrame(tick);
}

// ===== Teleport pads + tour
function teleportTo(catKey){
  const rig = $("rig");
  const c = catInfo(catKey);
  if(!rig) return;
  // Keep y at 0, z to room, x 0
  rig.setAttribute("animation__tp", `property: position; dur: 900; easing: easeInOutSine; to: 0 0 ${c.z};`);
  current = catKey;
  applyTheme(catKey);
  safeSetText("hint", `Sala: ${c.label}.`);
  whoosh();
}

let tourOn = false;
let tourStep = 0;
let tourTimer = null;

function startTour(){
  if(tourOn) return;
  tourOn = true;
  tourStep = 0;
  safeSetText("tourLabel", "TOUR: ON");

  const path = ["all","redes","promo","marca","web","musica","all"];
  const go = ()=>{
    if(!tourOn) return;
    teleportTo(path[tourStep % path.length]);
    tourStep++;
    tourTimer = setTimeout(go, 8500); // linger
  };
  go();
}

function stopTour(){
  tourOn = false;
  safeSetText("tourLabel", "TOUR: OFF");
  if(tourTimer) clearTimeout(tourTimer);
  tourTimer = null;
}

// ===== Theme apply: change strips, ceiling ring, subtle ambient
function applyTheme(catKey){
  const c = catInfo(catKey).color;

  safeSetText("catLabel", catInfo(catKey).label);

  setEmissive($("ceilingRing"), c, 1100);
  setEmissive($("stripL"), c, 1100);
  setEmissive($("stripR"), c, 1100);

  setLightColor($("ambientLight"), c, 1400);
  setLightIntensity($("ambientLight"), 0.60, 1400);

  // console accent
  setEmissive($("consoleAccent"), c, 1100);
}

// ===== Build all rooms once
function buildRooms(){
  // Containers per cat
  CATS.forEach(c=>{
    const container = $(`room_${c.key}`);
    clearContainer(container);

    const filtered = c.key === "all"
      ? itemsAll
      : itemsAll.filter(it => (it.category || "all").toLowerCase() === c.key);

    const show = filtered.slice(0, 14);
    const wallX = 5.35;
    const y = 1.75;
    const startZ = c.z - 1.0; // near each room center
    const stepZ = 2.55;

    let row = 0;
    for(let i=0;i<show.length;i++){
      const it = show[i];
      const file = it.file || it;
      const cat = (it.category || "all").toLowerCase();
      const title = it.title || (file || "Proyecto").replace(/\.[^/.]+$/, "");
      const sideLeft = (i % 2 === 0);
      const x = sideLeft ? -wallX : wallX;
      const z = startZ - row * stepZ;
      const rotY = sideLeft ? -90 : 90;

      makeFrame(container, {
        src: `assets/portfolio/${file}`,
        title,
        tag: cat === "all" ? "PORTFOLIO" : cat,
        x: x.toFixed(2), y: y.toFixed(2), z: z.toFixed(2),
        rotY,
        accent: c.color
      });

      if(!sideLeft) row += 1;
    }

    // Reels posters (vertical), 4 per room
    const reels = $(`reels_${c.key}`);
    clearContainer(reels);
    const reelZ = c.z - 3.0;
    const rx = 2.2;
    const ry = 1.8;
    for(let j=0;j<4;j++){
      const it = show[j % Math.max(1, show.length)] || show[0];
      if(!it) continue;
      const file = it.file || it;
      const title = (it.title || "Poster").slice(0, 28);
      // place on back wall facing forward
      makeReel(reels, {
        src: `assets/portfolio/${file}`,
        title,
        x: (-1.65 + j*1.1).toFixed(2),
        y: ry.toFixed(2),
        z: (reelZ - 8.5).toFixed(2),
        rotY: 180,
        accent: c.color
      });
    }
  });
}

// ===== Bind UI
function bindUI(){
  // Category buttons
  CATS.forEach(c=>{
    const btn = $(`cat_${c.key}`);
    if(!btn) return;
    btn.classList.add("clickable");
    btn.addEventListener("click", ()=>{
      teleportTo(c.key);
      if(window.EV_SFX && window.EV_SFX.menu) window.EV_SFX.menu();
    });
  });

  // Teleport pads (floor)
  CATS.forEach(c=>{
    const pad = $(`pad_${c.key}`);
    if(!pad) return;
    pad.classList.add("clickable");
    pad.addEventListener("click", ()=>{
      teleportTo(c.key);
      if(window.EV_SFX && window.EV_SFX.menu) window.EV_SFX.menu();
    });
  });

  // Back to site
  const back = $("backToSite");
  if(back){
    back.classList.add("clickable");
    back.addEventListener("click", ()=> {
      if(window.EV_SFX && window.EV_SFX.menu) window.EV_SFX.menu();
      window.location.href = "index.html";
    });
  }

  // WhatsApp
  const wa = $("waBtn");
  if(wa){
    wa.classList.add("clickable");
    wa.addEventListener("click", ()=> {
      if(window.EV_SFX && window.EV_SFX.click) window.EV_SFX.click();
      window.open("https://wa.me/526633220567", "_blank");
    });
  }

  // Tour toggle
  const tour = $("tourBtn");
  if(tour){
    tour.classList.add("clickable");
    tour.addEventListener("click", ()=>{
      if(tourOn) stopTour();
      else startTour();
      if(window.EV_SFX && window.EV_SFX.menu) window.EV_SFX.menu();
    });
  }
}

// ===== Init
async function init(){
  ensureSpotSystem();
  try{
    itemsAll = await loadManifest();
    buildRooms();
    bindUI();

    // Headline ribbon
    loadHeadlines();
    setInterval(loadHeadlines, 15*60*1000);

    applyTheme("all");
    safeSetText("hint", "Tip: Usa los pads del piso o la consola para moverte por salas.");
    tick();
  }catch(e){
    safeSetText("hint", "No se pudo cargar el portafolio. Abre con servidor local (no file://).");
    console.warn(e);
  }
}

window.addEventListener("DOMContentLoaded", init);
