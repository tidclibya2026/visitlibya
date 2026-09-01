(() => {
  "use strict";
  const ROTATION_INTERVAL = 3000;
  const hero = document.querySelector(".home-hero[data-hero-rotation-images]");
  if (!hero) return;
  const originalImage = hero.querySelector(".home-hero__image");
  const configuredImages = (hero.dataset.heroRotationImages ?? "").split("|")
    .map((path) => path.trim()).filter(Boolean)
    .map((path) => new URL(path, document.baseURI).href);
  const firstImage = originalImage?.currentSrc || originalImage?.src;
  const images = [...new Set([firstImage, ...configuredImages].filter(Boolean))];
  if (images.length < 2) return;

  images.slice(1).forEach((src) => { const preload = new Image(); preload.src = src; });
  const stage = document.createElement("div");
  stage.className = "vl-hero-rotation";
  stage.setAttribute("aria-hidden", "true");
  const imageA = document.createElement("img");
  const imageB = document.createElement("img");
  imageA.className = "vl-hero-rotation__image is-active";
  imageB.className = "vl-hero-rotation__image";
  imageA.alt = ""; imageB.alt = "";
  imageA.decoding = "async"; imageB.decoding = "async";
  imageA.src = images[0]; imageB.src = images[1];
  stage.append(imageA, imageB);
  hero.prepend(stage);
  hero.classList.add("is-hero-rotating");

  const dotsContainer = document.createElement("div");
  dotsContainer.className = "vl-hero-dots";
  const dotLabel = hero.dataset.heroDotLabel || "Image {index}";
  const dots = images.map((_, index) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = `vl-hero-dot${index === 0 ? " is-active" : ""}`;
    dot.setAttribute("aria-label", dotLabel.replace("{index}", String(index + 1)));
    dotsContainer.appendChild(dot);
    return dot;
  });
  hero.appendChild(dotsContainer);

  let activeLayer = imageA;
  let inactiveLayer = imageB;
  let currentIndex = 0;
  let timer = null;
  let transitionToken = 0;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const updateDots = (index) => dots.forEach((dot, dotIndex) =>
    dot.classList.toggle("is-active", dotIndex === index));
  const showSlide = (nextIndex) => {
    if (nextIndex === currentIndex) return;
    const token = ++transitionToken;
    let committed = false;
    const commit = () => {
      if (committed || token !== transitionToken) return;
      committed = true;
      window.requestAnimationFrame(() => {
        activeLayer.classList.remove("is-active");
        inactiveLayer.classList.add("is-active");
        [activeLayer, inactiveLayer] = [inactiveLayer, activeLayer];
        currentIndex = nextIndex;
        updateDots(currentIndex);
      });
    };
    inactiveLayer.onload = commit;
    inactiveLayer.src = images[nextIndex];
    if (inactiveLayer.complete) commit();
  };
  const stop = () => { window.clearInterval(timer); timer = null; };
  const start = () => {
    if (reducedMotion || document.hidden) return;
    stop();
    timer = window.setInterval(
      () => showSlide((currentIndex + 1) % images.length), ROTATION_INTERVAL,
    );
  };
  dots.forEach((dot, index) => dot.addEventListener("click", () => {
    showSlide(index);
    start();
  }));
  if (!reducedMotion) {
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) stop(); else start();
    });
    start();
  }
})();
