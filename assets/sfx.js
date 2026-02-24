(function(){
  // Audio only after user gesture. We arm sounds after first pointerdown.
  let ctx = null;
  let enabled = false;

  function getCtx(){
    if(ctx) return ctx;
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    return ctx;
  }

  function ping(freq=680, dur=0.045, type='sine', gain=0.035){
    try{
      if(!enabled) return;
      const c = getCtx();
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = type;
      o.frequency.value = freq;
      g.gain.value = 0.0001;
      o.connect(g); g.connect(c.destination);
      const t = c.currentTime;
      g.gain.exponentialRampToValueAtTime(gain, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.start(t);
      o.stop(t + dur + 0.01);
    }catch(e){}
  }

  function click(){
    ping(520, 0.05, 'triangle', 0.045);
    ping(210, 0.03, 'sine', 0.02);
  }
  function menu(){
    ping(620, 0.06, 'sine', 0.035);
    ping(880, 0.03, 'sine', 0.018);
  }

  window.EV_SFX = { ping, click, menu };

  function arm(){
    if(enabled) return;
    enabled = true;
    try{ getCtx().resume(); }catch(e){}

    // Buttons / primary actions
    document.querySelectorAll('a.btn, button.btn').forEach(el=>{
      el.addEventListener('click', ()=> click());
    });

    // Menu-only clicks (nav + mobile nav)
    document.querySelectorAll('header nav a, header .mnav a').forEach(el=>{
      el.addEventListener('click', ()=> menu());
    });
  }

  window.addEventListener('pointerdown', arm, { once:true });
})();
