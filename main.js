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

  const heroBackgroundValue = (src) => `linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.05) 55%, rgba(0,0,0,0.12) 100%), url("${src}")`;

  const setHeroBackground = (hero, src) => {
    if (!hero || !src) return;
    hero.style.backgroundImage = heroBackgroundValue(src);
    hero.style.backgroundSize = "cover";
    hero.style.backgroundPosition = "center";
    hero.style.backgroundRepeat = "no-repeat";
  };

  const wireHeroSlider = async (hero) => {
    if (!hero) return;

    const loadedImages = (await Promise.all(heroBackgrounds.map(testImage))).filter(Boolean);
    if (!loadedImages.length) return;

    let activeIndex = 0;
    setHeroBackground(hero, loadedImages[activeIndex]);
    hero.classList.add("has-panel-hero");

    if (loadedImages.length < 2) return;
    window.setInterval(() => {
      activeIndex = (activeIndex + 1) % loadedImages.length;
      setHeroBackground(hero, loadedImages[activeIndex]);
    }, 6000);
  };

  const wireDestinationFilters = () => {
    const filterScopes = document.querySelectorAll(".filter-tabs, .destination-filters");
    if (!filterScopes.length) return;

    filterScopes.forEach((scope) => {
      const buttons = scope.querySelectorAll("[data-filter]");
      const section = scope.closest("section") || document;
      const cards = section.querySelectorAll("[data-category]");
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
    { keys: ["طرابلس", "tripoli"], text: "طرابلس بداية مثالية للمدينة القديمة والأسواق والواجهة المتوسطية، ويمكن ربطها بزيارة لبدة وصبراتة." },
    { keys: ["بنغازي", "benghazi"], text: "بنغازي بوابة الشرق، وتناسب مسارًا يجمع المدينة مع الجبل الأخضر وشحات وسوسة ورأس الهلال." },
    { keys: ["لبدة", "leptis"], text: "لبدة الكبرى من أبرز مواقع التراث العالمي في ليبيا، وتضم مسرحًا وحمامات وأسواقًا ومعابد رومانية قرب الساحل الغربي." },
    { keys: ["صبراتة", "sabratha"], text: "صبراتة مدينة أثرية ساحلية تشتهر بمسرحها الروماني وموقعها المتوسطي القريب من طرابلس." },
    { keys: ["قورينا", "شحات", "cyrene"], text: "قورينا / شحات موقع كلاسيكي مهم في الجبل الأخضر، يضم معابد ومدافن صخرية ومشهدًا طبيعيًا غنيًا." },
    { keys: ["غدامس", "ghadames"], text: "غدامس القديمة واحة تراثية ذات عمارة صحراوية فريدة، وتناسب تجربة الثقافة والضيافة والمدينة القديمة." },
    { keys: ["أكاكوس", "اكاكوس", "acacus"], text: "تادرارت أكاكوس تجربة صحراوية عالمية للفنون الصخرية والتكوينات الطبيعية، والأفضل زيارتها مع دليل محلي متخصص." },
    { keys: ["الجبل الأخضر", "الجبل الاخضر", "وادي الكوف", "سوسة", "رأس الهلال", "راس الهلال", "الأثرون", "الاثرون"], text: "الجبل الأخضر يجمع الغابات والوديان والشواطئ والمواقع الأثرية، ومن أبرز محطاته شحات وسوسة ورأس الهلال ووادي الكوف." },
    { keys: ["الصحراء", "غات", "أوباري", "اوباري", "وادي الحياة", "وادي الحياه", "واو الناموس", "فزان"], text: "الصحراء الليبية تمنح تجربة واسعة بين غات وأوباري ووادي الحياة وواو الناموس، مع ضرورة التنظيم المحلي والاعتماد الرسمي عند الإطلاق." },
    { keys: ["جبل نفوسة", "جبل نفوسه", "نالوت", "غريان"], text: "جبل نفوسة يمنح تجربة تجمع العمارة الجبلية والحرف والقرى التاريخية ومسارات الثقافة المحلية." },
    { keys: ["الفلكلور", "الفروسية", "ممارسات شعبية", "اللباس", "الازياء", "الأزياء"], text: "الفلكلور الليبي يظهر في الفروسية واللباس التقليدي والممارسات الشعبية والمناسبات الاجتماعية التي تعكس تنوع المجتمع." },
    { keys: ["المطبخ الليبي", "المطبخ", "البازين", "الكسكسي", "العصيدة", "العصبان", "المبكبكة", "رشتة", "المقروض"], text: "المطبخ الليبي غني بأطباق مثل البازين والكسكسي والعصيدة والعصبان والمبكبكة ورشتة البرمة، وهو جزء أساسي من تجربة الضيافة." },
    { keys: ["الحرف", "الفخار", "الصناعات التقليدية", "الأسواق", "الاسواق"], text: "الحرف التقليدية تشمل الفخار والأدوات اليدوية والزخارف والأسواق المحلية، وتقدم للزائر جانبًا حيًا من الهوية الثقافية." },
    { keys: ["الضيافة", "كرم", "الشاي", "القهوة"], text: "الضيافة الليبية تقوم على الكرم والاحتفاء بالضيف، من تقديم الشاي والقهوة إلى مشاركة الطعام والمناسبات." },
    { keys: ["التراث", "unesco", "اليونسكو"], text: "مواقع التراث العالمي في ليبيا هي: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["الأطلس", "الاطلس", "خريطة", "خريطه"], text: "الأطلس السياحي الوطني يساعد على استكشاف المواقع التراثية والطبيعية والخدمية على خريطة تفاعلية." },
    { keys: ["برنامج 7 أيام", "برنامج 7 ايام", "سبعة أيام", "سبعه ايام"], text: "برنامج 7 أيام مبدئي يمكن أن يبدأ بطرابلس ولبدة وصبراتة، ثم شحات أو غدامس، مع يوم للتجربة الثقافية أو الصحراوية حسب التنظيم المتاح." },
    { keys: ["التأشيرات", "التاشيرات", "فيزا", "دخول"], text: "معلومات التأشيرات والدخول يجب الرجوع فيها إلى الجهات الرسمية عند الإطلاق النهائي، ولا يعتمد هذا النموذج كمرجع رسمي." },
    { keys: ["السلامة", "السلامه", "أمان", "امان"], text: "للسلامة: احتفظ بالوثائق المهمة، خطط مع مرشد محلي، انتبه للشمس والترطيب، وارجع للجهات الرسمية قبل السفر." },
    { keys: ["ميزانية", "ميزانيه", "تكلفة", "تكلفه"], text: "أي أرقام ميزانية داخل المنصة ستكون تقديرية وتجريبية فقط، وتحتاج إلى اعتماد رسمي عند الإطلاق النهائي." }
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

    console.log("Visit Libya panel hero slider v01 loaded");
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
