(function () {
  "use strict";

  const header = document.querySelector("#site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector("#primary-menu");
  const revealItems = document.querySelectorAll(".reveal");
  const accordions = document.querySelectorAll(".accordion");
  const galleryTrack = document.querySelector("#gallery-track");
  const budgetDemo = document.querySelector("[data-budget-demo]");
  const budgetDays = document.querySelector("[data-budget-days]");
  const budgetStyle = document.querySelector("[data-budget-style]");
  const budgetOutput = document.querySelector("[data-budget-output]");
  const chatForm = document.querySelector("#chat-form");
  const chatInput = document.querySelector("#chat-input");
  const chatMessages = document.querySelector("#chat-messages");
  const aiPromptButtons = document.querySelectorAll("[data-ai-prompt]");
  const floatingAI = document.querySelector(".floating-ai");
  const heroSlider = document.querySelector("[data-hero-slider]");
  const heroSlides = document.querySelectorAll("[data-hero-slide]");
  const heroDots = document.querySelectorAll("[data-hero-dot]");
  const heroPrev = document.querySelector("[data-hero-prev]");
  const heroNext = document.querySelector("[data-hero-next]");
  const heroSection = document.querySelector(".hero");
  const heroBackgrounds = [
    "imges/Acacus.jpg",
    "imges/Leptis Magna3.jpeg",
    "imges/Leptis Magna3.jpg",
    "imges/beaches.jpg",
    "imges/Ghadames2.JPG",
    "imges/Cyrene.jpg",
    "imges/Sabratha.jpg"
  ];
  let heroIndex = 0;
  let heroActiveLayer = 0;
  let heroLayers = [];

  const setHeaderState = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 18);
  };

  const closeMobileMenu = () => {
    if (!navToggle || !navLinks) return;
    navToggle.setAttribute("aria-expanded", "false");
    navLinks.classList.remove("is-open");
  };

  const openSection = (target) => {
    const section = document.querySelector(target);
    if (!section) return;
    closeMobileMenu();
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const getHeroImageValue = (source) =>
    `linear-gradient(180deg, rgba(0,0,0,0.03) 0%, rgba(0,0,0,0.08) 55%, rgba(0,0,0,0.18) 100%), url("${source}")`;

  const resolveHeroBackgrounds = () =>
    Promise.all(
      heroBackgrounds.map(
        (source) =>
          new Promise((resolve) => {
            const image = new Image();
            image.onload = () => resolve(source);
            image.onerror = () => resolve(null);
            image.src = source;
          })
      )
    ).then((sources) => sources.filter(Boolean));

  function updateHeroBackground() {
    if (!heroLayers.length || !heroBackgrounds.length) return;
    heroIndex = (heroIndex + 1) % heroBackgrounds.length;
    const nextLayer = heroActiveLayer === 0 ? 1 : 0;
    heroLayers[nextLayer].style.backgroundImage = getHeroImageValue(heroBackgrounds[heroIndex]);
    heroLayers[nextLayer].classList.add("is-active");
    heroLayers[heroActiveLayer].classList.remove("is-active");
    heroActiveLayer = nextLayer;
  }

  const wireHeroBackground = () => {
    if (!heroSection || !heroBackgrounds.length) return;

    heroLayers = [document.createElement("div"), document.createElement("div")];
    heroLayers.forEach((layer) => {
      layer.className = "hero-bg-layer";
      layer.setAttribute("aria-hidden", "true");
      heroSection.prepend(layer);
    });

    resolveHeroBackgrounds().then((sources) => {
      if (sources.length) heroBackgrounds.splice(0, heroBackgrounds.length, ...sources);
      heroIndex = 0;
      heroActiveLayer = 0;
      heroLayers[0].style.backgroundImage = getHeroImageValue(heroBackgrounds[0]);
      heroLayers[0].classList.add("is-active");
      if (heroBackgrounds.length > 1) {
        window.setInterval(updateHeroBackground, 5000);
      }
    });
  };

  const wireHeroSlider = () => {
    if (!heroSlides.length) return;

    const delay = 5000;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let activeIndex = Array.from(heroSlides).findIndex((slide) => slide.classList.contains("is-active"));
    let timerId = 0;

    if (activeIndex < 0) activeIndex = 0;

    const setActiveSlide = (index) => {
      activeIndex = (index + heroSlides.length) % heroSlides.length;

      heroSlides.forEach((slide, slideIndex) => {
        slide.classList.toggle("is-active", slideIndex === activeIndex);
      });

      heroDots.forEach((dot, dotIndex) => {
        dot.classList.toggle("is-active", dotIndex === activeIndex);
      });
    };

    const stopAutoplay = () => {
      if (!timerId) return;
      window.clearInterval(timerId);
      timerId = 0;
    };

    const startAutoplay = () => {
      stopAutoplay();
      if (heroSlides.length < 2 || reducedMotion.matches) return;
      timerId = window.setInterval(() => setActiveSlide(activeIndex + 1), delay);
    };

    const goToSlide = (index) => {
      setActiveSlide(index);
      startAutoplay();
    };

    heroDots.forEach((dot, index) => {
      dot.addEventListener("click", () => goToSlide(index));
    });

    if (heroPrev) {
      heroPrev.addEventListener("click", () => goToSlide(activeIndex - 1));
    }

    if (heroNext) {
      heroNext.addEventListener("click", () => goToSlide(activeIndex + 1));
    }

    if (heroSlider) {
      heroSlider.addEventListener("pointerenter", stopAutoplay);
      heroSlider.addEventListener("pointerleave", startAutoplay);
      heroSlider.addEventListener("focusin", stopAutoplay);
      heroSlider.addEventListener("focusout", startAutoplay);
    }

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stopAutoplay();
        return;
      }
      startAutoplay();
    });

    setActiveSlide(activeIndex);
    startAutoplay();
  };

  const wireNavigation = () => {
    if (navToggle && navLinks) {
      navToggle.addEventListener("click", () => {
        const isOpen = navToggle.getAttribute("aria-expanded") === "true";
        navToggle.setAttribute("aria-expanded", String(!isOpen));
        navLinks.classList.toggle("is-open", !isOpen);
      });
    }

    document.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", (event) => {
        const target = link.getAttribute("href");
        if (!target || target === "#") return;
        const section = document.querySelector(target);
        if (!section) return;
        event.preventDefault();
        openSection(target);
      });
    });

    document.addEventListener("click", (event) => {
      if (!navLinks || !navToggle) return;
      const clickedInsideMenu = navLinks.contains(event.target);
      const clickedToggle = navToggle.contains(event.target);
      if (!clickedInsideMenu && !clickedToggle) closeMobileMenu();
    });
  };

  const wireAccordions = () => {
    accordions.forEach((button) => {
      button.addEventListener("click", () => {
        const isOpen = button.classList.contains("is-open");
        accordions.forEach((item) => {
          item.classList.remove("is-open");
          item.setAttribute("aria-expanded", "false");
        });
        if (!isOpen) {
          button.classList.add("is-open");
          button.setAttribute("aria-expanded", "true");
        }
      });
    });
  };

  const wireReveal = () => {
    if (!revealItems.length) return;
    if (!("IntersectionObserver" in window)) {
      revealItems.forEach((item) => item.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.16, rootMargin: "0px 0px -60px 0px" }
    );

    revealItems.forEach((item) => observer.observe(item));
  };

  const wireGalleryDrag = () => {
    if (!galleryTrack) return;

    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;

    galleryTrack.addEventListener("pointerdown", (event) => {
      isDown = true;
      startX = event.pageX - galleryTrack.offsetLeft;
      scrollLeft = galleryTrack.scrollLeft;
      galleryTrack.classList.add("is-dragging");
      galleryTrack.setPointerCapture(event.pointerId);
    });

    galleryTrack.addEventListener("pointerleave", () => {
      isDown = false;
      galleryTrack.classList.remove("is-dragging");
    });

    galleryTrack.addEventListener("pointerup", () => {
      isDown = false;
      galleryTrack.classList.remove("is-dragging");
    });

    galleryTrack.addEventListener("pointermove", (event) => {
      if (!isDown) return;
      event.preventDefault();
      const x = event.pageX - galleryTrack.offsetLeft;
      const walk = (x - startX) * 1.35;
      galleryTrack.scrollLeft = scrollLeft - walk;
    });
  };

  const wireGalleryAuto = () => {
    if (!galleryTrack || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let frameId = 0;
    let paused = false;

    const tick = () => {
      if (!paused && !galleryTrack.classList.contains("is-dragging")) {
        galleryTrack.classList.add("is-auto-scrolling");
        galleryTrack.scrollLeft += 0.32;
        if (galleryTrack.scrollLeft + galleryTrack.clientWidth >= galleryTrack.scrollWidth - 2) {
          galleryTrack.scrollLeft = 0;
        }
      }
      frameId = window.requestAnimationFrame(tick);
    };

    galleryTrack.addEventListener("pointerenter", () => { paused = true; });
    galleryTrack.addEventListener("pointerleave", () => { paused = false; });
    galleryTrack.addEventListener("focusin", () => { paused = true; });
    galleryTrack.addEventListener("focusout", () => { paused = false; });

    frameId = window.requestAnimationFrame(tick);
    window.addEventListener("beforeunload", () => window.cancelAnimationFrame(frameId));
  };

  const wireBudgetDemo = () => {
    if (!budgetDemo || !budgetDays || !budgetStyle || !budgetOutput) return;

    const labels = {
      balanced: "متوازنة",
      heritage: "تراثية",
      desert: "صحراوية",
      coast: "ساحلية"
    };

    const updateBudget = () => {
      const days = Math.max(1, Math.min(21, Number(budgetDays.value) || 1));
      const styleLabel = labels[budgetStyle.value] || "متوازنة";
      const pace = days <= 3 ? "قصيرة ومركزة" : days <= 7 ? "متوسطة التفاصيل" : "واسعة وتحتاج تنسيقًا أكبر";
      budgetOutput.textContent = `مؤشر تخطيط تجريبي: رحلة ${styleLabel} ${pace}. الأرقام تقديرية وغير رسمية وتحتاج اعتمادًا عند الإطلاق النهائي.`;
    };

    budgetDays.addEventListener("input", updateBudget);
    budgetStyle.addEventListener("change", updateBudget);
    updateBudget();
  };
  const responses = [
    {
      keywords: ["طرابلس", "tripoli", "العاصمة", "المدينة القديمة"],
      answer: "طرابلس بداية ممتازة للتعرف على ليبيا: المدينة القديمة، الأسواق، المعالم المتوسطية، ثم يمكن ربطها بزيارة لبدة الكبرى أو صبراتة حسب الوقت."
    },
    {
      keywords: ["لبدة", "leptis", "لبدة الكبرى"],
      answer: "لبدة الكبرى من أهم محطات التراث في ليبيا. خصص لها يومًا مستقلًا إن أمكن، واجمعها مع طرابلس أو صبراتة في مسار تراثي قصير."
    },
    {
      keywords: ["صبراتة", "sabratha"],
      answer: "صبراتة تجمع بين المسرح القديم ومشهد البحر، وهي مناسبة لمسار تراثي ساحلي مع طرابلس ولبدة الكبرى."
    },
    {
      keywords: ["شحات", "قورينا", "cyrene", "الجبل الأخضر"],
      answer: "شحات / قورينا تمنحك تجربة كلاسيكية في الجبل الأخضر، ويمكن وضعها ضمن برنامج أطول يربط الشرق الليبي بالطبيعة والتراث."
    },
    {
      keywords: ["غدامس", "ghadames"],
      answer: "غدامس القديمة تجربة واحات وعمارة صحراوية فريدة. اجعلها محطة هادئة في برنامج يركز على الجنوب والثقافة المحلية."
    },
    {
      keywords: ["أكاكوس", "اكاكوس", "acacus"],
      answer: "تادرارت أكاكوس مناسبة لعشاق الصحراء والفنون الصخرية. يفضل التخطيط لها مع دليل محلي وتجهيزات مناسبة للمناطق المفتوحة."
    },
    {
      keywords: ["المطبخ", "الثقافة", "ثقافة", "اكل", "أكل", "مأكولات", "كسكسي", "بازين", "شاي", "culture", "cuisine"],
      answer: "الثقافة والمطبخ الليبي جزء أساسي من الرحلة: الكسكسي، البازين، الشاي الليبي، التمور، المأكولات البحرية، والحرف التقليدية. صفحة الثقافة تعرض تفاصيل أوسع."
    },
    {
      keywords: ["تراث", "التراث", "heritage", "unesco"],
      answer: "مواقع التراث العالمي في ليبيا هي: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس. لا نضيف مواقع أخرى تحت UNESCO إلا إذا كانت مدرجة رسميًا."
    },
    {
      keywords: ["التأشيرات", "تأشيرة", "فيزا", "الدخول", "visa", "entry"],
      answer: "معلومات التأشيرات والدخول يجب اعتمادها من الجهات الرسمية عند الإطلاق النهائي. صفحة خطط رحلتك تعرض إطارًا تنظيميًا فقط بدون معلومات رسمية غير مؤكدة."
    },
    {
      keywords: ["الأطلس", "اطلس", "atlas", "خريطة", "خرائط"],
      answer: "يمكنك فتح الأطلس السياحي الوطني من قسم الأطلس في الصفحة الرئيسية لاستكشاف ليبيا عبر خرائط تفاعلية وبيانات سياحية وطنية."
    },
    {
      keywords: ["برنامج 7 أيام", "سبعة أيام", "7 أيام", "seven days", "اسبوع", "أسبوع"],
      answer: "برنامج 7 أيام مقترح: طرابلس، لبدة الكبرى، صبراتة، غدامس، شحات / الجبل الأخضر، أكاكوس أو أوجلة، ثم الأسواق والمطبخ الليبي. راجع صفحة خطط رحلتك للتفاصيل."
    },
    {
      keywords: ["السلامة", "سلامة", "آمن", "أمان", "safety", "safe"],
      answer: "للسلامة العامة: احتفظ بنسخ من الوثائق، استخدم دليلًا محليًا في الصحراء والمناطق النائية، واحمل الماء وواقي الشمس، وتابع التعليمات الرسمية."
    },
    {
      keywords: ["الميزانية", "ميزانية", "تكلفة", "تكاليف", "budget", "cost"],
      answer: "حاسبة الميزانية في صفحة خطط رحلتك Demo فقط. لا تقدم أسعارًا رسمية، والأرقام أو المؤشرات تحتاج اعتمادًا عند الإطلاق النهائي."
    },
    {
      keywords: ["المهرجانات", "مهرجان", "فعاليات", "أوجلة", "جرمة", "سوكنة", "الفروسية", "festivals", "events"],
      answer: "من الفعاليات المقترحة للمحتوى السياحي: مهرجان غدامس الثقافي، أوجلة الثقافي السياحي، جرمة، مهرجانات الخريف، ملاقاة الربيع بسوكنة، والفروسية الشعبية."
    },
    {
      keywords: ["بحر", "شاطئ", "ساحل", "beach", "coast"],
      answer: "لرحلة ساحلية، اختر طرابلس وصبراتة والشواطئ القريبة، ويمكن ربطها بتجارب بحرية ومأكولات ساحلية."
    },
    {
      keywords: ["تصوير", "صور", "gallery", "photo"],
      answer: "أفضل وجهات التصوير تشمل لبدة الكبرى، صبراتة، غدامس، أكاكوس، شحات، والشواطئ الليبية في ساعات الصباح أو قبل الغروب."
    }
  ];

  const createMessage = (text, type) => {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    return message;
  };

  const getAIResponse = (text) => {
    const normalized = text.trim().toLowerCase();
    const match = responses.find((item) =>
      item.keywords.some((keyword) => normalized.includes(keyword.toLowerCase()))
    );

    if (match) return match.answer;
    return "اقتراح أولي: حدد عدد الأيام ونوع التجربة المفضلة، وسأرشح لك مسارًا بين التراث، الساحل، الصحراء، والواحات.";
  };

  const sendChatMessage = (text) => {
    if (!chatMessages || !text.trim()) return;
    chatMessages.appendChild(createMessage(text, "user"));
    chatMessages.scrollTop = chatMessages.scrollHeight;

    window.setTimeout(() => {
      chatMessages.appendChild(createMessage(getAIResponse(text), "bot"));
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 320);
  };

  const wireChat = () => {
    if (chatForm && chatInput) {
      chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const text = chatInput.value;
        sendChatMessage(text);
        chatInput.value = "";
        chatInput.focus();
      });
    }

    aiPromptButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const prompt = button.dataset.aiPrompt || "";
        sendChatMessage(prompt);
      });
    });

    if (floatingAI) {
      floatingAI.addEventListener("click", () => {
        const target = floatingAI.dataset.scrollTarget || "#ai";
        openSection(target);
        window.setTimeout(() => chatInput && chatInput.focus(), 600);
      });
    }
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
        image.setAttribute("aria-hidden", "true");
        if (image.hasAttribute("data-logo-fallback") && image.parentElement) {
          image.parentElement.classList.add("logo-missing");
        }
      });
    });
  };

  wireHeroSlider();
  wireHeroBackground();
  wireNavigation();
  wireAccordions();
  wireReveal();
  wireGalleryDrag();
  wireGalleryAuto();
  wireBudgetDemo();
  wireChat();
  wireImageFallbacks();
  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });
  console.log("Visit Libya global integration v03 loaded");
})();
