document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('primaryNav');
  if (toggle && nav) toggle.addEventListener('click', () => nav.classList.toggle('open'));

  const isArabicPage = document.documentElement.lang === 'ar' && window.location.pathname.includes('/ar/');
  const assetBase = isArabicPage ? '../' : '';
  const fallback = `${assetBase}imges/landscapes.jpg`;
  document.querySelectorAll('img').forEach(img => {
    img.addEventListener('error', () => {
      if (img.dataset.fallbackApplied === 'true') return;
      img.dataset.fallbackApplied = 'true';
      img.src = fallback;
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
  const appendMessage = (content, type) => {
    if (!chatMessages) return;
    const node = document.createElement('div');
    node.className = `message ${type}`;
    if (typeof content === 'string') {
      node.textContent = content;
    } else {
      const span = document.createElement('span');
      span.textContent = content.text;
      node.appendChild(span);
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
    const normalized = normalizeArabic(clean);
    const reply = aiReplies.find(item => item.keys.some(key => normalized.includes(normalizeArabic(key)))) || {
      text: 'يمكنني مساعدتك في الوجهات، التراث، الثقافة، المطبخ، الأطلس، العملة، أو تخطيط الرحلة.',
      link: isArabicPage ? 'destinations.html' : 'ar/destinations.html',
      label: 'ابدأ بالوجهات'
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
  document.querySelectorAll('[data-ai-question]').forEach(button => {
    button.addEventListener('click', () => answer(button.dataset.aiQuestion || button.textContent || ''));
  });
});
console.log("Visit Libya English proofreading v1 loaded");
console.log("Visit Libya Arabic version with tourism content v1 loaded");
