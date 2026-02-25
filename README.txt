EJE VISUAL — Sitio web + VR (A-Frame)

ESTRUCTURA
/
  index.html
  portfolio.html
  privacidad.html
  terminos.html
  vr.html
  assets/
    app.css
    app.js
    sfx.js
    ticker.js
    data_loader.js
    category.js
    fx.js
    vr.js
    logo.png
    logo-outline.png
    portfolio.manifest.json
    portfolio/
      (imágenes del portafolio)

PORTAFOLIO (MANUAL)
- Reemplaza las imágenes dentro de assets/portfolio/ conservando los nombres (incluye ejemplos).
- Si quieres cambiar qué se muestra en la galería, edita:
  assets/portfolio.manifest.json

IMPORTANTE
- Para que RSS/ticker y el portafolio (manifest) funcionen bien, abre con servidor (no file://):
  python -m http.server 8000
  luego abre: http://localhost:8000

VR
- Abre vr.html desde el mismo servidor.
- Meta Quest: usa el navegador del headset y entra a /vr.html
