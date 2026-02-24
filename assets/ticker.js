(function(){
  const tTrack = document.getElementById("tTrack");
  const btnES = document.getElementById("btnES");
  const btnEN = document.getElementById("btnEN");
  const btnRef = document.getElementById("btnRef");
  if(!tTrack) return;
  // ===== EJE VISUAL Ticker Config (patched by Portfolio Manager) =====
  const EV_TICKER_CONFIG_URL = "assets/ticker.config.json";
  let EV_CFG = { mode: "auto", custom_rss_url: "", speed_seconds: 55 };

  async function EV_loadCfg(){
    try{
      const r = await fetch(EV_TICKER_CONFIG_URL, { cache: "no-store" });
      if(r.ok){
        const j = await r.json();
        EV_CFG = Object.assign(EV_CFG, j || {});
      }
    }catch(e){}
  }


  // Choose language defaults from browser
  const navLang = (navigator.language || "en").toLowerCase();
  let lang = navLang.startsWith("es") ? "es" : "en";

  // Basic edition mapping
  function editionFor(country, lang){
    const gl = (country || "US").toUpperCase();
    const hl = lang === "es" ? "es-419" : "en-US";
    const ceidLang = lang === "es" ? "es-419" : "en";
    return { gl, hl, ceid: `${gl}:${ceidLang}` };
  }

  // Try to get user's approximate location (IP-based, no key)
  async function getLocation(){
    try{
      const r = await fetch("https://ipapi.co/json/", { cache: "no-store" });
      if(!r.ok) throw new Error("ipapi");
      const j = await r.json();
      return {
        city: j.city || "",
        region: j.region || j.region_code || "",
        country: j.country_code || ""
      };
    }catch(e){
      // fallback: timezone -> country rough
      const tz = (Intl.DateTimeFormat().resolvedOptions().timeZone || "").toLowerCase();
      if(tz.includes("mexico") || tz.includes("tijuana")) return { city:"Tijuana", region:"BC", country:"MX" };
      if(tz.includes("los_angeles") || tz.includes("san_diego")) return { city:"San Diego", region:"CA", country:"US" };
      return { city:"", region:"", country:"US" };
    }
  }

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

  function parseRSS(xmlText){
    const doc = new DOMParser().parseFromString(xmlText, "text/xml");
    return Array.from(doc.querySelectorAll("item")).slice(0, 12).map(it=>{
      const title = (it.querySelector("title")?.textContent || "").trim();
      const link = (it.querySelector("link")?.textContent || "").trim();
      const pub = (it.querySelector("pubDate")?.textContent || "").trim();
      const source = (it.querySelector("source")?.textContent || "").trim();
      return { title, link, pub, source };
    }).filter(x=>x.title && x.link);
  }

  function formatDate(pub){
    if(!pub) return "";
    const d = new Date(pub);
    if(isNaN(d.getTime())) return "";
    const df = new Intl.DateTimeFormat(lang === "es" ? "es-MX" : "en-US", {
      month: "short",
      day: "2-digit"
    });
    return df.format(d);
  }

  function setTickerSpeed(itemCount){
    const base = Number((EV_CFG && EV_CFG.speed_seconds) || 44);
    const add = Math.min(40, Math.max(0, itemCount - 10) * 1.8);
    tTrack.style.animationDuration = (base + add) + "s";
  }

  function render(items, label){
    if(!items.length){
      tTrack.innerHTML = `<span style="padding-left:18px; color:rgba(255,255,255,.72); font-size:12px;">
        No se pudieron cargar titulares. Da click en ↻.
      </span>`;
      tTrack.style.animationDuration = "0s";
      return;
    }

    const html = items.map(it=>{
      const d = formatDate(it.pub);
      const src = it.source || "Google News";
      const meta = d ? `${src} · ${d}` : src;
      return `<a class="tItem" href="${it.link}" target="_blank" rel="noopener">
        <span style="font-weight:900; letter-spacing:.08em;">[${label}]</span>
        <span>${it.title}</span>
        <span class="tMeta">— ${meta}</span>
      </a>`;
    }).join("");

    tTrack.innerHTML = html + html;
    setTickerSpeed(items.length);
  }

  async function load(){
    await EV_loadCfg();
tTrack.innerHTML = `<span style="padding-left:18px; color:rgba(255,255,255,.70); font-size:12px;">Cargando titulares…</span>`;

    const loc = await getLocation();
    const { gl, hl, ceid } = editionFor(loc.country || "US", lang);

    // Build a "local headlines" query. Use last 3 days for recency.
    const city = (loc.city || "").trim();
    const region = (loc.region || "").trim();
    const qLocal = lang === "es"
      ? `${city} ${region} noticias when:3d`
      : `${city} ${region} news when:3d`;

    const query = city ? qLocal : (lang === "es" ? "noticias locales when:3d" : "local news when:3d");
    const label = city ? city.toUpperCase() : (gl || "LOCAL");

    const autoUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=${encodeURIComponent(hl)}&gl=${encodeURIComponent(gl)}&ceid=${encodeURIComponent(ceid)}`;

    const url = (EV_CFG.mode === "custom" && EV_CFG.custom_rss_url)
      ? EV_CFG.custom_rss_url
      : autoUrl;


    try{
      const xml = await tryFetchText(url);
      const items = parseRSS(xml);
      render(items, label);
    }catch(e){
      render([], label);
    }
  }

  function setLang(next){
    lang = next;
    btnES?.classList.toggle("on", lang === "es");
    btnEN?.classList.toggle("on", lang === "en");
    load();
  }

  btnES?.addEventListener("click", ()=> setLang("es"));
  btnEN?.addEventListener("click", ()=> setLang("en"));
  btnRef?.addEventListener("click", load);

  // Initial
  setLang(lang);
  setInterval(load, 15 * 60 * 1000);
})();
