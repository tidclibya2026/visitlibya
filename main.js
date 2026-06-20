document.addEventListener("DOMContentLoaded", () => {
  const siteHeader = document.getElementById("siteHeader");
  const menuToggle = document.getElementById("menuToggle");
  const mobileNav = document.getElementById("mobileNav");
  const langToggle = document.getElementById("langToggle");
  const openAiDemo = document.getElementById("openAiDemo");
  const aiFloat = document.getElementById("aiFloat");
  const chatWindow = document.getElementById("chatWindow");
  const chatLog = document.getElementById("chatLog");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const scrollLinks = document.querySelectorAll("[data-scroll]");
  const accordionButtons = document.querySelectorAll(".accordion-button");
  const galleryScroll = document.getElementById("galleryScroll");

  function setHeaderState() {
    if (window.scrollY > 30) {
      siteHeader.classList.add("scrolled");
    } else {
      siteHeader.classList.remove("scrolled");
    }
  }

  setHeaderState();
  window.addEventListener("scroll", setHeaderState);

  if (menuToggle && mobileNav) {
    menuToggle.addEventListener("click", () => {
      const isOpen = mobileNav.hasAttribute("hidden");
      if (isOpen) {
        mobileNav.removeAttribute("hidden");
        menuToggle.setAttribute("aria-expanded", "true");
      } else {
        mobileNav.setAttribute("hidden", "true");
        menuToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  scrollLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const target = document.querySelector(link.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      if (mobileNav && !mobileNav.hasAttribute("hidden")) {
        mobileNav.setAttribute("hidden", "true");
        menuToggle.setAttribute("aria-expanded", "false");
      }
    });
  });

  if (langToggle) {
    langToggle.addEventListener("click", () => {
      const html = document.documentElement;
      if (html.getAttribute("dir") === "rtl") {
        html.setAttribute("dir", "ltr");
        html.setAttribute("lang", "en");
        langToggle.textContent = "AR";
      } else {
        html.setAttribute("dir", "rtl");
        html.setAttribute("lang", "ar");
        langToggle.textContent = "EN";
      }
    });
  }

  accordionButtons.forEach((button) => {
    const panel = button.nextElementSibling;
    button.addEventListener("click", () => {
      button.classList.toggle("active");
      if (panel.style.display === "block") {
        panel.style.display = "none";
      } else {
        panel.style.display = "block";
      }
    });
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("active");
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

  function appendMessage(text, type = "bot") {
    const message = document.createElement("div");
    message.className = `chat-message ${type}`;
    message.textContent = text;
    chatLog.appendChild(message);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  const RESPONSES = {
    "طرابلس": "طرابلس هي العاصمة البحرية الغنية بالأسواق التقليدية والمواقع التاريخية، ويمكنك تنظيم جولة في المدينة القديمة والميناء القديم.",
    "التراث": "التراث الليبي يظهر في صبراتة، لبدة الكبرى، شحات / قورينا، غدامس القديمة، وأكاكوس، حيث تتلاقى الحضارات القديمة مع الطبيعة.",
    "الصحراء": "الصحراء الكبرى في ليبيا تقدم رحلات الكثبان الرملية والواحات الصامتة، مع تجارب قيادة السيارات الرباعية وزيارات نقوش أكاكوس.",
    "الطعام": "المطبخ الليبي غني بالأطباق التقليدية مثل الكسكسي، البازين، العصبان، والتمور، إلى جانب القهوة والشاي المحلي.",
    "الفنادق": "يمكنك اختيار فنادق راقية في طرابلس أو بنغازي، أو التجربة البسيطة في واحات الأوجلة وغدامس خلال الرحلات الصحراوية.",
    "الرحلات": "ابدأ بتقسيم زيارتك بين المدن الساحلية، المواقع التراثية، والرحلات الصحراوية لتستفيد من تنوع ليبيا بالكامل.",
    "التأشيرات": "يختلف نظام التأشيرة حسب الجنسية، لذا تأكد من الاطلاع على المتطلبات الرسمية قبل السفر عبر مواقع السفارات القريبة.",
    "الفعاليات": "تابع الفعاليات المحلية مثل مهرجانات هون وغات، أوجلة، جرمة، وتساوة للاستمتاع بالثقافة والترفيه.",
    "الوجهات": "طرابلس، غدامس، لبدة الكبرى، صبراتة، شحات، أكاكوس، أوجلة، شواطئ ليبيا، البحيرات الطبيعية، والصحراء الكبرى هي أبرز الوجهات.",
    "التراث العالمي": "مواقع التراث العالمي الخمسة في ليبيا بنيت على تراث متنوع يجمع بين الروماني والإغريقي والصحراوي الأصيل.",
  };

  if (openAiDemo && chatWindow) {
    openAiDemo.addEventListener("click", () => {
      chatWindow.scrollIntoView({ behavior: "smooth", block: "center" });
      chatInput.focus();
    });
  }

  if (aiFloat && chatWindow) {
    aiFloat.addEventListener("click", () => {
      chatWindow.scrollIntoView({ behavior: "smooth", block: "center" });
      chatInput.focus();
    });
  }

  if (chatForm) {
    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = chatInput.value.trim();
      if (!value) return;
      appendMessage(value, "user");
      chatInput.value = "";
      const lower = value.toLowerCase();
      const key = Object.keys(RESPONSES).find((term) => lower.includes(term));
      setTimeout(() => {
        if (key) {
          appendMessage(RESPONSES[key], "bot");
        } else {
          appendMessage("مرحبًا! جرب كلمات مفتاحية مثل: طرابلس، التراث، الصحراء، الطعام، الفنادق، الرحلات، التأشيرات، الفعاليات.", "bot");
        }
      }, 600);
    });
  }

  if (galleryScroll) {
    let isDown = false;
    let startX;
    let scrollLeft;

    galleryScroll.addEventListener("mousedown", (e) => {
      isDown = true;
      galleryScroll.classList.add("dragging");
      startX = e.pageX - galleryScroll.offsetLeft;
      scrollLeft = galleryScroll.scrollLeft;
    });

    galleryScroll.addEventListener("mouseleave", () => {
      isDown = false;
      galleryScroll.classList.remove("dragging");
    });

    galleryScroll.addEventListener("mouseup", () => {
      isDown = false;
      galleryScroll.classList.remove("dragging");
    });

    galleryScroll.addEventListener("mousemove", (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - galleryScroll.offsetLeft;
      const walk = (x - startX) * 2;
      galleryScroll.scrollLeft = scrollLeft - walk;
    });
  }

  document.body.addEventListener("click", (event) => {
    if (event.target.matches(".dest-card .btn-card")) {
      const section = document.getElementById("destinations");
      if (section) section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});
