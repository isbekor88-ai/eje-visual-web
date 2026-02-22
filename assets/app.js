(function(){
  // mobile menu
  const hamb = document.getElementById('hamb');
  const mnav = document.getElementById('mnav');
  hamb?.addEventListener('click', () => mnav.classList.toggle('on'));
  mnav?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mnav.classList.remove('on')));

  // reveal on scroll
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('on'); });
  }, { threshold: .12 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));

  // modal (portfolio)
  const modal = document.getElementById('modal');
  const modalImg = document.getElementById('modalImg');
  const closeModal = document.getElementById('closeModal');

  function shut(){
    if(!modal) return;
    modal.classList.remove('on');
    modal.setAttribute('aria-hidden','true');
    if(modalImg) modalImg.src = '';
  }
  closeModal?.addEventListener('click', shut);
  modal?.addEventListener('click', (e)=>{ if(e.target === modal) shut(); });
  window.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') shut(); });

  // year
  const y = document.getElementById('year');
  if(y) y.textContent = new Date().getFullYear();

  // WhatsApp builder (if exists)
  const btnWA = document.getElementById('btnWA');
  if(btnWA){
    const PHONE = "526633220567";
    btnWA.addEventListener('click', ()=>{
      const name = document.getElementById('fName')?.value?.trim() || "Hola";
      const type = document.getElementById('fType')?.value || "Servicio";
      const use = document.getElementById('fUse')?.value?.trim() || "FB/IG/WhatsApp";
      const when = document.getElementById('fWhen')?.value || "Sin prisa";
      const msg = document.getElementById('fMsg')?.value?.trim() || "Te paso detalles y referencias.";
      const text =
`Hola, soy ${name}. Quiero cotizar con EJE VISUAL.

Servicio: ${type}
Uso/plataforma: ${use}
Entrega: ${when}

Detalles:
${msg}

Gracias.`;
      const url = `https://wa.me/${PHONE}?text=${encodeURIComponent(text)}`;
      window.open(url, "_blank");
    });
  }

  // expose modal open helper
  window.EV_openModal = function(src){
    if(!modal || !modalImg) return;
    modalImg.src = src;
    modal.classList.add('on');
    modal.setAttribute('aria-hidden','false');
  }
})();
