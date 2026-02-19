(function(){
  const root = document.documentElement;
  const themeBtn = document.getElementById('themeToggle');
  const menuBtn = document.getElementById('menuToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  const links = [...document.querySelectorAll('a[data-scroll]')];

  // Theme persistence
  const saved = localStorage.getItem('ejevisual_theme');
  if(saved){ root.setAttribute('data-theme', saved); }
  updateThemeIcon();

  themeBtn?.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('ejevisual_theme', next);
    updateThemeIcon();
  });

  function updateThemeIcon(){
    const current = root.getAttribute('data-theme') || 'light';
    const icon = document.getElementById('themeIcon');
    const label = document.getElementById('themeLabel');
    if(!icon || !label) return;
    if(current === 'dark'){
      icon.innerHTML = '<path d="M12 2a7 7 0 1 0 7 7A7 7 0 0 1 12 2Z"/>';
      label.textContent = 'Claro';
    } else {
      icon.innerHTML = '<path d="M12 18a6 6 0 0 1-6-6 6.8 6.8 0 0 1 7.5-6.7 6 6 0 1 0 4.5 10.7A6.9 6.9 0 0 1 12 18Z"/>';
      label.textContent = 'Oscuro';
    }
  }

  // Mobile menu
  menuBtn?.addEventListener('click', () => {
    const open = mobileMenu.classList.toggle('open');
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  links.forEach(a => a.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
    menuBtn?.setAttribute('aria-expanded','false');
  }));

  // Active section highlight
  const sections = [...document.querySelectorAll('section[id]')];
  const navAll = [...document.querySelectorAll('a[data-nav]')];

  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if(e.isIntersecting){
        navAll.forEach(a => a.removeAttribute('aria-current'));
        const id = e.target.getAttribute('id');
        navAll.filter(a => a.getAttribute('href') === '#'+id)
          .forEach(a => a.setAttribute('aria-current', 'page'));
      }
    });
  }, { rootMargin: "-55% 0px -40% 0px", threshold: 0.01 });

  sections.forEach(s => obs.observe(s));
})();
