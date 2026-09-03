(function () {
  const app = document.getElementById("destination-detail-app");
  if (!app) return;
  const key = document.body.dataset.destination || "";
  const assetPrefix = document.body.dataset.assetPrefix || "";
  const record = window.VISITLIBYA_DESTINATION_DETAILS?.[key];
  const lang = document.documentElement.lang?.toLowerCase().startsWith("ar") ? "ar" : "en";
  const t = (value) => value?.[lang] || value?.en || "";
  const ui = lang === "ar" ? {
    explore:"استكشف الوجهة", atlas:"الأطلس السياحي", intro:"اكتشف", highlights:"أبرز المعالم", highlightsTitle:"لماذا تزور هذه الوجهة؟", experiences:"تجارب المكان", experiencesTitle:"ما يمكن رؤيته وفعله", gallery:"معرض الصور", galleryIntro:"اكتشف الوجهة من خلال مجموعة مختارة من الصور.", galleryMore:"عرض المزيد من الصور", galleryLess:"عرض صور أقل", practical:"قبل أن تذهب", continue:"واصل استكشاف ليبيا", details:"استكشف الوجهة", missing:"تعذر تحميل تفاصيل هذه الوجهة.", back:"العودة إلى الوجهات"
  } : {
    explore:"Explore destination", atlas:"Tourist Atlas", intro:"Discover", highlights:"Signature highlights", highlightsTitle:"Why visit", experiences:"Experience the place", experiencesTitle:"Things to see & do", gallery:"Photo gallery", galleryIntro:"Discover the destination through a curated collection of images.", galleryMore:"Show more photos", galleryLess:"Show fewer photos", practical:"Know before you go", continue:"Continue exploring Libya", details:"Explore destination", missing:"This destination could not be loaded.", back:"Back to destinations"
  };
  const el = (tag, cls, text) => { const n=document.createElement(tag); if(cls)n.className=cls; if(text)n.textContent=text; return n; };
  const image = (data, className, eager=false) => { const n=el("img",className); n.src=`${assetPrefix}${data.src}`; n.alt=t(data.alt); n.width=data.width||1600; n.height=data.height||1000; n.decoding="async"; n.loading=eager?"eager":"lazy"; if(eager)n.fetchPriority="high"; return n; };
  const link = (href, cls, text) => { const n=el("a",cls,text); n.href=href; return n; };
  const heading = (eyebrow, title) => { const wrap=el("div","destination-section-heading"); wrap.append(el("p","destination-eyebrow",eyebrow),el("h2","",title)); return wrap; };
  if (!record) { const box=el("section","destination-missing"); box.append(el("h1","",ui.missing),link("../destinations.html","destination-button",ui.back)); app.append(box); return; }
  app.replaceChildren();

  const hero=el("section","destination-hero"); hero.id="destination-top"; hero.append(image(record.hero,"destination-hero__image",true));
  const heroShade=el("div","destination-hero__shade"), heroInner=el("div","destination-hero__inner");
  const meta=el("p","destination-hero__meta",`${t(record.region)} · ${t(record.type)}`); heroInner.append(meta);
  if(record.heritageStatus) heroInner.append(el("p","destination-heritage-label",t(record.heritageStatus)));
  heroInner.append(el("h1","",t(record.name)),el("p","destination-hero__tagline",t(record.tagline)));
  const actions=el("div","destination-actions"); actions.append(link("#destination-introduction","destination-button destination-button--primary",ui.explore),link(record.atlas.href,"destination-button destination-button--ghost",ui.atlas)); heroInner.append(actions); heroShade.append(heroInner); hero.append(heroShade); app.append(hero);

  const intro=el("section","destination-intro destination-shell"); intro.id="destination-introduction";
  const introMedia=el("div","destination-intro__media"); introMedia.append(image(record.introduction.image,"destination-editorial-image"));
  const introCopy=el("div","destination-intro__copy"); introCopy.append(el("p","destination-eyebrow",ui.intro),el("h2","",t(record.introduction.title)),el("p","destination-lede",t(record.introduction.body))); intro.append(introMedia,introCopy); app.append(intro);

  const highs=el("section","destination-highlights destination-shell"); highs.append(heading(ui.highlights,ui.highlightsTitle)); const highGrid=el("div","destination-highlights__grid");
  record.highlights.forEach((h,i)=>{const card=el("article",`destination-highlight destination-highlight--${i+1}`), media=el("div","destination-highlight__media"),copy=el("div","destination-highlight__copy"); media.append(image(h.image,"")); copy.append(el("h3","",t(h.title)),el("p","",t(h.description))); card.append(media,copy); highGrid.append(card);}); highs.append(highGrid); app.append(highs);

  const story=el("section","destination-story"); story.append(image(record.visualStory.image,"destination-story__image")); const storyCopy=el("div","destination-story__copy"); storyCopy.append(el("p","destination-eyebrow",t(record.visualStory.eyebrow)),el("h2","",t(record.visualStory.title)),el("p","",t(record.visualStory.description))); story.append(storyCopy); app.append(story);

  const experiences=el("section","destination-experiences destination-shell"); experiences.append(heading(ui.experiences,ui.experiencesTitle)); const expList=el("ol","destination-experiences__list"); record.experiences.forEach((x,i)=>{const item=el("li",""),num=el("span","destination-experience__number",String(i+1).padStart(2,"0")); item.append(num,el("h3","",t(x))); expList.append(item);}); experiences.append(expList); app.append(experiences);

  const context=el("section","destination-context destination-shell"); const contextCopy=el("div","destination-context__copy"); contextCopy.append(el("p","destination-eyebrow",t(record.type)),el("h2","",t(record.context.title)),el("p","destination-lede",t(record.context.body))); const contextMedia=el("div","destination-context__media"); contextMedia.append(image(record.context.image,"destination-editorial-image")); context.append(contextCopy,contextMedia); app.append(context);

  const gallery=el("section","destination-gallery destination-shell");
  const galleryHead=heading(ui.gallery,t(record.name));
  gallery.append(galleryHead,el("p","destination-gallery__intro",ui.galleryIntro));
  const mosaic=el("div","destination-gallery__mosaic");

  record.gallery.forEach((g,i)=>{
    const figure=el("figure","destination-gallery__item");
    if(i>=8) figure.classList.add("destination-gallery__item--extra");
    figure.append(image(g,""),el("figcaption","destination-gallery__caption",t(g.alt)));
    mosaic.append(figure);
  });

  gallery.append(mosaic);

  if(record.gallery.length>8){
    const controls=el("div","destination-gallery__controls");
    const more=el("button","destination-gallery__more",ui.galleryMore);
    more.type="button";
    more.setAttribute("aria-expanded","false");

    more.addEventListener("click",()=>{
      const expanded=gallery.classList.toggle("destination-gallery--expanded");
      more.setAttribute("aria-expanded",String(expanded));
      more.textContent=expanded?ui.galleryLess:ui.galleryMore;
    });

    controls.append(more);
    gallery.append(controls);
  }

  app.append(gallery);

  const practical=el("section","destination-practical destination-shell"); practical.append(heading("Visit well",ui.practical)); const pgrid=el("dl","destination-practical__grid"); record.practical.forEach(x=>{const item=el("div","destination-practical__item"); item.append(el("dt","",t(x.label)),el("dd","",t(x.value))); pgrid.append(item);}); practical.append(pgrid); app.append(practical);

  const atlas=el("section","destination-atlas destination-shell"); const atlasCard=el("div","destination-atlas__card"); atlasCard.append(image(record.atlas.image,"destination-atlas__image")); const atlasCopy=el("div","destination-atlas__copy"); atlasCopy.append(el("p","destination-eyebrow",ui.atlas),el("h2","",t(record.atlas.title)),el("p","",t(record.atlas.description)),link(record.atlas.href,"destination-button destination-button--primary",ui.atlas)); atlasCard.append(atlasCopy); atlas.append(atlasCard); app.append(atlas);

  const cont=el("section","destination-continue destination-shell"); cont.append(heading(ui.continue,ui.continue)); const cgrid=el("div","destination-continue__grid"); record.continueExploring.forEach(slug=>{const d=window.VISITLIBYA_DESTINATION_DETAILS[slug]; if(!d)return; const card=link(`./${slug}.html`,`destination-continue__card`,""); card.append(image(d.hero,"")); const copy=el("div","destination-continue__copy"); copy.append(el("p","",t(d.type)),el("h3","",t(d.name)),el("span","",ui.details)); card.append(copy); cgrid.append(card);}); cont.append(cgrid); app.append(cont);
}());
