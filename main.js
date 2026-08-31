document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('primaryNav');
  const closeNavigation = () => {
    if (!toggle || !nav) return;
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  };

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(isOpen));
    });
    nav.addEventListener('click', (event) => {
      if (event.target.closest('a') && window.matchMedia('(max-width: 1050px)').matches) {
        closeNavigation();
      }
    });
    document.addEventListener('click', (event) => {
      if (nav.classList.contains('open') && !nav.contains(event.target) && !toggle.contains(event.target)) {
        closeNavigation();
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        closeNavigation();
        toggle.focus();
      }
    });
  }

  const isArabicPage = document.documentElement.lang === 'ar' || window.location.pathname.includes('/ar/');
  const initHeroSlideshows = () => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.querySelectorAll('[data-hero-slideshow]').forEach((hero) => {
      const images = (hero.dataset.heroImages || '')
        .split('|')
        .map((item) => item.trim())
        .filter(Boolean);

      if (!images.length) return;

      const interval = Number(hero.dataset.heroInterval || 3000);

      const slides = images.map((src, index) => {
        const slide = document.createElement('span');
        slide.className = `hero-slide${index === 0 ? ' is-active' : ''}`;
        slide.setAttribute('aria-hidden', 'true');
        slide.style.backgroundImage = `url("${src}")`;
        hero.insertBefore(slide, hero.firstChild);
        return slide;
      });

      let current = 0;

      const preload = (src) => {
        const img = new Image();
        img.src = src;
      };

      preload(images[1] || images[0]);

      if (reducedMotion || slides.length < 2) return;

      window.setInterval(() => {
        const previous = current;
        current = (current + 1) % slides.length;

        slides[previous].classList.remove('is-active');
        slides[current].classList.add('is-active');

        preload(images[(current + 1) % images.length]);
      }, Math.max(interval, 3000));
    });
  };

  initHeroSlideshows();
  document.querySelectorAll('img[data-fallback]').forEach((img) => {
    img.addEventListener('error', () => {
      if (img.dataset.fallbackApplied === 'true') {
        console.error('Broken image fallback failed:', img.currentSrc || img.src);
        return;
      }

      img.dataset.fallbackApplied = 'true';
      img.src = img.dataset.fallback;
    });
  });

  document.querySelectorAll('img:not([data-fallback])').forEach((img) => {
    img.addEventListener('error', () => {
      console.error('Broken image:', img.currentSrc || img.src);
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

  const galleryItems = document.querySelectorAll('[data-gallery]');
  if (galleryItems.length) {
    const lightbox = document.createElement('div');
    lightbox.className = 'gallery-lightbox';
    lightbox.setAttribute('role', 'dialog');
    lightbox.setAttribute('aria-modal', 'true');
    lightbox.setAttribute('aria-hidden', 'true');

    const image = document.createElement('img');
    image.alt = '';

    const caption = document.createElement('span');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'gallery-lightbox-close';
    close.setAttribute('aria-label', isArabicPage ? 'إغلاق الصورة' : 'Close image');
    close.textContent = '×';

    lightbox.appendChild(close);
    lightbox.appendChild(image);
    lightbox.appendChild(caption);
    document.body.appendChild(lightbox);

    let lightboxTrigger = null;

    const closeLightbox = () => {
      if (!lightbox.classList.contains('open')) return;
      lightbox.classList.remove('open');
      lightbox.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('lightbox-open');
      if (lightboxTrigger) lightboxTrigger.focus();
    };

    galleryItems.forEach(item => {
      item.addEventListener('click', (event) => {
        event.preventDefault();
        lightboxTrigger = item;
        const thumb = item.querySelector('img');
        image.src = item.getAttribute('href');
        image.alt = thumb ? thumb.alt : '';
        caption.textContent = item.querySelector('span') ? item.querySelector('span').textContent : image.alt;
        lightbox.classList.add('open');
        lightbox.setAttribute('aria-hidden', 'false');
        document.body.classList.add('lightbox-open');
        close.focus();
      });
    });

    close.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (event) => {
      if (event.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', (event) => {
      if (!lightbox.classList.contains('open')) return;
      if (event.key === 'Escape') {
        closeLightbox();
        return;
      }
      if (event.key === 'Tab') {
        const focusable = [...lightbox.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')]
          .filter((element) => !element.hasAttribute('disabled'));
        if (!focusable.length) {
          event.preventDefault();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
  }
});
