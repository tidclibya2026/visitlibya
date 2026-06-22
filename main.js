(function () {
  "use strict";

  const header = document.querySelector("#site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector("#primary-menu");
  const revealItems = document.querySelectorAll(".reveal");
  const accordions = document.querySelectorAll(".accordion");
  const galleryTrack = document.querySelector("#gallery-track");
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

  const responses = [
    {
      keywords: ["الثقافة", "ثقافة", "المطبخ", "اكل", "أكل", "مأكولات", "كسكسي", "بازين", "culture", "cuisine"],
      answer: "الثقافة والمطبخ الليبي جزء أساسي من الرحلة: الضيافة، الشاي الليبي، الكسكسي، البازين، الحرف، والملابس التقليدية. يمكنك زيارة صفحة الثقافة والمطبخ لمعرفة المزيد."
    },
    {
      keywords: ["تراث", "التراث", "heritage", "لبدة", "صبراتة", "شحات", "قورينا", "غدامس", "أكاكوس"],
      answer: "لرحلة تراثية، ابدأ من لبدة الكبرى وصبراتة، ثم أضف شحات وغدامس وأكاكوس بحسب مدة الرحلة. صفحة التراث العالمي تعرض المواقع الخمسة بصور ومسار أوضح."
    },
    {
      keywords: ["التأشيرات", "تأشيرة", "فيزا", "الدخول", "visa", "entry"],
      answer: "معلومات التأشيرات والدخول يجب اعتمادها من الجهات الرسمية عند الإطلاق النهائي. في صفحة خطط رحلتك ستجد إطارًا تنظيميًا يساعدك على ترتيب الأسئلة قبل السفر."
    },
    {
      keywords: ["السلامة", "سلامة", "آمن", "أمان", "safety", "safe"],
      answer: "للسلامة العامة: حافظ على وثائقك، احمِ نفسك من الشمس، اشرب الماء بانتظام، واستعن بدليل محلي في المواقع المفتوحة. يرجى الرجوع إلى الجهات الرسمية عند الإطلاق النهائي."
    },
    {
      keywords: ["الميزانية", "ميزانية", "تكلفة", "تكاليف", "budget", "cost"],
      answer: "حاسبة الميزانية في صفحة خطط رحلتك تجربة Demo فقط، والأرقام تقديرية وغير رسمية إلى أن ترتبط المنصة بمصادر وخدمات معتمدة."
    },
    {
      keywords: ["المهرجانات", "مهرجان", "فعاليات", "غدامس الثقافي", "أوجلة", "جرمة", "تمور", "festivals", "events"],
      answer: "من المهرجانات الثقافية: غدامس الثقافي، أوجلة الثقافي السياحي، جرمة، مهرجانات الخريف، ومهرجان التمور. صفحة الثقافة تعرضها كمدخل للتجارب الموسمية."
    },
    {
      keywords: ["صحراء", "desert", "أكاكوس", "واحات"],
      answer: "لرحلة الصحراء، اجمع بين غدامس وأكاكوس مع توقف في الواحات. الأفضل تخصيص ستة أيام على الأقل لتكون الرحلة مريحة."
    },
    {
      keywords: ["بحر", "شاطئ", "ساحل", "beach", "coast"],
      answer: "لرحلة ساحلية، اختر طرابلس وصبراتة ثم أضف الشواطئ القريبة والبحيرات الطبيعية لتوازن بين التراث والاسترخاء."
    },
    {
      keywords: ["تصوير", "صور", "gallery", "photo"],
      answer: "أفضل وجهات التصوير تشمل لبدة الكبرى، غدامس، أكاكوس، قورينا، والشواطئ الليبية في ساعات الصباح أو قبل الغروب."
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
  wireChat();
  wireImageFallbacks();
  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });
  console.log("Visit Libya Hero Slider Clean Loaded");
})();
