document.addEventListener("DOMContentLoaded", () => {
  const siteHeader = document.getElementById("siteHeader");
  const menuToggle = document.getElementById("menuToggle");
  const mobileNav = document.getElementById("mobileNav");
  const openAiDemo = document.getElementById("openAiDemo");
  const askGuide = document.getElementById("askGuide");
  const aiFloat = document.getElementById("aiFloat");
  const chatBox = document.getElementById("chatBox");
  const chatLog = document.getElementById("chatLog");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const scrollLinks = document.querySelectorAll("[data-scroll]");
  const accordionButtons = document.querySelectorAll(".accordion-button");
  const galleryScroll = document.getElementById("galleryScroll");
  const heroSection = document.getElementById("home");
  const heroBackgrounds = [
    "imges/Leptis Magna3.jpeg",
    "imges/Acacus.jpg",
    "imges/beaches.jpg",
    "imges/Ghadames2.JPG"
  ];
  let heroIndex = 0;

  function setHeaderState() {
    if (window.scrollY > 30) {
      siteHeader.classList.add("scrolled");
    } else {
      siteHeader.classList.remove("scrolled");
    }
  }

  function updateHeroBackground() {
    heroIndex = (heroIndex + 1) % heroBackgrounds.length;
    heroSection.style.backgroundImage = `linear-gradient(135deg, rgba(4, 54, 77, 0.86), rgba(7, 87, 123, 0.72)), url(${heroBackgrounds[heroIndex]})`;
  }

  setHeaderState();
  window.addEventListener("scroll", setHeaderState);
  setInterval(updateHeroBackground, 5000);

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

  if (askGuide) {
    askGuide.addEventListener("click", () => {
      const chatSection = document.getElementById("visitlibyaai");
      if (chatSection) {
        chatSection.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  }

  if (openAiDemo && chatBox) {
    openAiDemo.addEventListener("click", () => {
      chatBox.scrollIntoView({ behavior: "smooth", block: "center" });
      chatInput.focus();
    });
  }

  if (aiFloat && chatBox) {
    aiFloat.addEventListener("click", () => {
      chatBox.scrollIntoView({ behavior: "smooth", block: "center" });
      chatInput.focus();
    });
  }

  accordionButtons.forEach((button) => {
    const panel = button.nextElementSibling;
    button.addEventListener("click", () => {
      const isOpen = panel.classList.toggle("open");
      button.classList.toggle("active", isOpen);
    });
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("active");
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));

  const RESPONSES = {
    "طرابلس": "طرابلس تقدم مزيجاً فاخراً بين البحر والأسواق التاريخية والهوية العصرية. يمكنك أن تبدأ زيارتك من المدينة القديمة وسوق القورف.",
    "التراث": "التراث الليبي يظهر في لبدة الكبرى وصبراتة وغدامس وأكاكوس، حيث تمتزج الحضارات المتوسطية مع الثقافة الصحراوية.",
    "الصحراء": "الصحراء الكبرى توفر مغامرات الكثبان ورحلات الواحات ونقوش أكاكوس القديمة التي تحكي قصة الإنسان والصحراء.",
    "الطعام": "المطبخ الليبي غني بالكسكسي والبازين والعصبان والتمور، وهو تجربة ضيافة متكاملة مع كل رحلة.",
    "الفنادق": "اختَر بين فنادق راقية في طرابلس وإقامات تقليدية في الواحات والمخيمات الصحراوية لتجربة مميزة.",
    "التأشيرات": "يمكنك التحقق من متطلبات التأشيرة من القنصليات أو من منظمي الرحلات المحليين قبل السفر.",
    "الفعاليات": "يتضمن الموسم السياحي مهرجانات هون وغات وأوجلة وجرمة وأحداث فروسية وصحراوية تعكس الثقافة الليبية.",
    "برنامج 7 أيام": "اقترحنا رحلة تبدأ في طرابلس، ثم لبدة، صبراتة، غدامس، الجبل الأخضر، أكاكوس أو أوجلة، وختاماً الأسواق والمطبخ المحلي.",
    "الوجهات": "طرابلس، غدامس، لبدة الكبرى، صبراتة، شحات، أكاكوس، أوجلة، الشواطئ، البحيرات الطبيعية، والصحراء الكبرى تشكل خارطة جميلة لليبيا.",
  };

  function appendMessage(text, type = "bot") {
    const message = document.createElement("div");
    message.className = `msg ${type}`;
    message.textContent = text;
    chatLog.appendChild(message);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  const quickButtons = document.querySelectorAll(".quick-prompts button");
  quickButtons.forEach((button) => {
    button.addEventListener("click", () => {
      chatInput.value = button.dataset.suggest;
      chatForm.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    });
  });

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
          appendMessage("مرحبًا! اسأل عن طرابلس، التراث، الصحراء، الطعام، الفنادق، التأشيرات، الفعاليات، أو برنامج 7 أيام.", "bot");
        }
      }, 700);
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
      const walk = (x - startX) * 1.8;
      galleryScroll.scrollLeft = scrollLeft - walk;
    });
  }
});
