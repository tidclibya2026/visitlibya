(function () {
  "use strict";

  const header = document.querySelector("#site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector("#primary-menu");
  const hero = document.querySelector(".hero");
  const accordions = document.querySelectorAll(".accordion");
  const revealItems = document.querySelectorAll(".reveal");
  const galleryTrack = document.querySelector("#gallery-track");
  const chatForm = document.querySelector("#chat-form");
  const chatInput = document.querySelector("#chat-input");
  const chatMessages = document.querySelector("#chat-messages");

  const heroImages = [
    "imges/Leptis Magna3.jpeg",
    "imges/Leptis Magna3.jpg",
    "imges/Acacus.jpg",
    "imges/Ghadames2.JPG",
    "imges/Ghadames2.jpg",
    "imges/beaches.jpg",
    "imges/Cyrene.jpg",
    "imges/Sabratha.jpg"
  ];

  let activeHeroIndex = 0;
  let availableHeroImages = [];

  const setHeaderState = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 20);
  };

  const closeMenu = () => {
    if (!navToggle || !navLinks) return;
    navLinks.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  };

  const wireMobileMenu = () => {
    if (!navToggle || !navLinks) return;
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-controls", "primary-menu");

    navToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (event) => {
      if (navLinks.contains(event.target) || navToggle.contains(event.target)) return;
      closeMenu();
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
        closeMenu();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  };

  const testImage = (src) => new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve(src);
    image.onerror = () => resolve(null);
    image.src = src;
  });

  const heroBackgroundValue = (src) =>
    `linear-gradient(180deg, rgba(0,0,0,0.02), rgba(0,0,0,0.08)), url("${src}")`;

  const setHeroBackground = (src) => {
    if (!hero || !src) return;
    hero.style.backgroundImage = heroBackgroundValue(src);
    hero.style.backgroundSize = "cover";
    hero.style.backgroundPosition = "center";
  };

  const wireHeroSlider = async () => {
    if (!hero) return;
    const results = await Promise.all(heroImages.map(testImage));
    availableHeroImages = results.filter(Boolean);
    if (!availableHeroImages.length) return;

    activeHeroIndex = 0;
    setHeroBackground(availableHeroImages[activeHeroIndex]);

    if (availableHeroImages.length < 2) return;
    window.setInterval(() => {
      activeHeroIndex = (activeHeroIndex + 1) % availableHeroImages.length;
      setHeroBackground(availableHeroImages[activeHeroIndex]);
    }, 5000);
  };

  const wireImageFallbacks = () => {
    document.querySelectorAll("img").forEach((image) => {
      image.addEventListener("error", () => {
        const fallback = image.dataset.fallbackSrc;
        if (fallback && !image.dataset.fallbackUsed) {
          image.dataset.fallbackUsed = "true";
          image.src = fallback;
          return;
        }
        image.classList.add("is-missing");
      });
    });
  };

  const wireAccordions = () => {
    accordions.forEach((button) => {
      button.addEventListener("click", () => {
        const wasOpen = button.classList.contains("is-open");
        accordions.forEach((item) => {
          item.classList.remove("is-open");
          item.setAttribute("aria-expanded", "false");
        });
        if (!wasOpen) {
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
    { keys: ["طرابلس", "العاصمة"], text: "طرابلس بداية مناسبة للتعرف على المدينة القديمة والأسواق والمعالم المتوسطية." },
    { keys: ["لبدة", "leptis"], text: "لبدة الكبرى محطة تراثية رئيسية ويمكن زيارتها ضمن مسار طرابلس وصبراتة." },
    { keys: ["صبراتة", "sabratha"], text: "صبراتة تجمع بين المسرح القديم والمشهد الساحلي على البحر المتوسط." },
    { keys: ["شحات", "قورينا", "cyrene"], text: "شحات / قورينا تجربة كلاسيكية في الجبل الأخضر وتناسب رحلات التراث والطبيعة." },
    { keys: ["غدامس"], text: "غدامس القديمة واحة فريدة بعمارتها الصحراوية وذاكرتها الثقافية." },
    { keys: ["أكاكوس", "اكاكوس"], text: "أكاكوس مناسبة لمحبي الصحراء والفنون الصخرية وتحتاج تخطيطًا مع دليل محلي." },
    { keys: ["مطبخ", "ثقافة", "كسكسي", "بازين"], text: "الثقافة والمطبخ الليبي يضمان الكسكسي والبازين والشاي الليبي والتمور والحرف التقليدية." },
    { keys: ["تراث", "unesco"], text: "مواقع التراث العالمي في ليبيا: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["تأشيرة", "التأشيرات", "فيزا"], text: "معلومات التأشيرات والدخول يجب الرجوع فيها إلى الجهات الرسمية عند الإطلاق النهائي." },
    { keys: ["الأطلس", "اطلس", "خريطة"], text: "يمكن فتح الأطلس السياحي الوطني من قسم الأطلس لاستكشاف الخرائط والبيانات السياحية." },
    { keys: ["7 أيام", "سبعة أيام", "برنامج"], text: "برنامج 7 أيام مقترح: طرابلس، لبدة، صبراتة، غدامس، شحات، أكاكوس أو أوجلة، ثم الأسواق والمطبخ الليبي." }
  ];

  const createMessage = (text, type) => {
    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;
    return message;
  };

  const getReply = (text) => {
    const normalized = text.trim().toLowerCase();
    const match = responses.find((item) => item.keys.some((key) => normalized.includes(key.toLowerCase())));
    return match ? match.text : "اختر نوع التجربة أو الوجهة، وسأقترح لك مسارًا أوليًا بين التراث والساحل والصحراء والثقافة.";
  };

  const wireChat = () => {
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
      }, 280);
    });
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

    galleryTrack.addEventListener("pointerup", () => {
      isDown = false;
      galleryTrack.classList.remove("is-dragging");
    });

    galleryTrack.addEventListener("pointerleave", () => {
      isDown = false;
      galleryTrack.classList.remove("is-dragging");
    });

    galleryTrack.addEventListener("pointermove", (event) => {
      if (!isDown) return;
      event.preventDefault();
      const x = event.pageX - galleryTrack.offsetLeft;
      galleryTrack.scrollLeft = scrollLeft - ((x - startX) * 1.25);
    });
  };

  wireMobileMenu();
  wireSmoothScroll();
  wireHeroSlider();
  wireImageFallbacks();
  wireAccordions();
  wireReveal();
  wireChat();
  wireGalleryDrag();
  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });

  console.log("Visit Libya final clean build v10 loaded");
})();
