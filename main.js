/* =========================================================
   Visit Libya Frontend
   Version: hero-image-only-05
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const header = document.getElementById("site-header");
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.getElementById("primary-menu");

  /* Header scroll */
  window.addEventListener("scroll", () => {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 40);
  });

  /* Mobile nav */
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      const isOpen = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* Smooth scroll */
  document.querySelectorAll('a[href^="#"], button[data-scroll-target]').forEach((el) => {
    el.addEventListener("click", (event) => {
      const href = el.getAttribute("href") || el.getAttribute("data-scroll-target");
      if (!href || href === "#") return;

      const target = document.querySelector(href);
      if (!target) return;

      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  /* Image fallback */
  document.querySelectorAll("img[data-fallback-src]").forEach((img) => {
    img.addEventListener("error", () => {
      const fallback = img.getAttribute("data-fallback-src");
      if (fallback && img.src.indexOf(fallback) === -1) {
        img.src = fallback;
      }
    });
  });

  /* Reveal on scroll */
  const reveals = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("active");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14 }
    );

    reveals.forEach((item) => revealObserver.observe(item));
  } else {
    reveals.forEach((item) => item.classList.add("active"));
  }

  /* Hero image-only slider */
  const heroSection = document.querySelector(".hero");

  const heroBackgrounds = [
    "imges/Leptis Magna3.jpeg",
    "imges/Leptis Magna3.jpg",
    "imges/Acacus.jpg",
    "imges/Ghadames2.JPG",
    "imges/Ghadames2.jpg",
    "imges/beaches.jpg",
    "imges/Cyrene.jpg",
    "imges/Sabratha.jpg"
  ];

  let validHeroImages = [];
  let heroIndex = 0;

  function preloadHeroImages(paths) {
    return Promise.all(
      paths.map((src) => {
        return new Promise((resolve) => {
          const img = new Image();
          img.onload = () => resolve(src);
          img.onerror = () => resolve(null);
          img.src = src;
        });
      })
    ).then((results) => results.filter(Boolean));
  }

  function setHeroBackground(src) {
    if (!heroSection || !src) return;

    heroSection.classList.add("hero-fading");

    heroSection.style.backgroundImage =
      `linear-gradient(
        180deg,
        rgba(0,0,0,0.02) 0%,
        rgba(0,0,0,0.04) 52%,
        rgba(0,0,0,0.10) 100%
      ), url("${src}")`;

    setTimeout(() => {
      heroSection.classList.remove("hero-fading");
    }, 650);
  }

  if (heroSection) {
    preloadHeroImages(heroBackgrounds).then((images) => {
      validHeroImages = images.length ? images : ["imges/Acacus.jpg"];
      setHeroBackground(validHeroImages[0]);

      setInterval(() => {
        heroIndex = (heroIndex + 1) % validHeroImages.length;
        setHeroBackground(validHeroImages[heroIndex]);
      }, 5000);
    });
  }

  /* Accordion */
  const accordionButtons = document.querySelectorAll(".accordion");

  accordionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const content = button.nextElementSibling;
      const isOpen = button.classList.contains("is-open");

      accordionButtons.forEach((btn) => {
        btn.classList.remove("is-open");
        btn.setAttribute("aria-expanded", "false");

        const panel = btn.nextElementSibling;
        if (panel && panel.classList.contains("accordion-content")) {
          panel.classList.remove("open");
        }
      });

      if (!isOpen) {
        button.classList.add("is-open");
        button.setAttribute("aria-expanded", "true");

        if (content && content.classList.contains("accordion-content")) {
          content.classList.add("open");
        }
      }
    });
  });

  /* VisitLibyaAI chat demo */
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const aiPromptButtons = document.querySelectorAll("[data-ai-prompt]");

  function appendMessage(text, type = "bot") {
    if (!chatMessages) return;

    const message = document.createElement("div");
    message.className = `message ${type}`;
    message.textContent = text;

    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function aiReply(input) {
    const text = input.trim().toLowerCase();

    if (!text) return "اكتب اسم وجهة أو نوع تجربة، وسأقترح لك مسارًا أوليًا.";

    if (text.includes("7") || text.includes("سبعة") || text.includes("برنامج")) {
      return "برنامج 7 أيام مقترح: اليوم الأول طرابلس والمدينة القديمة، الثاني لبدة الكبرى، الثالث صبراتة، الرابع غدامس، الخامس شحات والجبل الأخضر، السادس أكاكوس أو أوجلة، والسابع الأسواق والمطبخ الليبي.";
    }

    if (text.includes("طرابلس")) {
      return "طرابلس مناسبة كبداية للرحلة: المدينة القديمة، قوس ماركوس أوريليوس، الأسواق التقليدية، ثم يمكن ربطها بزيارة لبدة وصبراتة.";
    }

    if (text.includes("لبدة") || text.includes("leptis")) {
      return "لبدة الكبرى من أهم مواقع التراث في ليبيا، وتناسب مسار السياحة الثقافية والأثرية، خصوصًا مع طرابلس وصبراتة.";
    }

    if (text.includes("صبراتة")) {
      return "صبراتة تجمع بين الساحل والآثار، ويمكن زيارتها ضمن مسار قصير من طرابلس إلى الغرب الليبي.";
    }

    if (text.includes("شحات") || text.includes("قورينا") || text.includes("cyrene")) {
      return "شحات / قورينا وجهة مثالية في الجبل الأخضر لمحبي التاريخ والطبيعة والآثار الكلاسيكية.";
    }

    if (text.includes("غدامس")) {
      return "غدامس واحة معمارية فريدة، مناسبة لمسار الصحراء والواحات، وتحتاج تخطيطًا مع مرشد أو منظم رحلات.";
    }

    if (text.includes("أكاكوس") || text.includes("اكاكوس")) {
      return "أكاكوس من أهم مناطق الفن الصخري والصحراء في ليبيا، وتناسب رحلات المغامرة والثقافة العميقة.";
    }

    if (text.includes("المطبخ") || text.includes("الأكل") || text.includes("الطعام") || text.includes("الثقافة")) {
      return "الثقافة والمطبخ الليبي جزء مهم من التجربة: الكسكسي، البازين، الشاي الليبي، التمور، الحرف التقليدية، والضيافة الأصيلة.";
    }

    if (text.includes("تراث") || text.includes("يونسكو")) {
      return "مواقع التراث العالمي في ليبيا: لبدة الكبرى، صبراتة، شحات / قورينا، غدامس القديمة، وتادرارت أكاكوس.";
    }

    if (text.includes("أطلس") || text.includes("خريطة") || text.includes("خرائط")) {
      return "يمكنك استخدام الأطلس السياحي الوطني لاستكشاف المواقع على الخريطة وربط الوجهات الطبيعية والتراثية والخدمية.";
    }

    if (text.includes("تأشيرة") || text.includes("دخول") || text.includes("السفر")) {
      return "معلومات التأشيرات والدخول يجب اعتمادها من الجهات الرسمية عند الإطلاق النهائي. يمكنني مساعدتك الآن في بناء مسار رحلة أولي.";
    }

    return "ليبيا تقدم مسارات متعددة: التراث العالمي، الساحل، الصحراء، الواحات، الثقافة والمطبخ. اكتب اسم وجهة مثل طرابلس أو غدامس أو أكاكوس.";
  }

  if (chatForm && chatInput) {
    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const userText = chatInput.value.trim();
      if (!userText) return;

      appendMessage(userText, "user");
      chatInput.value = "";

      setTimeout(() => {
        appendMessage(aiReply(userText), "bot");
      }, 350);
    });
  }

  aiPromptButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const prompt = button.getAttribute("data-ai-prompt");
      if (!prompt) return;

      appendMessage(prompt, "user");

      setTimeout(() => {
        appendMessage(aiReply(prompt), "bot");
      }, 350);
    });
  });

  /* Gallery drag scroll */
  const galleryTrack = document.getElementById("gallery-track");

  if (galleryTrack) {
    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;

    galleryTrack.addEventListener("mousedown", (event) => {
      isDown = true;
      galleryTrack.classList.add("dragging");
      startX = event.pageX - galleryTrack.offsetLeft;
      scrollLeft = galleryTrack.scrollLeft;
    });

    galleryTrack.addEventListener("mouseleave", () => {
      isDown = false;
      galleryTrack.classList.remove("dragging");
    });

    galleryTrack.addEventListener("mouseup", () => {
      isDown = false;
      galleryTrack.classList.remove("dragging");
    });

    galleryTrack.addEventListener("mousemove", (event) => {
      if (!isDown) return;
      event.preventDefault();
      const x = event.pageX - galleryTrack.offsetLeft;
      const walk = (x - startX) * 1.4;
      galleryTrack.scrollLeft = scrollLeft - walk;
    });
  }

  console.log("Visit Libya hero image only v05 loaded");
});
