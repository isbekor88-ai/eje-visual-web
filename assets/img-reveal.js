/**
 * EJE VISUAL — Image Color Reveal (V23)
 * Show full-color image only under cursor (radial reveal), while base stays B/W.
 * Applies to:
 *  - .work (portfolio cards)
 *  - .hero-visual
 *  - .screen (mockups)
 *  - modal image (#modalImg)
 */
(function(){
  function setupContainer(container, img, fit){
    if(!container || !img) return;
    if(container.dataset.imgRevealInit === "1") return;
    container.dataset.imgRevealInit = "1";
    container.classList.add("imgfx-onhover");

    // Ensure container is positioned
    const cs = getComputedStyle(container);
    if(cs.position === "static"){
      container.style.position = "relative";
    }
    container.style.overflow = container.style.overflow || "hidden";

    // Create overlay layer
    const layer = document.createElement("div");
    layer.className = "imgColorReveal";
    layer.style.setProperty("--img-url", `url("${img.currentSrc || img.src}")`);
    if(fit) layer.style.setProperty("--reveal-fit", fit);

    // Insert after img (so metadata can sit above)
    if(img.nextSibling){
      container.insertBefore(layer, img.nextSibling);
    }else{
      container.appendChild(layer);
    }

    // Keep layer synced if image changes
    const sync = ()=> layer.style.setProperty("--img-url", `url("${img.currentSrc || img.src}")`);
    img.addEventListener("load", sync);

    // Pointer tracking -> set CSS vars on container
    const setXY = (ev)=>{
      const r = container.getBoundingClientRect();
      const x = ((ev.clientX - r.left) / r.width) * 100;
      const y = ((ev.clientY - r.top) / r.height) * 100;
      container.style.setProperty("--reveal-x", x.toFixed(2) + "%");
      container.style.setProperty("--reveal-y", y.toFixed(2) + "%");
    };

    container.addEventListener("pointermove", setXY, { passive: true });
    container.addEventListener("pointerenter", (ev)=>{
      setXY(ev);
      container.classList.add("imgfx-hot");
    }, { passive: true });
    container.addEventListener("pointerleave", ()=>{
      container.classList.remove("imgfx-hot");
      container.style.setProperty("--reveal-x", "50%");
      container.style.setProperty("--reveal-y", "50%");
    }, { passive: true });
  }

  function init(){
    document.querySelectorAll(".work").forEach(w=>{
      const img = w.querySelector("img");
      setupContainer(w, img, "cover");
    });
    document.querySelectorAll(".hero-visual").forEach(h=>{
      const img = h.querySelector("img");
      setupContainer(h, img, "cover");
    });
    document.querySelectorAll(".screen").forEach(s=>{
      const img = s.querySelector("img");
      setupContainer(s, img, "cover");
    });

    // Modal: wrap the img so we don't affect header inside .box
    const modalImg = document.getElementById("modalImg");
    if(modalImg && !modalImg.closest(".imgfx-wrap")){
      const wrap = document.createElement("div");
      wrap.className = "imgfx-wrap imgfx-onhover";
      wrap.style.position = "relative";
      wrap.style.overflow = "hidden";
      // Insert wrap before img
      modalImg.parentElement.insertBefore(wrap, modalImg);
      wrap.appendChild(modalImg);
      setupContainer(wrap, modalImg, "contain");
    }
  }

  // Run after DOM
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
