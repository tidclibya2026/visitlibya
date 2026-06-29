document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('primaryNav');
  if (toggle && nav) toggle.addEventListener('click', () => nav.classList.toggle('open'));

  const fallback = 'imges/landscapes.jpg';
  document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', () => {
      if (!img.src.includes(fallback)) img.src = fallback;
    });
  });

  document.querySelectorAll('[data-filter-scope]').forEach(scope => {
    const section = scope.closest('section');
    const cards = section ? section.querySelectorAll('[data-category]') : [];
    scope.querySelectorAll('[data-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;
        scope.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        cards.forEach(card => {
          const cats = (card.dataset.category || '').split(/\s+/);
          card.classList.toggle('hidden', filter !== 'all' && !cats.includes(filter));
        });
      });
    });
  });

  renderVideos();
  renderGallery();
  setupLanguageToggle();
});

function renderVideos() {
  const grid = document.querySelector('[data-video-grid]');
  if (!grid || !window.VISIT_LIBYA_CONTENT) return;
  grid.innerHTML = VISIT_LIBYA_CONTENT.videos.map(video => `
    <article class="video-card" data-video-card>
      <div class="video-frame">
        <iframe src="https://www.youtube.com/embed/${video.id}" title="${escapeHtml(video.title)}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
      </div>
      <div class="video-copy">
        <span>YouTube</span>
        <h3 data-original="${escapeHtml(video.title)}" data-ar="${escapeHtml(video.titleAr)}">${escapeHtml(video.title)}</h3>
        <p data-original="${escapeHtml(video.description)}" data-ar="${escapeHtml(video.descriptionAr)}">${escapeHtml(video.description)}</p>
        <a href="${video.url}" target="_blank" rel="noopener" data-original="Open on YouTube →" data-ar="افتح على يوتيوب ←">Open on YouTube →</a>
      </div>
    </article>
  `).join('');
}

function renderGallery() {
  const grid = document.querySelector('[data-gallery-grid]');
  if (!grid || !window.VISIT_LIBYA_CONTENT) return;
  grid.innerHTML = VISIT_LIBYA_CONTENT.gallery.map(item => `
    <article class="gallery-card">
      <img src="${item.image}" alt="${escapeHtml(item.title)}" loading="lazy">
      <div>
        <span data-original="${escapeHtml(item.category)}" data-ar="${escapeHtml(item.categoryAr)}">${escapeHtml(item.category)}</span>
        <h3 data-original="${escapeHtml(item.title)}" data-ar="${escapeHtml(item.titleAr)}">${escapeHtml(item.title)}</h3>
      </div>
    </article>
  `).join('');
}

function setupLanguageToggle() {
  const current = localStorage.getItem('visitLibyaLang') || 'en';
  applyLanguage(current);
  document.querySelectorAll('.vl-language').forEach(btn => {
    btn.addEventListener('click', event => {
      event.preventDefault();
      const next = (localStorage.getItem('visitLibyaLang') || 'en') === 'en' ? 'ar' : 'en';
      localStorage.setItem('visitLibyaLang', next);
      applyLanguage(next);
    });
  });
}

function applyLanguage(lang) {
  document.documentElement.lang = lang === 'ar' ? 'ar' : 'en';
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.body.classList.toggle('rtl-mode', lang === 'ar');
  const dict = (window.VISIT_LIBYA_I18N && VISIT_LIBYA_I18N.ar) || {};
  document.querySelectorAll('body *').forEach(node => {
    if (node.children.length) return;
    if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') return;
    if (node.tagName === 'INPUT') {
      if (!node.dataset.originalPlaceholder) node.dataset.originalPlaceholder = node.getAttribute('placeholder') || '';
      if (lang === 'ar') node.setAttribute('placeholder', dict[node.dataset.originalPlaceholder] || node.dataset.originalPlaceholder);
      else node.setAttribute('placeholder', node.dataset.originalPlaceholder);
      return;
    }
    const text = (node.dataset.original || node.textContent || '').trim().replace(/\s+/g, ' ');
    if (!text) return;
    if (!node.dataset.original) node.dataset.original = text;
    if (node.dataset.ar && lang === 'ar') node.textContent = node.dataset.ar;
    else if (lang === 'ar') node.textContent = dict[node.dataset.original] || node.dataset.original;
    else node.textContent = node.dataset.original;
  });
  document.querySelectorAll('.vl-language').forEach(btn => {
    btn.innerHTML = lang === 'ar' ? '<span>◉</span> English' : '<span>◉</span> عربي';
  });
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[char]));
}
