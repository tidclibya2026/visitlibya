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

  const normalizeArabic = (value) => (value || '')
    .toLowerCase()
    .replace(/[إأآا]/g, 'ا')
    .replace(/[ة]/g, 'ه')
    .replace(/[ى]/g, 'ي')
    .replace(/[^\u0600-\u06FFa-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const baseAiReplies = [
    { keys: ['طرابلس', 'tripoli'], text: 'طرابلس تجمع المدينة القديمة، قوس ماركوس، السرايا الحمراء، الأسواق، والذاكرة المتوسطية.', link: 'destinations.html#tripoli', label: 'افتح طرابلس' },
    { keys: ['بنغازي', 'بنغازي', 'benghazi'], text: 'بنغازي بوابة الشرق الليبي، تجمع البحر والأسواق والبحيرات والانطلاق نحو الجبل الأخضر.', link: 'destinations.html#benghazi', label: 'افتح بنغازي' },
    { keys: ['غدامس', 'ghadames'], text: 'غدامس جوهرة الصحراء ومدينة الطين الأبيض والشوارع المسقوفة وعمارة الواحة.', link: 'destinations.html#ghadames', label: 'افتح غدامس' },
    { keys: ['اكاكوس', 'أكاكوس', 'akakus', 'acacus'], text: 'أكاكوس وجهة صحراوية عالمية للفن الصخري والأقواس والوديان والتخييم المنظم.', link: 'destinations.html#acacus', label: 'افتح أكاكوس' },
    { keys: ['صبراته', 'صبراتة', 'sabratha'], text: 'صبراتة مدينة أثرية ساحلية تشتهر بالمسرح الروماني والمشهد المتوسطي.', link: 'destinations.html#sabratha', label: 'افتح صبراتة' },
    { keys: ['الجبل الاخضر', 'الجبل الأخضر', 'green mountain', 'jebel akhdar'], text: 'الجبل الأخضر يجمع الغابات والوديان والشواطئ وشحات وسوسة ورأس الهلال.', link: 'destinations.html#green-mountain', label: 'افتح الجبل الأخضر' },
    { keys: ['الصحراء', 'sahara', 'desert', 'ubari', 'ubari lakes'], text: 'الصحراء الليبية تقدم الكثبان والبحيرات والنجوم والسفاري والتخييم ومسارات القوافل.', link: 'experiences.html#desert', label: 'افتح تجارب الصحراء' },
    { keys: ['جبل نفوسه', 'جبل نفوسة', 'nafusa'], text: 'جبل نفوسة كنز للقصور الجبلية وبيوت الحفر والفخار وزيت الزيتون والحرف التقليدية.', link: 'destinations.html#nafusa', label: 'افتح جبل نفوسة' },
    { keys: ['اكل', 'الاكل', 'الأكلات', 'المطبخ', 'بازين', 'كسكسي', 'food', 'cuisine', 'libyan food', 'libyan cuisine'], text: 'من أشهر الأكلات الليبية: البازين، الكسكسي، الرشتة، العصبان، الحرايمي، والشربة الليبية.', link: 'culture.html#cuisine', label: 'افتح المطبخ الليبي' },
    { keys: ['living culture', 'traditional crafts'], text: 'تجمع الثقافة الليبية الحية الضيافة والأسواق القديمة والموسيقى والحرف التقليدية والقصص المتوارثة.', link: 'culture.html', label: 'افتح الثقافة الليبية' },
    { keys: ['تراث', 'التراث', 'unesco', 'heritage', 'world heritage', 'unesco sites', 'leptis magna', 'cyrene'], text: 'تضم ليبيا خمسة مواقع تراث عالمي: لبدة الكبرى، صبراتة، شحات، غدامس القديمة، وأكاكوس.', link: 'heritage.html#world-heritage', label: 'افتح التراث' },
    { keys: ['اطلس', 'الأطلس', 'الاطلس', 'خريطه', 'خريطة', 'atlas', 'map', 'tourism map', 'libya tourism atlas'], text: 'الأطلس السياحي الوطني يساعدك على استكشاف الوجهات والمواقع والطبقات السياحية على الخريطة.', link: 'atlas.html', label: 'افتح الأطلس' },
    { keys: ['عمله', 'عملة', 'الدينار', 'currency', 'dinar', 'money', 'exchange'], text: 'العملة الوطنية هي الدينار الليبي. أسعار الصرف متغيرة ويجب التحقق منها من المصادر الرسمية قبل السفر.', link: 'plan.html#currency', label: 'افتح التخطيط' },
    { keys: ['اوجله', 'أوجلة', 'awjila'], text: 'أوجلة واحة شرقية بطابع تراثي محلي، ضمن مسارات الواحات والصحراء.', link: 'destinations.html#awjila', label: 'افتح أوجلة' },
    { keys: ['خطط', 'رحله', 'رحلة', 'مسار', 'trip', 'trip planning', 'plan', 'itinerary', 'route', 'discover libya'], text: 'لرحلة أولى يمكنك البدء بطرابلس ولبدة وصبراتة، أو اختيار مسار الجبل الأخضر أو الصحراء حسب الموسم.', link: 'plan.html', label: 'افتح خطط رحلتك' }
  ];

  const englishAiReplies = [
    { text: 'Tripoli brings together the old city, Marcus Aurelius Arch, the Red Castle, traditional markets, and Mediterranean memory.', link: 'destinations.html#tripoli', label: 'Explore Tripoli' },
    { text: 'Benghazi is the gateway to eastern Libya, bringing together the sea, markets, lakes, and routes toward the Green Mountain.', link: 'destinations.html#benghazi', label: 'Explore Benghazi' },
    { text: 'Ghadames is a jewel of the Sahara, known for its white earthen architecture, covered lanes, and oasis traditions.', link: 'destinations.html#ghadames', label: 'Explore Ghadames' },
    { text: 'Acacus is a world-class desert destination for rock art, natural arches, valleys, scenic camping, and guided exploration.', link: 'destinations.html#acacus', label: 'Explore Acacus' },
    { text: 'Sabratha is a coastal archaeological city renowned for its Roman theatre and Mediterranean setting.', link: 'destinations.html#sabratha', label: 'Explore Sabratha' },
    { text: 'The Green Mountain combines forests, valleys, beaches, Shahat, Sousa, and Ras Al Hilal.', link: 'destinations.html#green-mountain', label: 'Explore the Green Mountain' },
    { text: 'The Libyan Sahara offers dunes, lakes, stargazing, safaris, camping, and historic caravan routes.', link: 'experiences.html#desert', label: 'Explore Sahara Experiences' },
    { text: 'The Nafusa Mountains are known for hilltop granaries, cave homes, pottery, olive oil, and traditional crafts.', link: 'destinations.html#nafusa', label: 'Explore the Nafusa Mountains' },
    { text: 'Popular Libyan dishes include bazin, couscous, rishta, osban, haraimi, and Libyan soup.', link: 'culture.html#cuisine', label: 'Explore Libyan Cuisine' },
    { text: 'Libya’s living culture brings together welcoming communities, historic souks, music, celebrations, and artisan traditions including pottery, weaving, leatherwork, and metalwork.', link: 'culture.html', label: 'Explore Living Culture' },
    { text: 'Libya has five UNESCO World Heritage Sites: Leptis Magna, Sabratha, Cyrene, the Old Town of Ghadames, and the Rock-Art Sites of Tadrart Acacus.', link: 'heritage.html#world-heritage', label: 'Explore Heritage' },
    { text: 'The Libya Tourism Atlas helps visitors explore destinations, heritage sites, natural attractions, and tourism layers on the map.', link: 'atlas.html', label: 'Open the Atlas' },
    { text: 'The national currency is the Libyan dinar. Exchange rates vary, so check official sources before travel and review customs declaration requirements.', link: 'plan.html#currency', label: 'Open Trip Planning' },
    { text: 'Awjila is an eastern oasis with a distinctive local heritage, located along Libya’s oasis and desert routes.', link: 'destinations.html#awjila', label: 'Explore Awjila' },
    { text: 'For a first trip, consider Tripoli, Leptis Magna, and Sabratha, or choose a Green Mountain or Sahara route according to the season.', link: 'plan.html', label: 'Plan Your Trip' }
  ];

  const aiReplies = baseAiReplies.map((reply, index) => ({
    keys: reply.keys,
    ar: { text: reply.text, link: reply.link, label: reply.label },
    en: englishAiReplies[index]
  }));

  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  const officialLinks = {
    services: 'services.html',
    evisa: 'https://evisa.gov.ly/',
    customs: 'https://customs.gov.ly/wp-content/uploads/2026/04/%D8%A5%D9%82%D8%B1%D8%A7%D8%B1-%D8%A7%D9%84%D8%A5%D9%81%D8%B5%D8%A7%D8%AD-%D8%B9%D9%86-%D8%B9%D9%85%D9%84%D8%A9-%D8%B1%D9%82%D9%85-1-%D9%84%D8%B3%D9%86%D8%A9-2016.pdf'
  };
  const includesAny = (source, keys) => keys.some(key => source.includes(normalizeArabic(key)));

  window.getVisitLibyaOfficialAnswer = (question) => {
    const normalized = normalizeArabic(question);
    const hasVisa = includesAny(normalized, ['تأشيرة', 'تاشيرة', 'visa', 'evisa']);
    const hasEntry = includesAny(normalized, ['دخول', 'جواز', 'arrival', 'entry', 'passport']);
    const hasCurrency = includesAny(normalized, ['عملة', 'الدينار', 'افصاح', 'إفصاح', 'جمارك', 'currency', 'dinar', 'customs', 'declaration']);
    const hasWork = includesAny(normalized, ['عمل', 'شغل', 'وظيفة', 'work', 'job', 'employment']);

    if (hasWork && hasVisa) {
      return isArabicPage ? {
        title: 'تنبيه رسمي',
        text: 'التأشيرة السياحية مخصصة للزيارة والسياحة فقط ولا تستخدم لغرض العمل. لأغراض العمل يجب الرجوع إلى الجهات الرسمية المختصة وإجراءات التأشيرات والتصاريح المناسبة.',
        link: officialLinks.services,
        label: 'الخدمات والدخول'
      } : {
        title: 'Official Notice',
        text: 'A tourist visa is for tourism and visits only. Work requires the appropriate visa and permits through the competent official authorities.',
        link: officialLinks.services,
        label: 'Travel Services'
      };
    }

    if (hasVisa || hasEntry) {
      return isArabicPage ? {
        title: 'التأشيرة والدخول',
        text: 'يرجى التحقق من الأهلية والرسوم ومتطلبات الدخول عبر الموقع الحكومي الرسمي للتأشيرة الإلكترونية قبل السفر. لا تعتمد المنصة مبالغ ثابتة أو شروطًا نهائية داخل الصفحة.',
        link: officialLinks.evisa,
        label: 'فتح الموقع الحكومي للتأشيرة'
      } : {
        title: 'eVisa and Entry',
        text: 'Please verify eligibility, fees, and entry requirements through the official Libya eVisa government portal before travel. This platform does not publish fixed fees or final entry rules.',
        link: officialLinks.evisa,
        label: 'Open Official eVisa Portal'
      };
    }

    if (hasCurrency) {
      return isArabicPage ? {
        title: 'العملة والإفصاح الجمركي',
        text: 'العملة الوطنية هي الدينار الليبي. عند تجاوز الحدود الرسمية، يجب الإفصاح عن العملة وفق نموذج مصلحة الجمارك وتعليماتها قبل الدخول أو الخروج.',
        link: officialLinks.customs,
        label: 'تحميل نموذج الإفصاح'
      } : {
        title: 'Currency and Customs Declaration',
        text: 'The national currency is the Libyan dinar. When exceeding official thresholds, travelers should complete the customs currency declaration form and review customs instructions before entry or departure.',
        link: officialLinks.customs,
        label: 'Download Customs Declaration'
      };
    }

    return null;
  };

  const appendMessage = (content, type) => {
    if (!chatMessages) return;
    const node = document.createElement('div');
    node.className = `message ${type}`;
    if (typeof content === 'string') {
      node.textContent = content;
    } else {
      if (content.title) {
        const title = document.createElement('strong');
        title.textContent = content.title;
        node.appendChild(title);
      }
      if (content.text) {
        const paragraph = document.createElement('p');
        paragraph.textContent = content.text;
        node.appendChild(paragraph);
      }
      if (content.link) {
        const link = document.createElement('a');
        link.href = content.link;
        link.textContent = content.label || 'افتح الرابط';
        node.appendChild(link);
      }
    }
    chatMessages.appendChild(node);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };
  const answer = (question) => {
    const clean = (question || '').trim();
    if (!clean) return;
    appendMessage(clean, 'user');
    const officialReply = window.getVisitLibyaOfficialAnswer(clean);
    if (officialReply) {
      window.setTimeout(() => appendMessage(officialReply, 'bot'), 180);
      return;
    }
    const normalized = normalizeArabic(clean);
    const reply = aiReplies.find(item => item.keys.some(key => normalized.includes(normalizeArabic(key)))) || {
      ar: {
        text: 'يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، الأطلس، العملة، أو تخطيط الرحلة.',
        link: 'destinations.html',
        label: 'ابدأ بالوجهات'
      },
      en: {
        text: 'I can help with destinations, heritage, culture, cuisine, the atlas, currency, and trip planning.',
        link: 'destinations.html',
        label: 'Explore Destinations'
      }
    };
    const localizedReply = isArabicPage ? reply.ar : reply.en;
    window.setTimeout(() => appendMessage(localizedReply, 'bot'), 180);
  };
  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', (event) => {
      event.preventDefault();
      answer(chatInput.value);
      chatInput.value = '';
    });
  }
  document.querySelectorAll('[data-ai-question], [data-question]').forEach(button => {
    button.addEventListener('click', () => answer(button.dataset.aiQuestion || button.dataset.question || button.textContent || ''));
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
console.log("Visit Libya English proofreading v1 loaded");
console.log("Visit Libya Arabic version with tourism content v1 loaded");
console.log("Visit Libya services visa currency FAQ gallery v1 loaded");
