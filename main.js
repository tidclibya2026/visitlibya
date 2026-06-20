// Data for destinations (updated with provided image paths)
const DESTS = [
  {name:'طرابلس', img:'imges/tripoliMarcus Arch.jpg', type:'ساحلية', desc:'عاصمة نابضة بالحياة وميناء تاريخي.'},
  {name:'طرابلس - قديمة', img:'imges/oldtripoli.jpg', type:'ثقافية', desc:'الطرابلس التاريخية وأسواقها.'},
  {name:'غدامس', img:'imges/Ghadames2.jpg', type:'أثرية', desc:'المدينة الواحة ذات الطابع المعماري الفريد.'},
  {name:'أكاكوس', img:'imges/Acacus.jpg', type:'صحراوية', desc:'تكوينات حجرية ونقوش شديدة الجمال.'},
  {name:'لبدة الكبرى', img:'imges/Leptis Magna.jpg', type:'أثرية', desc:'موقع روماني رائع ضمن التراث العالمي.'},
  {name:'صبراتة', img:'imges/Sabratha.jpg', type:'أثرية', desc:'مسرح روماني وإطلالة بحرية تاريخية.'},
  {name:'شحات / قورينا', img:'imges/Cyrene.jpg', type:'أثرية', desc:'مواقع أثرية على تلال تاريخية.'},
  {name:'أوجلة', img:'imges/Awjila.jpg', type:'ثقافية', desc:'واحات وتقاليد بدوية.'},
  {name:'الشواطئ', img:'imges/beaches.jpg', type:'بحرية', desc:'سواحل طويلة وشواطئ رملية.'},
  {name:'الصحراء', img:'imges/The Sahara Desert.jpg', type:'صحراوية', desc:'مناظر واسعة وكثبان ذهبية.'},
  {name:'البحيرات', img:'imges/natural lakes2.jpg', type:'طبيعية', desc:'بحيرات طبيعية ومناظر ساحرة.'}
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
