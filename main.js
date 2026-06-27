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
      button.addEventListener("click", () => {
        const selector = button.getAttribute("data-scroll-target");
        const target = selector ? document.querySelector(selector) : null;
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  };

  const wireHeroVideoFallback = async () => {
    const hero = document.querySelector(".cinematic-hero");
    if (!hero) return;
    const fallback = (await Promise.all(panelFallbackImages.map(testImage))).find(Boolean);
    if (fallback) hero.style.setProperty("--hero-fallback-image", `url("${fallback}")`);
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
        const fallback = image.dataset.fallbackSrc;
        if (fallback && image.src.indexOf(fallback) === -1) {
          image.src = fallback;
          return;
        }
        image.classList.add("is-missing");
      });
    });
  };

  const wireFilters = () => {
    document.querySelectorAll(".filter-tabs").forEach((scope) => {
      const buttons = scope.querySelectorAll("[data-filter]");
      const section = scope.closest("section") || document;
      const cards = section.querySelectorAll("[data-category]");
      buttons.forEach((button) => {
        button.addEventListener("click", () => {
          const filter = button.dataset.filter || "all";
          buttons.forEach((item) => item.classList.toggle("is-active", item === button));
          cards.forEach((card) => {
            const categories = (card.dataset.category || "").split(/\s+/).filter(Boolean);
            card.classList.toggle("is-hidden", filter !== "all" && !categories.includes(filter));
          });
        });
      });
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
      image.src = button.dataset.image || "";
      image.alt = button.dataset.title || "";
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
    { keys: ["طرابلس", "tripoli"], text: "طرابلس بداية مثالية للمدينة القديمة والأسواق والواجهة المتوسطية، ويمكن ربطها بزيارة لبدة الكبرى وصبراتة." },
    { keys: ["غدامس", "ghadames"], text: "غدامس مدينة الواحة والظل والضوء، وتناسب تجربة الثقافة والضيافة والمدينة القديمة." },
    { keys: ["أكاكوس", "اكاكوس", "acacus"], text: "أكاكوس تجربة صحراوية عالمية للفنون الصخرية والتكوينات الطبيعية، وينصح بزيارتها مع دليل محلي متخصص." },
    { keys: ["برنامج 7 أيام", "سبعة أيام"], text: "برنامج 7 أيام مبدئي: طرابلس، لبدة الكبرى، صبراتة، ثم غدامس أو شحات حسب التنظيم، مع يوم للتجربة الثقافية." },
    { keys: ["المطبخ", "الأكلات", "البازين", "الكسكسي", "العصبان"], text: "من أشهر الأكلات الليبية: البازين، الكسكسي، العصبان، المبكبكة، ورشدة البرمة." },
    { keys: ["التراث", "اليونسكو", "unesco"], text: "مواقع التراث العالمي في ليبيا: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["السلامة", "التأشيرات", "فيزا"], text: "معلومات السلامة والتأشيرات يجب الرجوع فيها إلى الجهات الرسمية عند الإطلاق النهائي." }
  ];

  const getBotReply = (message) => {
    const normalized = normalizeText(message);
    const match = knowledge.find((item) => item.keys.some((key) => normalized.includes(normalizeText(key))));
    return match ? match.text : "يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، برنامج 7 أيام، أو التخطيط الأولي للرحلة.";
  };

  const wireChat = () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    if (!form || !input || !messages) return;
    const appendMessage = (text, type) => {
      const message = document.createElement("div");
      message.className = `message ${type}`;
      message.textContent = text;
      messages.appendChild(message);
      messages.scrollTop = messages.scrollHeight;
    };
    const ask = (value) => {
      const clean = value.trim();
      if (!clean) return;
      appendMessage(clean, "user");
      window.setTimeout(() => appendMessage(getBotReply(clean), "bot"), 220);
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

  const wireBudget = () => {
    const form = document.getElementById("budget-form");
    if (!form) return;
    const days = document.getElementById("budget-days");
    const people = document.getElementById("budget-people");
    const style = document.getElementById("budget-style");
    const output = document.getElementById("budget-output");
    const update = () => {
      const total = Number(days.value || 0) * Number(people.value || 0) * Number(style.value || 0);
      output.value = `تقدير تجريبي: ${total.toLocaleString("ar")} وحدة`;
      output.textContent = output.value;
    };
    [days, people, style].forEach((field) => field.addEventListener("input", update));
    update();
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
    wireBudget();
    console.log("Visit Libya official portal v1 loaded");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
