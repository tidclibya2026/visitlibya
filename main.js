// Data for destinations
const DESTS = [
  {name:'طرابلس', img:'imges/tripoliMarcus Arch.jpg', type:'ساحلية', desc:'عاصمة نابضة بالحياة وميناء تاريخي.'},
  {name:'بنغازي', img:'imges/oldtripoli.jpg', type:'ثقافية', desc:'مزيج من التاريخ والحداثة.'},
  {name:'مصراتة', img:'imges/tripolinow2.jpg', type:'ساحلية', desc:'شواطئ ومجتمع تجاري قوي.'},
  {name:'غدامس', img:'imges/Ghadames2.jpg', type:'أثرية', desc:'واحة تاريخية ومناظر تراثية.'},
  {name:'لبدة الكبرى', img:'imges/Leptis Magna.jpg', type:'أثرية', desc:'موقع روماني قديم ذو أهمية عالمية.'},
  {name:'صبراتة', img:'imges/Sabratha.jpg', type:'أثرية', desc:'مدرج روماني ساحر وميناء قديم.'},
  {name:'شحات / قورينا', img:'imges/Cyrene.jpg', type:'أثرية', desc:'مواقع أثرية وتلة تاريخية.'},
  {name:'أكاكوس', img:'imges/Acacus.jpg', type:'صحراوية', desc:'تكوينات صخرية ورسومات صخرية.'},
  {name:'غات', img:'imges/landscapes.jpg', type:'صحراوية', desc:'واحات ومناظر رملية.'},
  {name:'أوباري', img:'imges/Awjila.jpg', type:'صحراوية', desc:'بوابة إلى صحراء الوسط.'}
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
    'طرابلس':'طرابلس: العاصمة التاريخية مع شواطئ ومواقع أثرية وأسواق تقليدية.',
    'تراث':'مواقع التراث العالمي في ليبيا تشمل لبدة وصبراتة وأكاكوس.',
    'صحراء':'الصحراء الكبرى تمنحك رحلات رملية، تزلج على الكثبان، وتعرف على الواحات.',
    'طعام':'المطبخ الليبي غني: كسكسي، بشش، خبز تقليدي، وأطباق بحرية.',
    'فنادق':'تتوفر خيارات من الضيافة المحلية إلى فنادق في المدن الكبرى. تحقق من تقييمات المنصات.',
    'رحلات':'تنظيم الرحلات يتم عبر منظمي رحلات محليين مع تراخيص وتجربة صحراوية.'
  };

  function appendMessage(text,who='bot'){
    const el = document.createElement('div'); el.className = 'msg '+(who==='user'?'user':'bot'); el.textContent = text; chatLog.appendChild(el); chatLog.scrollTop = chatLog.scrollHeight;
  }

  chatForm.addEventListener('submit',e=>{
    e.preventDefault(); const txt = chatInput.value.trim(); if(!txt) return; appendMessage(txt,'user'); chatInput.value='';
    // simple keyword reply
    const ltxt = txt.toLowerCase();
    let found = false;
    Object.keys(RESPONSES).forEach(k=>{ if(ltxt.includes(k)){ found=true; setTimeout(()=>appendMessage(RESPONSES[k],'bot'),700); } });
    if(!found) setTimeout(()=>appendMessage('مرحبًا! يمكنك السؤال عن: طرابلس، التراث العالمي، الصحراء، الطعام، الفنادق، الرحلات.', 'bot'),600);
  });

});
