(function () {
  "use strict";

  // ========== HELPER FUNCTIONS ==========
  const normalize = (text) =>
    text
      .toString()
      .toLowerCase()
      .replace(/[أإآ]/g, "ا")
      .replace(/ؤ/g, "و")
      .replace(/ئ/g, "ي")
      .replace(/ة/g, "ه")
      .replace(/[\u064B-\u065F\u0640]/g, "")
      .trim();

  // ========== HERO SLIDER ==========
  const heroImages = [
    "imges/pan1.webp",
    "imges/pan6.webp",
    "imges/pan4.webp",
    "imges/pan5.webp",
    "imges/pan2.avif",
    "imges/pan3.avif",
    "imges/Leptis Magna3.jpeg",
    "imges/Acacus.jpg",
    "imges/Ghadames2.JPG",
    "imges/beaches.jpg",
    "imges/Cyrene.jpg",
    "imges/Sabratha.jpg"
  ];

  const loadHeroSlider = async () => {
    const hero = document.querySelector(".hero .hero-slider");
    if (!hero) return;

    const available = [];
    for (const src of heroImages) {
      try {
        const img = new Image();
        img.src = src;
        await new Promise((resolve) => {
          img.onload = () => {
            available.push(src);
            resolve();
          };
          img.onerror = () => resolve();
        });
      } catch (_) { /* ignore */ }
    }

    if (!available.length) return;

    available.forEach((src, i) => {
      const slide = document.createElement("div");
      slide.className = `hero-slide${i === 0 ? " is-active" : ""}`;
      slide.style.backgroundImage = `url("${src}")`;
      hero.appendChild(slide);
    });

    const slides = hero.querySelectorAll(".hero-slide");
    if (slides.length < 2) return;

    let active = 0;
    setInterval(() => {
      slides[active].classList.remove("is-active");
      active = (active + 1) % slides.length;
      slides[active].classList.add("is-active");
    }, 5000);
  };

  // ========== MOBILE MENU ==========
  const initMenu = () => {
    const toggle = document.querySelector(".nav-toggle");
    const menu = document.querySelector("#primary-menu");
    if (!toggle || !menu) return;

    toggle.addEventListener("click", () => {
      const isOpen = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen);
    });

    document.addEventListener("click", (e) => {
      if (!menu.contains(e.target) && !toggle.contains(e.target)) {
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  };

  // ========== HEADER SCROLL ==========
  const initHeaderScroll = () => {
    const header = document.querySelector("#site-header");
    if (!header) return;
    window.addEventListener("scroll", () => {
      header.classList.toggle("is-scrolled", window.scrollY > 20);
    }, { passive: true });
  };

  // ========== DESTINATION FILTERS ==========
  const initFilters = () => {
    const buttons = document.querySelectorAll(".destination-filters [data-filter]");
    const cards = document.querySelectorAll(".destination-card[data-category]");
    if (!buttons.length || !cards.length) return;

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const filter = btn.dataset.filter;
        buttons.forEach((b) => b.classList.toggle("is-active", b === btn));

        cards.forEach((card) => {
          const categories = (card.dataset.category || "").split(/\s+/);
          const show = filter === "all" || categories.includes(filter);
          card.style.display = show ? "block" : "none";
        });
      });
    });
  };

  // ========== REVEAL ON SCROLL ==========
  const initReveal = () => {
    const items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    items.forEach((el) => observer.observe(el));
  };

  // ========== GALLERY DRAG ==========
  const initGalleryDrag = () => {
    const track = document.querySelector("#gallery-track");
    if (!track) return;

    let isDragging = false,
      startX = 0,
      scrollLeft = 0;

    const onStart = (e) => {
      isDragging = true;
      startX = e.pageX - track.offsetLeft;
      scrollLeft = track.scrollLeft;
      track.classList.add("is-dragging");
      track.setPointerCapture(e.pointerId);
    };

    const onMove = (e) => {
      if (!isDragging) return;
      e.preventDefault();
      const x = e.pageX - track.offsetLeft;
      track.scrollLeft = scrollLeft - (x - startX) * 1.2;
    };

    const onEnd = () => {
      isDragging = false;
      track.classList.remove("is-dragging");
    };

    track.addEventListener("pointerdown", onStart);
    track.addEventListener("pointermove", onMove);
    track.addEventListener("pointerup", onEnd);
    track.addEventListener("pointercancel", onEnd);
    track.addEventListener("pointerleave", onEnd);
  };

  // ========== CHATBOT ==========
  const chatResponses = [
    { keys: ["طرابلس", "tripoli"], text: "طرابلس عاصمة ليبيا، تجمع بين المدينة القديمة (المدينة المنورة) والأسواق التاريخية والشواطئ الجميلة. يمكنك زيارة الجامع العتيق، قوس ماركوس أوريليوس، ومتحف السراي الحمراء." },
    { keys: ["بنغازي", "benghazi"], text: "بنغازي هي بوابة الشرق، تتميز ببحيرتها ومنتزه البوسكو وشارع دبي للتسوق. تضم معالم تاريخية مثل الجامع العتيق والقشلة." },
    { keys: ["لبدة", "leptis"], text: "لبدة الكبرى هي مدينة رومانية ضخمة، من أفضل المواقع الرومانية المحفوظة في العالم. تضم أعمدة ضخمة، مسرحاً، وحمامات رومانية." },
    { keys: ["صبراتة", "sabratha"], text: "صبراتة مدينة فينيقية ثم رومانية، تشتهر بمسرحها الأثري المطل على البحر، ومينائها القديم." },
    { keys: ["شحات", "قورينا", "cyrene"], text: "شحات (قورينا) مدينة كلاسيكية في الجبل الأخضر، تضم معبد أبولو والمقابر الملكية والمدرج الروماني." },
    { keys: ["غدامس", "ghadames"], text: "غدامس هي واحة صحراوية بعمارة فريدة من الطين، مدرجة على قائمة اليونسكو. تشتهر بأزقتها المسقوفة وبيوتها المزخرفة." },
    { keys: ["اكاكوس", "أكاكوس", "acacus"], text: "تادرارت أكاكوس موقع فني صخري يعود إلى عصور ما قبل التاريخ، يضم آلاف النقوش والرسومات. مناظر صحراوية خلابة." },
    { keys: ["جبل نفوسه", "نفوسة", "غريان", "نالوت"], text: "جبل نفوسة منطقة جبلية غنية بالتراث، تضم قرى تاريخية وحرفاً يدوية. يمكنك زيارة غريان ونالوت." },
    { keys: ["الجبل الاخضر", "الجبل الأخضر", "البيضاء", "درنة"], text: "الجبل الأخضر منطقة طبيعية ساحرة في الشرق، تضم غابات الصنوبر والمناظر الخلابة. قريب من شحات ودرنة." },
    { keys: ["اوباري", "أوباري", "وادي الحياه"], text: "أوباري ووادي الحياة يقدمان بحيرات عذبة وسط الصحراء، مناظر لا تنسى ورحلات استرخاء." },
    { keys: ["المطبخ", "اكل", "كسكسي", "بازين", "شاي"], text: "المطبخ الليبي غني بالأطباق مثل الكسكسي، الطاجين، المبروكة، والشاي الليبي بالتمر. يتميز باستخدام التوابل واللحوم والخضروات." },
    { keys: ["الثقافه", "العادات", "الضيافه", "اللباس"], text: "الثقافة الليبية تجمع بين الضيافة، الأزياء التقليدية، الحرف اليدوية، والمهرجانات الشعبية. الضيافة من أسمى القيم." },
    { keys: ["التراث", "unesco", "اليونسكو"], text: "مواقع التراث العالمي في ليبيا: لبدة الكبرى، صبراتة، شحات/قورينا، غدامس القديمة، وتادرارت أكاكوس." },
    { keys: ["برنامج 7 ايام", "7 أيام"], text: "برنامج مقترح: اليوم 1-2: طرابلس ولبدة. اليوم 3: صبراتة. اليوم 4-5: جبل نفوسة وغدامس. اليوم 6-7: بنغازي وشحات." },
    { keys: ["تاشيرات", "تأشيرات", "فيزا"], text: "معلومات التأشيرات تتغير، يُرجى الرجوع إلى السفارة الليبية في بلدك أو وزارة الخارجية الليبية للحصول على أحدث المعلومات." },
  ];

  const getChatReply = (input) => {
    const normalized = normalize(input);
    for (const item of chatResponses) {
      if (item.keys.some((key) => normalized.includes(normalize(key)))) {
        return item.text;
      }
    }
    return "شكراً لسؤالك! يمكنك السؤال عن وجهات مثل طرابلس، لبدة، غدامس، أو عن الثقافة والمطبخ. سأكون سعيداً بمساعدتك.";
  };

  const initChat = () => {
    const form = document.querySelector("#chat-form");
    const input = document.querySelector("#chat-input");
    const messages = document.querySelector("#chat-messages");
    if (!form || !input || !messages) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      // User message
      const userMsg = document.createElement("div");
      userMsg.className = "message user";
      userMsg.textContent = text;
      messages.appendChild(userMsg);

      input.value = "";
      messages.scrollTop = messages.scrollHeight;

      // Bot reply
      setTimeout(() => {
        const botMsg = document.createElement("div");
        botMsg.className = "message bot";
        botMsg.textContent = getChatReply(text);
        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
      }, 400);
    });
  };

  // ========== SMOOTH SCROLL ==========
  const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        const targetId = anchor.getAttribute("href");
        if (targetId === "#") return;
        const target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });
  };

  // ========== IMAGE FALLBACK ==========
  const initImageFallback = () => {
    document.querySelectorAll("img").forEach((img) => {
      img.addEventListener("error", () => {
        const fallback = img.dataset.fallbackSrc;
        if (fallback && img.src !== fallback) {
          img.src = fallback;
        } else {
          img.style.display = "none";
        }
      });
    });
  };

  // ========== INIT ==========
  document.addEventListener("DOMContentLoaded", () => {
    loadHeroSlider();
    initMenu();
    initHeaderScroll();
    initFilters();
    initReveal();
    initGalleryDrag();
    initChat();
    initSmoothScroll();
    initImageFallback();
    console.log("Visit Libya – Premium Tourism Platform loaded.");
  });
})();
