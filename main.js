(function () {
  "use strict";

  const heroBackgrounds = [
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

  const heroBackgroundValue = (src) =>
    `linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.05) 55%, rgba(0,0,0,0.12) 100%), url("${src}")`;

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
        if (!targetId || targetId === "#") return;
        const target = document.querySelector(targetId);
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });

    document.querySelectorAll("[data-scroll-target]").forEach((button) => {
      button.addEventListener("click", () => {
        const targetSelector = button.getAttribute("data-scroll-target");
        const target = targetSelector ? document.querySelector(targetSelector) : null;
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });
  };

  const wireHeroSlider = async () => {
    const hero = document.querySelector(".hero");
    if (!hero || hero.classList.contains("cinematic-hero")) return;
    const loadedImages = (await Promise.all(heroBackgrounds.map(testImage))).filter(Boolean);
    if (!loadedImages.length) return;
    let activeIndex = 0;
    let timer = null;
    const dots = document.getElementById("hero-dots");
    const setHero = (index) => {
      activeIndex = (index + loadedImages.length) % loadedImages.length;
      hero.classList.add("is-changing");
      hero.style.backgroundImage = heroBackgroundValue(loadedImages[activeIndex]);
      if (dots) {
        dots.querySelectorAll(".hero-dot").forEach((dot, dotIndex) => {
          dot.classList.toggle("is-active", dotIndex === activeIndex);
        });
      }
      window.setTimeout(() => hero.classList.remove("is-changing"), 700);
    };
    if (dots) {
      dots.innerHTML = loadedImages.map((_, index) => `<button class="hero-dot${index === 0 ? " is-active" : ""}" type="button" aria-label="صورة ${index + 1}"></button>`).join("");
      dots.querySelectorAll(".hero-dot").forEach((dot, index) => {
        dot.addEventListener("click", () => {
          setHero(index);
          if (timer) window.clearInterval(timer);
          timer = window.setInterval(() => setHero(activeIndex + 1), 6000);
        });
      });
    }
    setHero(0);
    if (loadedImages.length > 1) timer = window.setInterval(() => setHero(activeIndex + 1), 6000);
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
    document.querySelectorAll(".js-open-modal").forEach((button) => {
      button.addEventListener("click", () => openModal(button));
    });
    modal.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", closeModal));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal();
    });
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

  const knowledge = [
    { keys: ["طرابلس", "tripoli"], text: "طرابلس بداية ممتازة للمدينة القديمة والأسواق والواجهة المتوسطية، ويمكن ربطها بزيارة لبدة الكبرى وصبراتة." },
    { keys: ["بنغازي", "benghazi"], text: "بنغازي بوابة الشرق، وتناسب مسارًا يجمع المدينة مع الجبل الأخضر وشحات وسوسة ورأس الهلال." },
    { keys: ["لبدة", "leptis"], text: "لبدة الكبرى من أبرز مواقع التراث العالمي في ليبيا، وتضم مسرحًا وحمامات وأسواقًا ومعابد رومانية قرب الساحل الغربي." },
    { keys: ["صبراتة", "sabratha"], text: "صبراتة مدينة أثرية ساحلية تشتهر بمسرحها الروماني وموقعها المتوسطي القريب من طرابلس." },
    { keys: ["قورينا", "شحات", "cyrene"], text: "قورينا / شحات موقع كلاسيكي مهم في الجبل الأخضر، يجمع المعابد والمدافن الصخرية والمشهد الطبيعي." },
    { keys: ["غدامس", "ghadames"], text: "غدامس القديمة واحة تراثية ذات عمارة صحراوية فريدة، وتناسب تجربة الثقافة والضيافة والمدينة القديمة." },
    { keys: ["أكاكوس", "اكاكوس", "acacus"], text: "تادرارت أكاكوس تجربة عالمية للفنون الصخرية والتكوينات الطبيعية، والأفضل زيارتها مع دليل محلي متخصص." },
    { keys: ["الجبل الأخضر", "الجبل الاخضر", "وادي الكوف", "سوسة", "رأس الهلال", "راس الهلال"], text: "الجبل الأخضر يجمع الغابات والوديان والشواطئ والمواقع الأثرية، ومن أبرز محطاته شحات وسوسة ورأس الهلال ووادي الكوف." },
    { keys: ["الصحراء", "غات", "أوباري", "او باري", "وادي الحياة", "واو الناموس", "فزان"], text: "الصحراء الليبية تمنح تجربة واسعة بين غات وأوباري ووادي الحياة وواو الناموس، مع ضرورة التنظيم المحلي والاعتماد الرسمي عند الإطلاق." },
    { keys: ["الثقافة", "الفلكلور", "اللباس", "الأزياء", "الحرف"], text: "الثقافة الليبية تظهر في الضيافة واللباس التقليدي والحرف والموسيقى والمناسبات الاجتماعية." },
    { keys: ["المطبخ", "الكسكسي", "البازين", "العصيدة", "العصبان", "المبكبكة", "رشدة"], text: "المطبخ الليبي غني بأطباق مثل البازين والكسكسي والعصيدة والعصبان والمبكبكة ورشدة البرمة، وهو جزء أساسي من تجربة الضيافة." },
    { keys: ["المهرجانات", "غدامس", "أوجلة", "جرمة", "التمور"], text: "من أمثلة المهرجانات الثقافية: غدامس، أوجلة الثقافي السياحي، جرمة، مهرجانات الخريف، ومهرجان التمور." },
    { keys: ["التراث", "unesco", "اليونسكو"], text: "مواقع التراث العالمي في ليبيا هي: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["الأطلس", "الاطلس", "خريطة", "خريطه"], text: "الأطلس السياحي الوطني يساعد على استكشاف المواقع التراثية والطبيعية والخدمية على خريطة تفاعلية." },
    { keys: ["برنامج 7 أيام", "سبعة أيام", "سبعه ايام"], text: "برنامج 7 أيام مبدئي قد يبدأ بطرابلس ولبدة وصبراتة، ثم شحات أو غدامس، مع يوم للتجربة الثقافية أو الصحراوية حسب التنظيم المتاح." },
    { keys: ["التأشيرات", "التاشيرات", "فيزا", "دخول"], text: "معلومات التأشيرات والدخول يجب الرجوع فيها إلى الجهات الرسمية عند الإطلاق النهائي، ولا يعتمد هذا النموذج كمرجع رسمي." },
    { keys: ["السلامة", "السلامه", "أمان", "امان"], text: "للسلامة: احتفظ بالوثائق المهمة، خطط مع مرشد محلي، انتبه للشمس والترطيب، وارجع للجهات الرسمية قبل السفر." },
    { keys: ["ميزانية", "ميزانيه", "تكلفة", "تكلفه"], text: "أي أرقام ميزانية داخل المنصة تقديرية وتجريبية فقط، وتحتاج إلى اعتماد رسمي عند الإطلاق النهائي." }
  ];

  const getBotReply = (message) => {
    const normalized = normalizeText(message);
    const match = knowledge.find((item) => item.keys.some((key) => normalized.includes(normalizeText(key))));
    if (match) return match.text;
    return "يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، المهرجانات، السلامة، الميزانية، أو برنامج 7 أيام داخل ليبيا.";
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
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = input.value.trim();
      if (!value) return;
      appendMessage(value, "user");
      input.value = "";
      window.setTimeout(() => appendMessage(getBotReply(value), "bot"), 260);
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
    wireHeroSlider();
    wireFilters();
    wireModal();
    wireImageFallbacks();
    wireReveal();
    wireChat();
    wireBudget();
    console.log("Visit Libya master content v10 loaded");
    console.log("Visit Libya cinematic video hero v01 loaded");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
