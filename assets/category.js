(function(){
  const grid = document.getElementById("portGrid");
  if(!grid) return;

  const params = new URLSearchParams(window.location.search);
  const urlCat = (params.get("cat") || "").toLowerCase();
  const pageCat = (grid.dataset.category || "all").toLowerCase();
  const effectiveCat = (pageCat === "all" && urlCat) ? urlCat : pageCat;
  const showFilters = grid.dataset.filters === "true";
  const chips = Array.from(document.querySelectorAll(".chip"));

  function EV_setActiveChip(val){
    const v = (val || 'all').toLowerCase();
    chips.forEach(c=> c.classList.toggle('active', (c.dataset.filter||'').toLowerCase() === v));
  }

  function EV_applyFilter(val){
    const f = (val || 'all').toLowerCase();
    Array.from(grid.children).forEach(w=>{
      const cat = (w.dataset.cat || 'all').toLowerCase();
      w.style.display = (f === 'all' || cat === f) ? '' : 'none';
    });
  }

  function EV_updateUrl(cat){
    const c = (cat || 'all').toLowerCase();
    const url = new URL(window.location.href);
    if(c === 'all') url.searchParams.delete('cat');
    else url.searchParams.set('cat', c);
    // keep hash stable
    history.replaceState({}, '', url.toString());
  }

  function EV_bindChips(){
    if(!showFilters || !chips.length) return;
    chips.forEach(ch=>{
      ch.addEventListener('click', (e)=>{
        // allow normal navigation if modifier key
        if(e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        const f = (ch.dataset.filter || 'all').toLowerCase();
        EV_setActiveChip(f);
        EV_applyFilter(f);
        EV_updateUrl(f);
      });
    });
  }


  function renderPlaceholders(){
    grid.innerHTML = "";
    for(let i=1;i<=8;i++){
      const el = document.createElement("div");
      el.className = "work reveal";
      el.dataset.cat = pageCat;
      el.innerHTML = `
        <img src="assets/portfolio/placeholder-${i}.jpg" alt="Agrega imágenes" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22600%22 height=%22400%22><rect width=%22100%25%22 height=%22100%25%22 fill=%22%230b0b0b%22/><text x=%2250%25%22 y=%2250%25%22 fill=%22%23cfcfcf%22 font-family=%22Arial%22 font-size=%2220%22 text-anchor=%22middle%22>Agrega imágenes en assets/portfolio</text></svg>'">
        <div class="meta">
          <div class="title"><strong>Tu portafolio aquí</strong><span>${pageCat.toUpperCase()}</span></div>
          <div class="tag">${pageCat.toUpperCase()}</div>
        </div>
      `;
      grid.appendChild(el);
    }
    EV_forceReveal();

    // Initial filter by ?cat=
    if(showFilters && urlCat){
      const target = chips.find(c=> (c.dataset.filter||"").toLowerCase() === urlCat);
      if(target){
        chips.forEach(c=>c.classList.remove("active"));
        target.classList.add("active");
        const f = urlCat;
        Array.from(grid.children).forEach(w=>{
          const cat = (w.dataset.cat || "all").toLowerCase();
          w.style.display = (f === "all" || cat === f) ? "" : "none";
        });
      }
    }
  }

  async function load(){
    const { items, meta } = await EV_loadPortfolioData();

    let list = items.map(it => ({
      file: it.file || it,
      category: (it.category && it.category !== "all") ? it.category : EV_categoryFromFilename(it.file || it),
      title: it.title || EV_titleFromFilename(it.file || it)
    }));

    // merge metadata by filename
    list = list.map(x=>{
      const m = meta[x.file];
      if(!m) return x;
      return {
        ...x,
        title: m.title || x.title,
        meta: m
      };
    });

    if(effectiveCat !== "all"){
      list = list.filter(x => (x.category || "all") === effectiveCat);
    }

    if(!list.length){
      // Set chip active from URL, if any
      if(showFilters && urlCat){
        const target = chips.find(c=> (c.dataset.filter||"").toLowerCase() === urlCat);
        if(target){
          chips.forEach(c=>c.classList.remove("active"));
          target.classList.add("active");
        }
      }
      renderPlaceholders();
      return;
    }

    grid.innerHTML = "";
    list.forEach(x=>{
      const src = `assets/portfolio/${x.file}`;
      const m = x.meta || {};
      const metaTextParts = [];
      if(m.client) metaTextParts.push(m.client);
      if(m.service) metaTextParts.push(m.service);
      if(m.year) metaTextParts.push(String(m.year));
      const metaText = metaTextParts.join(" · ");
      grid.appendChild(EV_buildCard({
        src,
        title: x.title,
        cat: x.category,
        metaText,
        url: m.url || ""
      }));
    });

    EV_forceReveal();

    // Initial filter by ?cat=
    if(showFilters && urlCat){
      const target = chips.find(c=> (c.dataset.filter||"").toLowerCase() === urlCat);
      if(target){
        chips.forEach(c=>c.classList.remove("active"));
        target.classList.add("active");
        const f = urlCat;
        Array.from(grid.children).forEach(w=>{
          const cat = (w.dataset.cat || "all").toLowerCase();
          w.style.display = (f === "all" || cat === f) ? "" : "none";
        });
      }
    }

    
    // Bind chips (fallback links + JS filter)
    EV_bindChips();

    // Apply initial filter from ?cat=
    if(showFilters && urlCat){
      EV_setActiveChip(urlCat);
      EV_applyFilter(urlCat);
    }
  }

  load();
})();
