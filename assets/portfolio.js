(function(){
  const grid = document.getElementById("portGrid");
  const chips = Array.from(document.querySelectorAll(".chip"));
  if(!grid) return;

  function titleFromFilename(file){
    const name = file.replace(/\.[^/.]+$/, '');
    const cleaned = name
      .replace(/^([a-z]+)(__|-|_)/i,'') // strip category prefix if present
      .replace(/__/g,' ')
      .replace(/[-_]+/g,' ')
      .trim();
    return cleaned ? cleaned.replace(/\b\w/g, c => c.toUpperCase()) : "Proyecto";
  }

  function categoryFromFilename(file){
    const lower = file.toLowerCase();
    const known = ["redes","promo","marca","web","apps","programas","musica"];
    // prefix styles: redes__x.jpg, redes-x.jpg, redes_x.jpg
    const m = lower.match(/^([a-z]+)(?:__|-|_)/);
    if(m && known.includes(m[1])) return m[1];
    return "all";
  }

  function placeholderCard(idx){
    const el = document.createElement("div");
    el.className = "work reveal";
    el.dataset.cat = "all";
    el.innerHTML = `
      <img src="assets/portfolio/placeholder-${idx}.jpg" alt="Agrega imágenes" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22600%22 height=%22400%22><rect width=%22100%25%22 height=%22100%25%22 fill=%22%230b0b0b%22/><text x=%2250%25%22 y=%2250%25%22 fill=%22%23cfcfcf%22 font-family=%22Arial%22 font-size=%2220%22 text-anchor=%22middle%22>Agrega imágenes en assets/portfolio</text></svg>'">
      <div class="meta">
        <div class="title"><strong>Tu portafolio aquí</strong><span>Agrega .jpg/.png/.webp</span></div>
        <div class="tag">Portfolio</div>
      </div>
    `;
    return el;
  }

  function render(items){
    grid.innerHTML = "";
    if(!items.length){
      // show 6 placeholders
      for(let i=1;i<=6;i++) grid.appendChild(placeholderCard(i));
      // re-observe reveals if app.js loaded
      setTimeout(()=> document.querySelectorAll('.reveal').forEach(el=> el.classList.add('on')), 60);
      return;
    }

    items.forEach(it=>{
      const file = it.file || it;
      const src = `assets/portfolio/${file}`;
      const cat = (it.category && it.category !== "all") ? it.category : categoryFromFilename(file);
      const t = it.title || titleFromFilename(file);

      const el = document.createElement("div");
      el.className = "work reveal";
      el.dataset.cat = cat;
      el.dataset.full = src;
      el.innerHTML = `
        <img src="${src}" alt="${t}">
        <div class="meta">
          <div class="title"><strong>${t}</strong><span>${cat.toUpperCase()}</span></div>
          <div class="tag">${cat.toUpperCase()}</div>
        </div>
      `;
      el.addEventListener("click", ()=> window.EV_openModal?.(src));
      grid.appendChild(el);
    });

    // reveal immediate if observer already done
    setTimeout(()=> document.querySelectorAll('.reveal').forEach(el=> el.classList.add('on')), 60);
  }

  async function load(){
    try{
      const r = await fetch("assets/portfolio.manifest.json", { cache: "no-store" });
      if(!r.ok) throw new Error("manifest missing");
      const j = await r.json();
      const items = Array.isArray(j) ? j : (j.items || []);
      render(items);
    }catch(e){
      render([]);
    }
  }

  // Filter chips
  chips.forEach(ch => ch.addEventListener('click', ()=>{
    chips.forEach(c => c.classList.remove('active'));
    ch.classList.add('active');
    const f = ch.dataset.filter;
    Array.from(grid.children).forEach(w=>{
      const cat = w.dataset.cat;
      const show = (f === 'all') || (cat === f) || (f === 'portfolio' && cat === 'all');
      w.style.display = show ? '' : 'none';
    });
  }));

  load();
})();
