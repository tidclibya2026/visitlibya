// Visit Libya shared layout
// Header is tourism-only. Official institution names appear only in footer.

document.addEventListener("DOMContentLoaded", () => {
  renderHeader();
  renderFooter();
  setActiveNavLink();
});

function renderHeader() {
  const headerMount = document.getElementById("site-header");
  if (!headerMount) return;

  headerMount.innerHTML = `
    <header class="vl-header">
      <div class="vl-header__inner">
        <a class="vl-brand" href="index.html" aria-label="Visit Libya homepage">
          <img src="visitlibyalogo.png" alt="Visit Libya" class="vl-brand__logo">
          <span class="vl-brand__text">Visit Libya</span>
        </a>

        <button class="vl-menu-toggle" type="button" aria-label="Open navigation">
          ☰
        </button>

        <nav class="vl-nav" aria-label="Main navigation">
          <a href="index.html">الرئيسية</a>
          <a href="destinations.html">الوجهات</a>
          <a href="experiences.html">التجارب</a>
          <a href="culture.html">الثقافة</a>
          <a href="heritage.html">الموروث</a>
          <a href="atlas.html">الأطلس والخريطة</a>
          <a href="plan.html">خطط رحلتك</a>
          <a href="ai.html">المرشد الذكي</a>
        </nav>

        <div class="vl-header__actions">
          <button class="vl-lang" type="button">AR / EN</button>
          <a class="vl-cta" href="destinations.html">اكتشف ليبيا</a>
        </div>
      </div>
    </header>
  `;

  const toggle = headerMount.querySelector(".vl-menu-toggle");
  const nav = headerMount.querySelector(".vl-nav");

  toggle.addEventListener("click", () => {
    nav.classList.toggle("is-open");
  });
}

function renderFooter() {
  const footerMount = document.getElementById("site-footer");
  if (!footerMount) return;

  footerMount.innerHTML = `
    <footer class="vl-footer">
      <div class="vl-footer__gold-line"></div>

      <div class="vl-footer__inner">
        <div class="vl-footer__brand">
          <h2>Visit Libya</h2>
          <p>المنصة الوطنية الرسمية للترويج السياحي في ليبيا</p>
          <p class="vl-footer__official">
            وزارة السياحة والصناعات التقليدية<br>
            مركز المعلومات والتوثيق السياحي
          </p>
        </div>

        <div class="vl-footer__links">
          <a href="index.html">الرئيسية</a>
          <a href="destinations.html">الوجهات</a>
          <a href="culture.html">الثقافة</a>
          <a href="heritage.html">الموروث</a>
          <a href="atlas.html">الأطلس</a>
          <a href="plan.html">خطط رحلتك</a>
        </div>

        <div class="vl-footer__note">
          <p>
            ليبيا… أرض الحضارات وموطن السحر والجمال.
          </p>
          <p>
            من عبق التاريخ إلى مستقبل واعد.
          </p>
        </div>
      </div>
    </footer>
  `;
}

function setActiveNavLink() {
  const current = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".vl-nav a").forEach((link) => {
    const href = link.getAttribute("href");
    if (href === current) {
      link.classList.add("is-active");
    }
  });
}