(function(){
  const root = document.documentElement;

  // ========= 1) Cursor Reveal Background (no assets) =========
  // Uses CSS variables --mx/--my and a backdrop layer that reveals a subtle pattern under cursor.
  function onMove(e){
    const x = (e.clientX / window.innerWidth) * 100;
    const y = (e.clientY / window.innerHeight) * 100;
    root.style.setProperty('--mx', x.toFixed(2) + '%');
    root.style.setProperty('--my', y.toFixed(2) + '%');
  }
  window.addEventListener('pointermove', onMove, { passive:true });

  // ========= 2) 3D Tilt Mockups =========
  const tiltEls = document.querySelectorAll('[data-tilt]');
  tiltEls.forEach(el=>{
    const strength = Number(el.getAttribute('data-tilt')) || 10;
    const glare = el.querySelector('.glare');
    function move(ev){
      const r = el.getBoundingClientRect();
      const px = (ev.clientX - r.left) / r.width;   // 0..1
      const py = (ev.clientY - r.top) / r.height;  // 0..1
      const rx = (py - 0.5) * -strength;
      const ry = (px - 0.5) * strength;
      el.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) translateZ(0)`;
      if(glare){
        glare.style.opacity = '1';
        glare.style.transform = `translate(${(px*40-20).toFixed(1)}px, ${(py*40-20).toFixed(1)}px)`;
      }
    }
    function leave(){
      el.style.transform = '';
      if(glare){ glare.style.opacity = '0'; glare.style.transform = ''; }
    }
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerleave', leave);
  });

  // ========= 3) Vector Animation (SVG) =========
  // Animate strokes when element enters viewport.
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(ent=>{
      if(!ent.isIntersecting) return;
      ent.target.classList.add('draw-on');
      io.unobserve(ent.target);
    });
  }, { threshold: 0.35 });

  document.querySelectorAll('.vec-draw').forEach(svg=>{
    // Prep paths
    svg.querySelectorAll('path, line, polyline, polygon, circle, rect').forEach(p=>{
      try{
        const len = p.getTotalLength ? p.getTotalLength() : 120;
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
      }catch(e){}
    });
    io.observe(svg);
  });

  // ========= 4) Creative Navigation (magnetic hover) =========
  const magnets = document.querySelectorAll('[data-magnet]');
  magnets.forEach(btn=>{
    const max = 10;
    function mm(e){
      const r = btn.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width/2);
      const dy = e.clientY - (r.top + r.height/2);
      btn.style.transform = `translate(${(dx/r.width*max).toFixed(2)}px, ${(dy/r.height*max).toFixed(2)}px)`;
    }
    function ml(){ btn.style.transform = ''; }
    btn.addEventListener('pointermove', mm);
    btn.addEventListener('pointerleave', ml);
  });

  // ========= 5) Creative Sound Design (optional, generated) =========
  // Small UI sounds using WebAudio; no MP3 assets. Opt-in toggle stored in localStorage.
  let ac = null;
  function audioOn(){
    if(ac) return ac;
    ac = new (window.AudioContext || window.webkitAudioContext)();
    return ac;
  }
  function ping(freq=620, dur=0.045, type='sine', gain=0.04){
    try{
      const ctx = audioOn();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = type;
      o.frequency.value = freq;
      g.gain.value = 0.0001;
      o.connect(g); g.connect(ctx.destination);
      const t = ctx.currentTime;
      g.gain.exponentialRampToValueAtTime(gain, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.start(t);
      o.stop(t + dur + 0.01);
    }catch(e){}
  }
  function clicky(){
    ping(520, 0.05, 'triangle', 0.045);
    ping(210, 0.035, 'sine', 0.02);
  }
  function hover(){
    ping(740, 0.032, 'sine', 0.02);
  }

  const SOUND_KEY = 'ev_sound';
  function isSoundEnabled(){
    return localStorage.getItem(SOUND_KEY) === '1';
  }
  function setSoundEnabled(v){
    localStorage.setItem(SOUND_KEY, v ? '1' : '0');
    const t = document.getElementById('soundToggle');
    if(t) t.setAttribute('aria-pressed', v ? 'true' : 'false');
    if(t) t.querySelector('span').textContent = v ? 'Sound: ON' : 'Sound: OFF';
    if(v) audioOn();
  }

  // Attach UI sounds if enabled
  function wireSounds(){
    if(!isSoundEnabled()) return;
    document.querySelectorAll('a, button, .chip, [data-tilt]').forEach(el=>{
      el.addEventListener('pointerenter', ()=> hover(), { passive:true });
    });
    document.querySelectorAll('a, button').forEach(el=>{
      el.addEventListener('click', ()=> clicky());
    });
  }

  // Create toggle button if header exists
  const header = document.querySelector('header .actions');
  if(false){
    const b = document.createElement('button');
    b.className = 'iconbtn mail';
    b.id = 'soundToggle';
    b.type = 'button';
    b.setAttribute('aria-label','Sound toggle');
    b.setAttribute('aria-pressed', isSoundEnabled() ? 'true':'false');
    b.innerHTML = `
      <svg class="ico" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 10v4h4l5 4V6L7 10H3zm13.5 2c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
      </svg>
      <span style="position:absolute;left:-9999px;">Sound</span>
    `;
    b.addEventListener('click', ()=>{
      setSoundEnabled(!isSoundEnabled());
      // once enabled, wire handlers
      if(isSoundEnabled()) wireSounds();
    });
    header.insertBefore(b, header.firstChild);
    // label text (hidden) for accessibility
    const hidden = document.createElement('span');
    hidden.textContent = isSoundEnabled() ? 'Sound: ON' : 'Sound: OFF';
    hidden.style.position='absolute'; hidden.style.left='-9999px';
    b.appendChild(hidden);
  }

  // Wire now (if enabled already)
  wireSounds();

  // Resume audio on first interaction (browser policy)
  window.addEventListener('pointerdown', ()=>{
    if(isSoundEnabled()){
      try{ audioOn().resume(); }catch(e){}
    }
  }, { once:true });

})();


// ===== AUTO SOUND HOVER (requested) =====
(function(){
  // Use the existing ping() helper if present; otherwise no-op.
  const canPing = typeof ping === 'function';

  let enabled = false;
  function enable(){
    if(enabled) return;
    enabled = true;
    // Resume context if present
    try{ if(typeof audioOn === 'function') audioOn().resume(); }catch(e){}

    const hoverTargets = () => document.querySelectorAll('a.btn, button.btn, .chip, nav a');
    hoverTargets().forEach(el=>{
      el.addEventListener('pointerenter', ()=>{ try{ if(canPing) ping(760, 0.03, 'sine', 0.018); }catch(e){} }, { passive:true });
      el.addEventListener('click', ()=>{ try{ if(canPing){ ping(520, 0.05, 'triangle', 0.04); ping(210, 0.03, 'sine', 0.02);} }catch(e){} });
    });
  }

  // Enable after first user interaction (browser policy)
  window.addEventListener('pointerdown', enable, { once:true });
})();


// ===== SECTION CHANGE SFX =====
(function(){
  let last = 0;
  const minGap = 700; // ms

  function playSection(){
    const now = Date.now();
    if(now - last < minGap) return;
    last = now;
    try{ if(typeof ping === 'function') ping(420, 0.05, 'sine', 0.03); }catch(e){}
  }

  // Hash changes (nav anchors)
  window.addEventListener('hashchange', ()=> playSection());

  // Section enter via scroll
  const secs = Array.from(document.querySelectorAll('section[id]'));
  if(!secs.length) return;
  const io = new IntersectionObserver((ents)=>{
    ents.forEach(e=>{
      if(e.isIntersecting){
        playSection();
      }
    });
  }, { threshold: 0.55 });
  secs.forEach(s=> io.observe(s));
})();
