(function () {
  "use strict";

  const panelFallbackImages = [
    "panel/panel1.png",
    "panel/panel2.png",
    "panel/panel3.png",
    "panel/panel4.png",
    "panel/panel5.png",
    "panel/panel6.jpg",
    "panel/panel7.jpg",
    "panel/panel8.jpg",
    "panel/panel9.jpg",
    "panel/panel10.jpg",
    "panel/panel11.jpg",
    "panel/panel12.jpg",
    "panel/panel13.jpg",
    "panel/panel14.jpg",
    "panel/panel15.jpeg",
    "panel/panel16.jpg",
    "panel/panel17.JPG",
    "panel/panel18.JPG",
    "panel/panel19.jpeg",
    "panel/panel20.jpg",
    "panel/panel21.jpg",
    "panel/panel22.jpg"
];
  const defaultImageFallback = "imges/landscapes.jpg";
  const atlasUrl = "https://tidclibya2026.github.io/libyan--map/";

  const normalizeText = (value) => String(value || "")
    .toLowerCase()
    .replace(/[أإآ]/g, "ا")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/[\u064B-\u065F\u0640]/g, "")
    .trim();

  const testImage = (src) => new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve(src);
    image.onerror = () => resolve(null);
    image.src = src;
  });

  const wireHeader = () => {
    const header = document.getElementById("site-header");
    const navToggle = document.querySelector(".nav-toggle");
    const navLinks = document.getElementById("primary-menu");
    const setHeader = () => header && header.classList.toggle("is-scrolled", window.scrollY > 20);
    setHeader();
    window.addEventListener("scroll", setHeader, { passive: true });
    if (navLinks) {
      const currentPage = (location.pathname.split("/").pop() || "index.html").toLowerCase();
      navLinks.querySelectorAll("a").forEach((link) => {
        const linkPage = (link.getAttribute("href") || "").split("#")[0].split("?")[0].toLowerCase();
        link.classList.toggle("is-active", linkPage === currentPage);
      });
    }
    if (!navToggle || !navLinks) return;
    const closeMenu = () => {
      navLinks.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    };
    navToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });
    navLinks.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
    document.addEventListener("click", (event) => {
      if (navLinks.contains(event.target) || navToggle.contains(event.target)) return;
      closeMenu();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
  };

  const scrollToSelector = (selector) => {
    const target = selector ? document.querySelector(selector) : null;
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const wireSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"], a[href^="index.html#"]').forEach((link) => {
      link.addEventListener("click", (event) => {
        const href = link.getAttribute("href") || "";
        if (href.startsWith("index.html#") && !location.pathname.endsWith("index.html") && location.pathname !== "/") return;
        const targetId = href.replace("index.html", "");
        const target = targetId && targetId !== "#" ? document.querySelector(targetId) : null;
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
    document.querySelectorAll("[data-scroll-target]").forEach((button) => {
      button.addEventListener("click", () => scrollToSelector(button.getAttribute("data-scroll-target")));
    });
    if (location.hash) {
      window.setTimeout(() => scrollToSelector(location.hash), 350);
    }
  };

  const wireHeroVideoFallback = async () => {
    const hero = document.querySelector(".cinematic-hero");
    if (!hero) return;
    const fallback = (await Promise.all(panelFallbackImages.map(testImage))).find(Boolean);
    if (fallback) hero.style.backgroundImage = `linear-gradient(180deg, rgba(7,59,76,.16), rgba(7,59,76,.28)), url("${fallback}")`;
    const frame = hero.querySelector(".hero-video");
    if (!frame) {
      hero.classList.add("is-video-fallback");
      return;
    }
    let loaded = false;
    frame.addEventListener("load", () => {
      loaded = true;
      hero.classList.remove("is-video-fallback");
    });
    window.setTimeout(() => {
      if (!loaded) hero.classList.add("is-video-fallback");
    }, 3500);
  };

  const wireReveal = () => {
    const revealItems = document.querySelectorAll(".reveal");
    if (!revealItems.length) return;
    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });
    revealItems.forEach((item) => observer.observe(item));
  };

  const wireImageFallbacks = () => {
    document.querySelectorAll("img").forEach((image) => {
      image.addEventListener("error", () => {
        const fallback = image.dataset.fallbackSrc || defaultImageFallback;
        if (fallback && image.src.indexOf(fallback) === -1) {
          image.src = fallback;
          return;
        }
        image.classList.add("is-missing");
      });
    });
  };

  const applyFilter = (scope, filter) => {
    const buttons = scope.querySelectorAll("[data-filter]");
    const section = scope.closest("section") || document;
    const cards = section.querySelectorAll("[data-category]");
    buttons.forEach((item) => item.classList.toggle("is-active", (item.dataset.filter || "all") === filter));
    cards.forEach((card) => {
      const categories = (card.dataset.category || "").split(/\s+/).filter(Boolean);
      card.classList.toggle("is-hidden", filter !== "all" && !categories.includes(filter));
    });
  };

  const wireFilters = () => {
    document.querySelectorAll(".filter-tabs").forEach((scope) => {
      const buttons = scope.querySelectorAll("[data-filter]");
      buttons.forEach((button) => {
        button.addEventListener("click", () => applyFilter(scope, button.dataset.filter || "all"));
      });
      const queryFilter = new URLSearchParams(location.search).get("filter");
      if (queryFilter) {
        applyFilter(scope, queryFilter);
      }
    });
  };

  const wireModal = () => {
    const modal = document.getElementById("destination-modal");
    if (!modal) return;
    const title = document.getElementById("modal-title");
    const tag = document.getElementById("modal-tag");
    const image = document.getElementById("modal-image");
    const description = document.getElementById("modal-description");
    const openModal = (button) => {
      title.textContent = button.dataset.title || "";
      tag.textContent = button.dataset.tag || "";
      description.textContent = button.dataset.description || "";
      image.src = button.dataset.image || defaultImageFallback;
      image.alt = button.dataset.title || "وجهة سياحية في ليبيا";
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    };
    const closeModal = () => {
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    };
    document.querySelectorAll(".js-open-modal").forEach((button) => button.addEventListener("click", () => openModal(button)));
    modal.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", closeModal));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal();
    });
  };

  const knowledge = [
    { keys: ["طرابلس", "tripoli"], text: "طرابلس تجمع المدينة القديمة وقوس ماركوس والأسواق والسرايا الحمراء في تجربة حضرية متوسطية.", link: "destinations.html#tripoli", label: "افتح طرابلس" },
    { keys: ["غدامس", "ghadames"], text: "غدامس جوهرة الصحراء، تشتهر بالشوارع المسقوفة وعين الفرس والرملة وعمارة الواحة.", link: "destinations.html#ghadames", label: "افتح غدامس" },
    { keys: ["أكاكوس", "اكاكوس", "acacus"], text: "أكاكوس تجربة للفن الصخري والأقواس والوديان والتخييم في الجنوب الليبي.", link: "heritage.html#acacus", label: "افتح أكاكوس" },
    { keys: ["أوجلة", "اوجلة", "awjila"], text: "أوجلة واحة ليبية في الشرق، تتميز بطابعها المحلي والتراثي وتعد محطة مهمة ضمن مسار الواحات: أوجلة → هون → سوكنة → ودان → أوباري → غدامس.", link: "destinations.html#awjila", label: "افتح أوجلة" },
    { keys: ["الأكل", "اكل", "المطبخ", "البازين", "الكسكسي", "العصبان", "الرشدة", "المقروض"], text: "من أشهر الأكلات الليبية: البازين، الكسكسي، العصبان، الرشدة، والمقروض.", link: "culture.html#cuisine", label: "افتح المطبخ الليبي" },
    { keys: ["الأطلس", "الاطلس", "خريطة", "خريطه"], text: "يمكنك فتح الأطلس السياحي الوطني عبر الرابط الرسمي الجديد.", link: atlasUrl, label: "افتح الأطلس السياحي" },
    { keys: ["برنامج", "رحلة", "7 أيام", "خمسة", "عشرة"], text: "اقتراحات سريعة: 3 أيام طرابلس ولبدة وصبراتة، 5 أيام طرابلس وغدامس، 7 أيام طرابلس والجبل الأخضر والتراث العالمي، 10 أيام الساحل والصحراء والواحات.", link: "plan.html", label: "افتح تخطيط الرحلة" }
  ];

  const getBotReply = (message) => {
    const normalized = normalizeText(message);
    return knowledge.find((item) => item.keys.some((key) => normalized.includes(normalizeText(key)))) || {
      text: "يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، الأطلس، أوجلة، أو برنامج رحلة.",
      link: "destinations.html",
      label: "ابدأ بالوجهات"
    };
  };

  const appendMessage = (messages, content, type) => {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    if (typeof content === "string") {
      message.textContent = content;
    } else {
      const text = document.createElement("span");
      text.textContent = content.text;
      message.appendChild(text);
      if (content.link) {
        const link = document.createElement("a");
        link.className = "chat-link";
        link.href = content.link;
        link.textContent = content.label || "افتح الرابط";
        if (content.link.startsWith("http")) {
          link.target = "_blank";
          link.rel = "noopener";
        }
        message.appendChild(link);
      }
    }
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
  };

  const wireChat = () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    if (!form || !input || !messages) return;
    const ask = (value) => {
      const clean = value.trim();
      if (!clean) return;
      appendMessage(messages, clean, "user");
      window.setTimeout(() => appendMessage(messages, getBotReply(clean), "bot"), 220);
    };
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      ask(input.value);
      input.value = "";
    });
    document.querySelectorAll("[data-ai-question]").forEach((button) => {
      button.addEventListener("click", () => ask(button.dataset.aiQuestion || button.textContent || ""));
    });
  };

  const init = () => {
    wireHeader();
    wireSmoothScroll();
    wireHeroVideoFallback();
    wireReveal();
    wireImageFallbacks();
    wireFilters();
    wireModal();
    wireChat();
    console.log("Visit Libya content atlas Awjila v3 loaded");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
