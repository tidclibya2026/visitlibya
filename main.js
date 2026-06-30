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
});
console.log("Visit Libya English proofreading v1 loaded");
