document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('primaryNav');
  if (toggle && nav) toggle.addEventListener('click', () => nav.classList.toggle('open'));

  const isArabicPage = document.documentElement.lang === 'ar' || window.location.pathname.includes('/ar/');
  const assetBase = isArabicPage ? '../' : '';
  const fallbackImages = [
    `${assetBase}imges/landscapes.jpg`,
    `${assetBase}imges/landscapes5.JPG`,
    `${assetBase}panel/panel1.png`
  ];
  document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', () => {
      const fallbackIndex = Number(img.dataset.fallbackIndex || 0);
      if (fallbackIndex >= fallbackImages.length) return;
      img.dataset.fallbackIndex = String(fallbackIndex + 1);
      img.src = fallbackImages[fallbackIndex];
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

  const aiReplies = [
    { keys: ['طرابلس', 'tripoli'], text: 'طرابلس تجمع المدينة القديمة، قوس ماركوس، السرايا الحمراء، الأسواق، والذاكرة المتوسطية.', link: 'destinations.html#tripoli', label: 'افتح طرابلس' },
    { keys: ['بنغازي', 'بنغازي', 'benghazi'], text: 'بنغازي بوابة الشرق الليبي، تجمع البحر والأسواق والبحيرات والانطلاق نحو الجبل الأخضر.', link: 'destinations.html#benghazi', label: 'افتح بنغازي' },
    { keys: ['غدامس', 'ghadames'], text: 'غدامس جوهرة الصحراء ومدينة الطين الأبيض والشوارع المسقوفة وعمارة الواحة.', link: 'destinations.html#ghadames', label: 'افتح غدامس' },
    { keys: ['اكاكوس', 'أكاكوس', 'akakus', 'acacus'], text: 'أكاكوس وجهة صحراوية عالمية للفن الصخري والأقواس والوديان والتخييم المنظم.', link: 'destinations.html#acacus', label: 'افتح أكاكوس' },
    { keys: ['صبراته', 'صبراتة', 'sabratha'], text: 'صبراتة مدينة أثرية ساحلية تشتهر بالمسرح الروماني والمشهد المتوسطي.', link: 'destinations.html#sabratha', label: 'افتح صبراتة' },
    { keys: ['الجبل الاخضر', 'الجبل الأخضر', 'green mountain'], text: 'الجبل الأخضر يجمع الغابات والوديان والشواطئ وشحات وسوسة ورأس الهلال.', link: 'destinations.html#green-mountain', label: 'افتح الجبل الأخضر' },
    { keys: ['الصحراء', 'sahara', 'desert'], text: 'الصحراء الليبية تقدم الكثبان والبحيرات والنجوم والسفاري والتخييم ومسارات القوافل.', link: 'experiences.html#desert', label: 'افتح تجارب الصحراء' },
    { keys: ['جبل نفوسه', 'جبل نفوسة', 'nafusa'], text: 'جبل نفوسة كنز للقصور الجبلية وبيوت الحفر والفخار وزيت الزيتون والحرف التقليدية.', link: 'destinations.html#nafusa', label: 'افتح جبل نفوسة' },
    { keys: ['اكل', 'الاكل', 'الأكلات', 'المطبخ', 'بازين', 'كسكسي'], text: 'من أشهر الأكلات الليبية: البازين، الكسكسي، الرشتة، العصبان، الحرايمي، والشربة الليبية.', link: 'culture.html#cuisine', label: 'افتح المطبخ الليبي' },
    { keys: ['تراث', 'التراث', 'unesco'], text: 'تضم ليبيا خمسة مواقع تراث عالمي: لبدة الكبرى، صبراتة، شحات، غدامس القديمة، وأكاكوس.', link: 'heritage.html#world-heritage', label: 'افتح التراث' },
    { keys: ['اطلس', 'الأطلس', 'الاطلس', 'خريطه', 'خريطة'], text: 'الأطلس السياحي الوطني يساعدك على استكشاف الوجهات والمواقع والطبقات السياحية على الخريطة.', link: 'atlas.html', label: 'افتح الأطلس' },
    { keys: ['عمله', 'عملة', 'الدينار'], text: 'العملة الوطنية هي الدينار الليبي. أسعار الصرف متغيرة ويجب التحقق منها من المصادر الرسمية قبل السفر.', link: 'plan.html#currency', label: 'افتح التخطيط' },
    { keys: ['اوجله', 'أوجلة', 'awjila'], text: 'أوجلة واحة شرقية بطابع تراثي محلي، ضمن مسارات الواحات والصحراء.', link: 'destinations.html#awjila', label: 'افتح أوجلة' },
    { keys: ['خطط', 'رحله', 'رحلة', 'مسار'], text: 'لرحلة أولى يمكنك البدء بطرابلس ولبدة وصبراتة، أو اختيار مسار الجبل الأخضر أو الصحراء حسب الموسم.', link: 'plan.html', label: 'افتح خطط رحلتك' }
  ];

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
      text: isArabicPage ? 'يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، الأطلس، العملة، أو تخطيط الرحلة.' : 'I can help with destinations, heritage, culture, cuisine, the atlas, currency, and trip planning.',
      link: 'destinations.html',
      label: isArabicPage ? 'ابدأ بالوجهات' : 'Explore Destinations'
    };
    window.setTimeout(() => appendMessage(reply, 'bot'), 180);
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

    const closeLightbox = () => {
      lightbox.classList.remove('open');
      lightbox.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('lightbox-open');
    };

    galleryItems.forEach(item => {
      item.addEventListener('click', (event) => {
        event.preventDefault();
        const thumb = item.querySelector('img');
        image.src = item.getAttribute('href');
        image.alt = thumb ? thumb.alt : '';
        caption.textContent = item.querySelector('span') ? item.querySelector('span').textContent : image.alt;
        lightbox.classList.add('open');
        lightbox.setAttribute('aria-hidden', 'false');
        document.body.classList.add('lightbox-open');
      });
    });

    close.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (event) => {
      if (event.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeLightbox();
    });
  }
});
console.log("Visit Libya English proofreading v1 loaded");
console.log("Visit Libya Arabic version with tourism content v1 loaded");
console.log("Visit Libya services visa currency FAQ gallery v1 loaded");
