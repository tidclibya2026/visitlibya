// Data for destinations (updated with provided image paths)
const DESTS = [
  {name:'طرابلس', img:'imges/tripoliMarcus Arch.jpg', type:'ساحلية', desc:'عاصمة نابضة بالحياة وميناء تاريخي.'},
  {name:'بنغازي', img:'imges/tripolinow2.jpg', type:'ثقافية', desc:'مركز حضري وتاريخي على الساحل الشرقي.'},
  {name:'مصراتة', img:'imges/oldtripoli.jpg', type:'ساحلية', desc:'مدينة تجارية وساحلية بحياة محلية نشطة.'},
  {name:'غدامس', img:'imges/Ghadames2.jpg', type:'أثرية', desc:'المدينة الواحة ذات الطابع المعماري الفريد.'},
  {name:'شحات / قورينا', img:'imges/Cyrene.jpg', type:'أثرية', desc:'مواقع أثرية على تلال تاريخية.'},
  {name:'لبدة الكبرى', img:'imges/Leptis Magna.jpg', type:'أثرية', desc:'موقع روماني رائع ضمن التراث العالمي.'},
  {name:'صبراتة', img:'imges/Sabratha.jpg', type:'أثرية', desc:'مسرح روماني وإطلالة بحرية تاريخية.'},
  {name:'أكاكوس', img:'imges/Acacus1.jpg', type:'صحراوية', desc:'تكوينات حجرية ونقوش شديدة الجمال.'},
  {name:'أوجلة', img:'imges/Awjila.jpg', type:'ثقافية', desc:'واحات وتقاليد بدوية.'},
  {name:'غات', img:'imges/landscapes.jpg', type:'صحراوية', desc:'بوابة نحو رحلات صحراوية ومشاهد رملية.'},
  {name:'أوباري', img:'imges/Acacus2.jpg', type:'صحراوية', desc:'منطقة صحراوية ذات معالم طبيعية.'}
];

document.addEventListener('DOMContentLoaded',()=>{
  // inject destination cards
  const grid = document.querySelector('.dest-grid');
  DESTS.forEach(d=>{
    const card = document.createElement('article');
    card.className='dest-card reveal';
    card.innerHTML = `
      <div class="thumb"><img src="${d.img}" alt="صورة ${d.name}" onerror="this.style.display='none'"/></div>
      <div class="content">
        <span class="chip">${d.type}</span>
        <h3>${d.name}</h3>
        <p>${d.desc}</p>
        <div class="actions"><button class="btn" data-dest="${d.name}">اكتشف المزيد</button></div>
      </div>`;
    grid.appendChild(card);
  });

  // mobile menu
  const menuToggle = document.getElementById('menuToggle');
  const mobileMenu = document.getElementById('mobileMenu');
  menuToggle.addEventListener('click',()=>{
    const open = mobileMenu.hidden;
    mobileMenu.hidden = !open;
    menuToggle.setAttribute('aria-expanded', String(open));
    menuToggle.classList.toggle('open', open);
  });

  // lang toggle (RTL/LTR demo)
  const langToggle = document.getElementById('langToggle');
  langToggle.addEventListener('click',()=>{
    const html = document.documentElement;
    if(html.getAttribute('dir')==='rtl'){
      html.setAttribute('dir','ltr'); html.setAttribute('lang','en'); langToggle.textContent='AR';
    } else { html.setAttribute('dir','rtl'); html.setAttribute('lang','ar'); langToggle.textContent='EN'; }
  });

  // desktop submenu toggles
  document.querySelectorAll('.sub-toggle').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const li = btn.parentElement;
      li.classList.toggle('open');
    });
  });
  // close submenus when clicking outside
  document.addEventListener('click',(e)=>{
    document.querySelectorAll('.nav-list .has-sub.open').forEach(openLi=>{
      if(!openLi.contains(e.target)) openLi.classList.remove('open');
    });
  });

  // smooth scroll
  document.querySelectorAll('[data-scroll]').forEach(a=>{
    a.addEventListener('click',e=>{
      e.preventDefault(); const href = a.getAttribute('href'); document.querySelector(href).scrollIntoView({behavior:'smooth',block:'start'});
      if(!mobileMenu.hidden) { mobileMenu.hidden=true; menuToggle.setAttribute('aria-expanded','false') }
    })
  });

  // reveal on scroll
  const observer = new IntersectionObserver((entries)=>{
    entries.forEach(ent=>{ if(ent.isIntersecting) ent.target.classList.add('revealed'); })
  },{threshold:0.08});
  document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));

  // sticky header: add .scrolled when past threshold
  const header = document.getElementById('siteHeader');
  function checkHeader(){ if(window.scrollY>40) header.classList.add('scrolled'); else header.classList.remove('scrolled'); }
  checkHeader(); window.addEventListener('scroll', checkHeader);

  // accordion
  document.querySelectorAll('.acc-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      btn.classList.toggle('active'); const panel = btn.nextElementSibling; if(panel.style.display==='block'){ panel.style.display='none' } else { panel.style.display='block' }
    })
  });

  // Dest buttons
  document.body.addEventListener('click',e=>{
    if(e.target.matches('.dest-card .btn')||e.target.matches('.dest-card button')){
      const name = e.target.dataset.dest; alert(name + ' — للمزيد قم بزيارة قسم الوجهات');
    }
  });

  // AI demo chat
  const aiFloat = document.getElementById('aiFloat');
  const openAiDemo = document.getElementById('openAiDemo');
  const chatWindow = document.getElementById('chatWindow');
  const chatLog = document.getElementById('chatLog');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');

  function toggleChat(open=true){
    if(chatWindow.style.display==='block' || open){ chatWindow.style.display='block'; chatInput.focus(); }
    else chatWindow.style.display='none';
  }
  aiFloat.addEventListener('click',()=>{ toggleChat(true); window.scrollTo({top:document.body.scrollHeight, behavior:'smooth'}); });
  openAiDemo.addEventListener('click',()=>{ toggleChat(true); chatInput.focus(); });

  const RESPONSES = {
    'طرابلس': 'اقتراح برنامج 3 أيام في طرابلس:\nاليوم 1: جولة في المدينة القديمة وأسواقها.\nاليوم 2: زيارة المتاحف والمواقع الساحلية.\nاليوم 3: رحلات يومية للمعالم المحيطة.',
    'التراث': 'مواقع التراث العالمي في ليبيا:\n- لبدة الكبرى\n- صبراتة\n- شحات / قورينا\n- غدامس القديمة\n- أكاكوس',
    'الصحراء': 'اقتراحات للصحراء: غدامس، أكاكوس، غات، أوباري — رحلات منظمة مع مرشدين محليين.',
    'الطعام': 'أطباق تقليدية: الكسكس، البازين، العصبان، والشاي الليبي مع التمر.',
    'الفنادق': 'سيتم ربط المنصة لاحقًا بمنظومة الإيواء السياحي لتوصيات الفنادق والحجوزات.'
  };
  // extend responses
  RESPONSES['نبذة عن ليبيا'] = 'ليبيا دولة في شمال أفريقيا، تمتاز بتاريخ عريق وسواحل على البحر المتوسط، وصحراء واسعة ومواقع أثرية مهمة.';
  RESPONSES['التاريخ'] = 'ليبيا احتضنت حضارات متعددة: الفينيقيون، الإغريق، الرومان، والإسلام، مما أثرى التراث المعماري والثقافي.';
  RESPONSES['العادات'] = 'الضيافة والكرم جزء من الثقافة الليبية، مع عادات تختلف بين المناطق الساحلية والصحراوية.';
  RESPONSES['المطبخ'] = 'المطبخ الليبي متنوع: كسكسي، بَازين، العصبان، أطباق بحرية، وحلويات محلية.';
  RESPONSES['التراث العالمي'] = RESPONSES['التراث'];
  RESPONSES['الوجهات'] = 'تتوفر وجهات متنوعة: طرابلس، بنغازي، مصراتة، غدامس، شحات، لبدة، صبراتة، أكاكوس، أغوالة، غات، أوباري.';
  RESPONSES['خطط رحلتك'] = 'ابدأ بتحديد مدة الإقامة، الاهتمامات، ثم اختر برنامجًا يغطي المدن الأثرية والشواطئ والصحراء.';
  RESPONSES['الفعاليات'] = 'تابع جدول الفعاليات المحلية مثل مهرجانات هون وغات ومهرجان أوجلة للاستمتاع بتجارب محلية.';
  RESPONSES['التأشيرات'] = 'تختلف متطلبات التأشيرة حسب الجنسية؛ يُنصح بالرجوع للسفارات والجهات الرسمية قبل السفر.';
  RESPONSES['التنقل'] = 'التنقل بين المدن عبر خطوط جوية محلية، حافلات، واستئجار سيارات، مع توفر رحلات منظمة للصحارى.';

  function appendMessage(text,who='bot'){
    const el = document.createElement('div'); el.className = 'msg '+(who==='user'?'user':'bot'); el.textContent = text; chatLog.appendChild(el); chatLog.scrollTop = chatLog.scrollHeight;
  }

  chatForm.addEventListener('submit',e=>{
    e.preventDefault(); const txt = chatInput.value.trim(); if(!txt) return; appendMessage(txt,'user'); chatInput.value='';
    const ltxt = txt.toLowerCase();
    let found = false;
    Object.keys(RESPONSES).forEach(k=>{ if(ltxt.includes(k)){ found=true; setTimeout(()=>appendMessage(RESPONSES[k],'bot'),700); } });
    if(!found) setTimeout(()=>appendMessage('مرحبًا! جرب كلمات مفتاحية مثل: طرابلس، التراث، الصحراء، الطعام، الفنادق.', 'bot'),600);
  });

  // gallery: drag to scroll
  const gallery = document.getElementById('galleryScroll');
  if(gallery){
    let isDown = false; let startX; let scrollLeft;
    gallery.addEventListener('mousedown',(e)=>{ isDown=true; gallery.classList.add('dragging'); startX=e.pageX - gallery.offsetLeft; scrollLeft=gallery.scrollLeft; });
    gallery.addEventListener('mouseleave',()=>{ isDown=false; gallery.classList.remove('dragging'); });
    gallery.addEventListener('mouseup',()=>{ isDown=false; gallery.classList.remove('dragging'); });
    gallery.addEventListener('mousemove',(e)=>{ if(!isDown) return; e.preventDefault(); const x=e.pageX - gallery.offsetLeft; const walk=(x-startX)*2; gallery.scrollLeft = scrollLeft - walk; });
  }

});
