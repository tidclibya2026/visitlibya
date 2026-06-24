(function () {
  "use strict";

  const normalizeText = (value) => value
    .toString()
    .toLowerCase()
    .replace(/[أإآ]/g, "ا")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/[\u064B-\u065F\u0640]/g, "")
    .trim();

  const heroImageGroups = [
    ["imges/pan1.webp"],
    ["imges/pan6.webp"],
    ["imges/pan4.webp"],
    ["imges/pan5.webp"],
    ["imges/pan2.avif"],
    ["imges/pan3.avif"],
    ["imges/Leptis Magna3.jpeg", "imges/Leptis Magna3.jpg"],
    ["imges/Acacus.jpg"],
    ["imges/Ghadames2.JPG"],
    ["imges/beaches.jpg"],
    ["imges/Cyrene.jpg"],
    ["imges/Sabratha.jpg"]
  ];

  const testImage = (src) => new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve(src);
    image.onerror = () => resolve(null);
    image.src = src;
  });

  const firstAvailableFromGroup = async (group) => {
    for (const src of group) {
      const resolved = await testImage(src);
      if (resolved) return resolved;
    }
    return null;
  };

  const setHeaderState = (header) => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 20);
  };

  const wireMobileMenu = (navToggle, navLinks) => {
    if (!navToggle || !navLinks) return;

    const closeMenu = () => {
      navLinks.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    };

    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-controls", "primary-menu");
    navToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeMenu);
    });

    document.addEventListener("click", (event) => {
      if (navLinks.contains(event.target) || navToggle.contains(event.target)) return;
      closeMenu();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
  };

  const wireSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", (event) => {
        const targetId = link.getAttribute("href");
        if (!targetId || targetId === "#") return;
        const target = document.querySelector(targetId);
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  };

  const wireHeroSlider = async (hero) => {
    if (!hero) return;

    const resolvedGroups = await Promise.all(heroImageGroups.map(firstAvailableFromGroup));
    const heroImages = resolvedGroups.filter(Boolean);
    if (!heroImages.length) return;

    const slider = document.createElement("div");
    slider.className = "hero-slider";

    const slides = heroImages.map((src, index) => {
      const slide = document.createElement("div");
      slide.className = index === 0 ? "hero-slide is-active" : "hero-slide";
      slide.style.backgroundImage = `url("${src}")`;
      slider.appendChild(slide);
      return slide;
    });

    hero.prepend(slider);
    hero.classList.add("has-slider");

    if (slides.length < 2) return;
    let activeIndex = 0;
    window.setInterval(() => {
      slides[activeIndex].classList.remove("is-active");
      activeIndex = (activeIndex + 1) % slides.length;
      slides[activeIndex].classList.add("is-active");
    }, 5000);
  };

  const wireDestinationFilters = () => {
    const buttons = document.querySelectorAll(".destination-filters [data-filter]");
    const cards = document.querySelectorAll(".destination-card[data-category]");
    if (!buttons.length || !cards.length) return;

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const filter = button.dataset.filter || "all";
        buttons.forEach((item) => item.classList.toggle("is-active", item === button));

        cards.forEach((card) => {
          const categories = (card.dataset.category || "").split(/\s+/).filter(Boolean);
          const shouldShow = filter === "all" || categories.includes(filter);
          card.classList.toggle("is-hidden", !shouldShow);
        });
      });
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

  const wireAccordions = () => {
    const accordions = document.querySelectorAll(".accordion");
    accordions.forEach((button) => {
      button.addEventListener("click", () => {
        const panel = button.nextElementSibling;
        const isOpen = button.classList.toggle("is-open");
        button.setAttribute("aria-expanded", String(isOpen));
        if (panel) panel.hidden = !isOpen;
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
    }, { threshold: 0.14, rootMargin: "0px 0px -60px 0px" });

    revealItems.forEach((item) => observer.observe(item));
  };

  const responses = [
    { keys: ["طرابلس", "tripoli"], text: "طرابلس بداية مثالية للتعرف على المدينة القديمة والأسواق والواجهة المتوسطية، ويمكن ربطها بزيارة لبدة وصبراتة." },
    { keys: ["بنغازي", "benghazi"], text: "بنغازي بوابة الشرق، وتناسب مسارًا يجمع المدينة مع الجبل الأخضر وشحات ودرنة عند توفر التنظيم المناسب." },
    { keys: ["لبدة", "leptis"], text: "لبدة الكبرى من أبرز مواقع التراث العالمي في ليبيا، وتمنح الزائر تجربة رومانية متوسطية واسعة وقريبة من طرابلس." },
    { keys: ["صبراتة", "sabratha"], text: "صبراتة تجمع بين المسرح الأثري والبحر، وهي محطة قوية ضمن مسار الساحل والتراث العالمي." },
    { keys: ["شحات", "قورينا", "cyrene"], text: "شحات / قورينا وجهة تراثية في الجبل الأخضر، ويمكن ربطها بالطبيعة والمرتفعات والمدن الشرقية." },
    { keys: ["غدامس", "ghadames"], text: "غدامس القديمة واحة تراثية ذات عمارة صحراوية فريدة، وتناسب تجربة الثقافة والضيافة والمدينة القديمة." },
    { keys: ["غات", "ghat"], text: "غات بوابة جنوبية لمسارات الصحراء وأكاكوس، وتحتاج الرحلة إليها إلى تنظيم محلي واعتماد الجهات المختصة." },
    { keys: ["اكاكوس", "أكاكوس", "acacus"], text: "تادرارت أكاكوس تجربة صحراوية عالمية للفنون الصخرية والتكوينات الطبيعية، والأفضل زيارتها مع دليل محلي متخصص." },
    { keys: ["جبل نفوسه", "جبل نفوسة", "نالوت", "غريان"], text: "جبل نفوسة يمنح تجربة تجمع العمارة الجبلية والحرف والقرى التاريخية ومسارات الثقافة المحلية." },
    { keys: ["الجبل الاخضر", "الجبل الأخضر", "البيضاء", "درنه", "درنة"], text: "الجبل الأخضر مناسب للطبيعة والمرتفعات والتراث القريب من شحات، مع مشاهد مختلفة عن الصحراء والساحل." },
    { keys: ["اوباري", "أوباري", "وادي الحياه", "وادي الحياة"], text: "أوباري ووادي الحياة يقدمان تجربة البحيرات والواحات وسط الصحراء، مع ضرورة التخطيط المسبق والتنظيم المحلي." },
    { keys: ["واو الناموس"], text: "واو الناموس وجهة جيولوجية استثنائية في عمق الصحراء، وتناسب رحلات التصوير والبحث عند توفر ترتيبات آمنة." },
    { keys: ["الحدائق الجيولوجيه", "الحدائق الجيولوجية", "جيولوجيا"], text: "الحدائق الجيولوجية والتكوينات الصخرية في ليبيا مناسبة للتصوير والتعليم والرحلات العلمية التجريبية." },
    { keys: ["المطبخ", "اكل", "أكل", "كسكسي", "بازين", "شاي"], text: "المطبخ الليبي جزء من التجربة: الكسكسي والبازين والشاي الليبي والتمور والأكلات الساحلية تعكس كرم الضيافة." },
    { keys: ["الثقافه", "الثقافة", "مهرجان", "مهرجانات", "الحرف", "اللباس"], text: "الثقافة الليبية تجمع الضيافة واللباس التقليدي والحرف والموسيقى والمهرجانات، وهي محور مهم في التجربة السياحية." },
    { keys: ["التراث", "unesco", "اليونسكو"], text: "مواقع التراث العالمي في ليبيا هي: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["الاطلس", "الأطلس", "اطلس", "خريطه", "خريطة"], text: "الأطلس السياحي الوطني يساعد على استكشاف المواقع التراثية والطبيعية والخدمية على خريطة تفاعلية." },
    { keys: ["برنامج 7 ايام", "برنامج 7 أيام", "سبعه ايام", "سبعة أيام", "7 ايام", "7 أيام"], text: "برنامج 7 أيام مبدئي: طرابلس، لبدة الكبرى، صبراتة، غدامس، بنغازي أو شحات، ثم تجربة ثقافية أو صحراوية حسب التنظيم المتاح." },
    { keys: ["التاشيرات", "التأشيرات", "فيزا", "دخول"], text: "معلومات التأشيرات والدخول يجب الرجوع فيها إلى الجهات الرسمية عند الإطلاق النهائي، ولا يعتمد هذا النموذج كمرجع رسمي." },
    { keys: ["السلامه", "السلامة", "امان", "أمان"], text: "للسلامة: احتفظ بالوثائق المهمة، خطط مع مرشد محلي، انتبه للشمس والترطيب، وارجع للجهات الرسمية قبل السفر." },
    { keys: ["ميزانيه", "ميزانية", "تكلفه", "تكلفة"], text: "أي أرقام ميزانية داخل المنصة ستكون تقديرية وتجريبية فقط، وتحتاج إلى اعتماد رسمي عند الإطلاق النهائي." }
  ];

  const getReply = (text) => {
    const normalized = normalizeText(text);
    const match = responses.find((item) => item.keys.some((key) => normalized.includes(normalizeText(key))));
    return match ? match.text : "اختر وجهة أو نوع تجربة، وسأقترح لك مسارًا أوليًا بين التراث والساحل والصحراء والثقافة.";
  };

  const createMessage = (text, type) => {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    return message;
  };

  const wireChat = () => {
    const chatForm = document.querySelector("#chat-form");
    const chatInput = document.querySelector("#chat-input");
    const chatMessages = document.querySelector("#chat-messages");
    if (!chatForm || !chatInput || !chatMessages) return;

    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = chatInput.value.trim();
      if (!value) return;

      chatMessages.appendChild(createMessage(value, "user"));
      chatInput.value = "";
      chatMessages.scrollTop = chatMessages.scrollHeight;

      window.setTimeout(() => {
        chatMessages.appendChild(createMessage(getReply(value), "bot"));
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }, 260);
    });
  };

  const wireGalleryDrag = () => {
    const galleryTrack = document.querySelector("#gallery-track");
    if (!galleryTrack) return;

    let isDragging = false;
    let startX = 0;
    let scrollLeft = 0;

    const endDrag = () => {
      isDragging = false;
      galleryTrack.classList.remove("is-dragging");
    };

    galleryTrack.addEventListener("pointerdown", (event) => {
      isDragging = true;
      startX = event.pageX - galleryTrack.offsetLeft;
      scrollLeft = galleryTrack.scrollLeft;
      galleryTrack.classList.add("is-dragging");
      galleryTrack.setPointerCapture(event.pointerId);
    });

    galleryTrack.addEventListener("pointerup", endDrag);
    galleryTrack.addEventListener("pointercancel", endDrag);
    galleryTrack.addEventListener("pointerleave", endDrag);

    galleryTrack.addEventListener("pointermove", (event) => {
      if (!isDragging) return;
      event.preventDefault();
      const x = event.pageX - galleryTrack.offsetLeft;
      galleryTrack.scrollLeft = scrollLeft - ((x - startX) * 1.25);
    });
  };

  const init = () => {
    const header = document.querySelector("#site-header");
    const navToggle = document.querySelector(".nav-toggle");
    const navLinks = document.querySelector("#primary-menu");
    const hero = document.querySelector(".hero");

    wireMobileMenu(navToggle, navLinks);
    wireSmoothScroll();
    wireHeroSlider(hero);
    wireDestinationFilters();
    wireImageFallbacks();
    wireAccordions();
    wireReveal();
    wireChat();
    wireGalleryDrag();

    setHeaderState(header);
    window.addEventListener("scroll", () => setHeaderState(header), { passive: true });

    console.log("Visit Libya global premium design inspired by tourism portals v01 loaded");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
